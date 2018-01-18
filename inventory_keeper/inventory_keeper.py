# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import logging
import sys

import pytz
from texttable import Texttable
from web3 import Web3, HTTPProvider

from inventory_keeper.config import Config, OasisCache
from inventory_keeper.reloadable_config import ReloadableConfig
from inventory_keeper.type import BaseAccount
from pymaker.approval import directly
from pymaker.lifecycle import Lifecycle
from pymaker.numeric import Wad
from pymaker.token import ERC20Token


class InventoryKeeper:
    """Keeper acting as an inventory manager for market maker keeper or other bots."""

    logger = logging.getLogger('inventory-keeper')

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='inventory-keeper')

        parser.add_argument("--rpc-host", type=str, default="localhost",
                            help="JSON-RPC host (default: `localhost')")

        parser.add_argument("--rpc-port", type=int, default=8545,
                            help="JSON-RPC port (default: `8545')")

        parser.add_argument("--config", type=str, required=True,
                            help="Inventory configuration file")

        parser.add_argument("--gas-price", type=int, default=0,
                            help="Gas price (in Wei)")

        parser.add_argument("--gas-price-increase", type=int,
                            help="Gas price increase (in Wei) if no confirmation within"
                                 " `--gas-price-increase-every` seconds")

        parser.add_argument("--gas-price-increase-every", type=int, default=120,
                            help="Gas price increase frequency (in seconds, default: 120)")

        parser.add_argument("--gas-price-max", type=int,
                            help="Maximum gas price (in Wei)")

        parser.add_argument("--gas-price-file", type=str,
                            help="Gas price configuration file")

        parser.add_argument("--manage-inventory", dest='manage_inventory', action='store_true',
                            help="If specified, the keeper will actively manage inventory according to the config")

        parser.add_argument("--manage-inventory-frequency", type=int, default=60,
                            help="Frequency of actively managing the inventory (in seconds, default: 60)")

        parser.add_argument("--inventory-dump-file", type=str,
                            help="File the keeper will periodically write the inventory dump to")

        parser.add_argument("--inventory-dump-frequency", type=int, default=30,
                            help="Frequency of writing the inventory dump file (in seconds, default: 30)")

        parser.add_argument("--debug", dest='debug', action='store_true',
                            help="Enable debug output")

        self.arguments = parser.parse_args(args)

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.oasis_cache = OasisCache(self.web3)
        self.reloadable_config = ReloadableConfig(self.arguments.config)
        self._first_inventory_dump = True
        self._last_config_dict = None
        self._last_config = None

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                            level=(logging.DEBUG if self.arguments.debug else logging.INFO))

    def main(self):
        with Lifecycle(self.web3) as lifecycle:
            lifecycle.on_startup(self.approve)
            if self.arguments.manage_inventory:
                lifecycle.every(self.arguments.manage_inventory_frequency, self.rebalance_members)
            if self.arguments.inventory_dump_file:
                lifecycle.every(self.arguments.inventory_dump_interval, self.dump_inventory)

    def get_config(self):
        current_config = self.reloadable_config.get_config()
        if current_config != self._last_config_dict:
            self._last_config = Config(current_config)
            self._last_config_dict = current_config

        return self._last_config

    def approve(self):
        config = self.get_config()
        base = BaseAccount(web3=self.web3, address=config.base_address, min_eth_balance=config.base_min_eth_balance)

        for member in config.members:
            member_implementation = member.implementation(self.web3, self.oasis_cache)
            if not hasattr(member_implementation, 'address'):
                continue

            for member_token in member.tokens:
                token = next(filter(lambda token: token.name == member_token.token_name, config.tokens))
                if token.name == "ETH":
                    continue

                self.web3.eth.defaultAccount = member_implementation.address.address
                erc20token = ERC20Token(web3=self.web3, address=token.address)
                directly()(erc20token, base.address, config.base_name)

        self.web3.eth.defaultAccount = None

    def add_first_column(self, table, name: str):
        result = []
        for index, row in enumerate(table):
            if index == 0:
                result.append([name] + row)
            else:
                result.append([""] + row)

        return result

    def print_base_table(self, table_data: list):
        assert(isinstance(table_data, list))

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't'])
        table.set_cols_align(['l', 'r'])
        table.set_cols_width([30, 35])
        table.add_rows([["Base account", "Balance"]] + table_data)
        return table.draw()

    def print_members_table(self, table_data: list):
        assert(isinstance(table_data, list))

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't'])
        table.set_cols_align(['l', 'r', 'r', 'r'])
        table.set_cols_width([30, 35, 37, 33])
        table.add_rows([["Member accounts", "Balance", "Min", "Max"]] + table_data)
        return table.draw()

    def print_totals_table(self, table_data: list):
        assert(isinstance(table_data, list))

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t'])
        table.set_cols_align(['r'])
        table.set_cols_width([35])
        table.add_rows([["Total balance"]] + table_data)
        return table.draw()

    def print_inventory(self):
        config = self.get_config()
        base = BaseAccount(web3=self.web3, address=config.base_address, min_eth_balance=config.base_min_eth_balance)

        longest_token_name = max(map(lambda token: len(token.name), config.tokens))

        def format_amount(amount: Wad, token_name: str):
            return str(amount) + " " + token_name.ljust(longest_token_name, ".")

        base_data = map(lambda token: [format_amount(base.balance(token.name, token.address), token.name)], config.tokens)
        base_data = self.add_first_column(base_data, config.base_name)

        total_balances = {}
        for token in config.tokens:
            total_balances[token.name] = base.balance(token.name, token.address)

        members_data = []
        for member in config.members:
            table = []
            member_implementation = member.implementation(self.web3, self.oasis_cache)
            for member_token in member.tokens:
                token = next(filter(lambda token: token.name == member_token.token_name, config.tokens))
                try:
                    balance = member_implementation.balance(token.name, token.address)
                except:
                    balance = None

                table.append([
                    format_amount(balance, token.name) if balance is not None else '?',
                    format_amount(member_token.min_amount, token.name) if member_token.min_amount else "",
                    format_amount(member_token.max_amount, token.name) if member_token.max_amount else ""
                ])

                if balance is not None:
                    total_balances[token.name] = total_balances[token.name] + balance

            members_data = members_data + self.add_first_column(table, member.name)
            members_data.append(["","","",""])

        totals_data = list(map(lambda token: [format_amount(total_balances[token.name] if token.name in total_balances else Wad(0), token.name)], config.tokens))

        return self.print_base_table(base_data) + "\n\n" + \
               self.print_members_table(members_data) + "\n\n" + \
               self.print_totals_table(totals_data) + "\n\n" + \
               "Generated at: " + datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')

    def dump_inventory(self):
        # The first time we write the inventory dump to a file we log a message
        # so the user knows where to look for that file.
        if self._first_inventory_dump:
            self.logger.info(f"Will regularly write current inventory dump to '{self.arguments.inventory_dump_file}'")
            self.logger.info(f"Use 'watch cat {self.arguments.inventory_dump_file}' to monitor that file")
            self._first_inventory_dump = False

        inventory = self.print_inventory()
        with open(self.arguments.inventory_dump_file, 'w') as file:
            file.write(inventory)

        self.logger.debug(f"Written current inventory dump to '{self.arguments.inventory_dump_file}'")

    def rebalance_members(self):
        config = self.get_config()
        base = BaseAccount(web3=self.web3, address=config.base_address, min_eth_balance=config.base_min_eth_balance)

        for member in config.members:
            member_implementation = member.implementation(self.web3, self.oasis_cache)
            for member_token in member.tokens:
                token = next(filter(lambda token: token.name == member_token.token_name, config.tokens))
                try:
                    current_balance = member_implementation.balance(token.name, token.address)
                except Exception as e:
                    self.logger.warning(f"Failed to read balance of {member.name}: {e}")
                    continue

                # deposit if balance too low
                if member_token.min_amount is not None and member_token.avg_amount is not None:
                    if current_balance < member_token.min_amount:
                        self.logger.info(f"Member '{member.name}' has {token.name} balance {current_balance}"
                                         f" {token.name} below minimum ({member_token.min_amount} {token.name}).")

                        try:
                            result = member_implementation.deposit(base=base,
                                                                   token_name=token.name,
                                                                   token_address=token.address,
                                                                   amount=member_token.avg_amount-current_balance)

                            if result:
                                self.logger.info(f"Successfully deposited {token.name} to '{member.name}'")
                            else:
                                self.logger.warning(f"Failed to deposit {token.name} to '{member.name}'")
                        except Exception as e:
                            self.logger.warning(f"Failed to deposit {token.name} to '{member.name}': {e}")

                # withdraw if balance too high
                if member_token.max_amount is not None and member_token.avg_amount is not None:
                    if current_balance > member_token.max_amount:
                        self.logger.info(f"Member '{member.name}' has {token.name} balance {current_balance}"
                                         f" {token.name} above maximum ({member_token.max_amount} {token.name}).")

                        try:
                            result = member_implementation.withdraw(base=base,
                                                                   token_name=token.name,
                                                                   token_address=token.address,
                                                                   amount=current_balance-member_token.avg_amount)

                            if result:
                                self.logger.info(f"Successfully withdrawn excess {token.name} from '{member.name}'")
                            else:
                                self.logger.warning(f"Failed to withdraw excess {token.name} from '{member.name}'")
                        except Exception as e:
                            self.logger.warning(f"Failed to withdraw excess {token.name} from '{member.name}': {e}")


if __name__ == '__main__':
    InventoryKeeper(sys.argv[1:]).main()
