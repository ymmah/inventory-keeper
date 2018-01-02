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
import json
import logging
import sys

import os
import pytz
from texttable import Texttable
from web3 import Web3, HTTPProvider

from inventory_keeper.config import Config, Member
from inventory_keeper.type import EthereumAccount, OasisMarketMakerKeeper, RadarRelayMarketMakerKeeper, \
    EtherDeltaMarketMakerKeeper, BiboxMarketMakerKeeper
from pymaker import Address
from pymaker.bibox import BiboxApi
from pymaker.etherdelta import EtherDelta
from pymaker.lifecycle import Web3Lifecycle
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket


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

        parser.add_argument("--inventory-dump-file", type=str,
                            help="File the keeper will periodically write the inventory dump to")

        parser.add_argument("--inventory-dump-interval", type=int, default=30,
                            help="Frequency of writing the inventory dump file (in seconds, default: 30)")

        parser.add_argument("--debug", dest='debug', action='store_true',
                            help="Enable debug output")

        self.arguments = parser.parse_args(args)

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))

        self.config = Config(json.load(open(self.arguments.config)))

        self.first_inventory_dump = True

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                            level=(logging.DEBUG if self.arguments.debug else logging.INFO))

    def main(self):
        with Web3Lifecycle(self.web3) as lifecycle:
            if self.arguments.inventory_dump_file:
                lifecycle.every(self.arguments.inventory_dump_interval, self.dump_inventory)

    def get_type(self, member: Member):
        assert(isinstance(member, Member))

        if member.type == 'oasis-market-maker-keeper':
            oasis_address = Address(member.config['oasisAddress'])
            market_maker_address = Address(member.config['marketMakerAddress'])

            return OasisMarketMakerKeeper(web3=self.web3,
                                          otc=MatchingMarket(web3=self.web3, address=oasis_address),
                                          address=market_maker_address)
        elif member.type == 'etherdelta-market-maker-keeper':
            etherdelta_address = Address(member.config['etherDeltaAddress'])
            market_maker_address = Address(member.config['marketMakerAddress'])

            return EtherDeltaMarketMakerKeeper(web3=self.web3,
                                               etherdelta=EtherDelta(web3=self.web3, address=etherdelta_address),
                                               address=market_maker_address)
        elif member.type == 'radarrelay-market-maker-keeper':
            market_maker_address = Address(member.config['marketMakerAddress'])
            return RadarRelayMarketMakerKeeper(web3=self.web3, address=market_maker_address)
        elif member.type == 'bibox-market-maker-keeper':
            bibox_api = BiboxApi(api_server="https://api.bibox.com",
                                 api_key=self.environ(member.config['apiKey']),
                                 secret=self.environ(member.config['secret']))
            return BiboxMarketMakerKeeper(web3=self.web3, bibox_api=bibox_api)
        else:
            raise Exception(f"Unknown member type: '{member.type}'")

    def environ(self, value: str):
        if value.startswith('$'):
            return os.environ[value[1:]]
        else:
            return value

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

    def print_inventory(self):
        longest_token_name = max(map(lambda token: len(token.name), self.config.tokens))

        def format_amount(amount: Wad, token_name: str):
            return str(amount) + " " + token_name.ljust(longest_token_name, ".")

        base_type = EthereumAccount(web3=self.web3, address=self.config.base_address)
        base_data = map(lambda token: [format_amount(base_type.balance(token.name, token.address), token.name)], self.config.tokens)
        base_data = self.add_first_column(base_data, self.config.base_name)

        members_data = []
        for member in self.config.members:
            table = []
            member_type = self.get_type(member)
            for member_token in member.tokens:
                token = next(filter(lambda token: token.name == member_token.token_name, self.config.tokens))
                table.append([
                    format_amount(member_type.balance(token.name, token.address), token.name),
                    format_amount(member_token.min_amount, token.name) if member_token.min_amount else "",
                    format_amount(member_token.max_amount, token.name) if member_token.max_amount else ""
                ])

            members_data = members_data + self.add_first_column(table, member.name)
            members_data.append(["","","",""])

        return self.print_base_table(base_data) + "\n\n" + \
               self.print_members_table(members_data) + "\n\n" + \
               "Generated at: " + datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')

    def dump_inventory(self):
        # The first time we write the inventory dump to a file we log a message
        # so the user knows where to look for that file.
        if self.first_inventory_dump:
            self.logger.info(f"Will regularly write current inventory dump to '{self.arguments.inventory_dump_file}'")
            self.logger.info(f"Use 'watch cat {self.arguments.inventory_dump_file}' to monitor that file")
            self.first_inventory_dump = False

        inventory = self.print_inventory()
        with open(self.arguments.inventory_dump_file, 'w') as file:
            file.write(inventory)

        self.logger.debug(f"Written current inventory dump to '{self.arguments.inventory_dump_file}'")


if __name__ == '__main__':
    InventoryKeeper(sys.argv[1:]).main()
