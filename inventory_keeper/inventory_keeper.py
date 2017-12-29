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
import json
import logging
import sys

from texttable import Texttable
from web3 import Web3, HTTPProvider

from inventory_keeper.config import Config
from inventory_keeper.type import EthereumAccount, OasisMarketMakerKeeper
from pymaker import Address
from pymaker.lifecycle import Web3Lifecycle
from pymaker.oasis import MatchingMarket


class InventoryKeeper:
    """Keeper acting as an inventory manager for market maker keeper on other bots."""

    logger = logging.getLogger('inventory-keeper')

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='inventory-keeper')

        parser.add_argument("--rpc-host", type=str, default="localhost",
                            help="JSON-RPC host (default: `localhost')")

        parser.add_argument("--rpc-port", type=int, default=8545,
                            help="JSON-RPC port (default: `8545')")

        parser.add_argument("--oasis-address", type=str, required=True,
                            help="Ethereum address of the OasisDEX contract")

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

        parser.add_argument("--debug", dest='debug', action='store_true',
                            help="Enable debug output")

        self.arguments = parser.parse_args(args)

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.otc = MatchingMarket(web3=self.web3, address=Address(self.arguments.oasis_address))
        self.config = Config(json.load(open(self.arguments.config)))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                            level=(logging.DEBUG if self.arguments.debug else logging.INFO))

        self.clear_screen()
        self.print()

    def main(self):
        with Web3Lifecycle(self.web3) as lifecycle:
            self.lifecycle = lifecycle

    def clear_screen(self):
        print("\033[H\033[J")

    def add_first_column(self, table, description, address):
        result = []
        for index, row in enumerate(table):
            if index == 0:
                result.append([description] + row)
            elif index == 1:
                result.append([f"({address})"] + row)
            else:
                result.append([""] + row)

        return result

    def print_base_table(self, table_data):
        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't'])
        table.set_cols_align(['l', 'r'])
        table.set_cols_width([60, 35])
        table.add_rows([["Base account", "Balance"]] + table_data)
        print(table.draw())

    def print(self):
        longest_token_name = max(map(lambda token: len(token.name), self.config.tokens))

        base_type = EthereumAccount(web3=self.web3, address=self.config.base_address)
        base_table = map(lambda token: [str(base_type.balance(token.address)) + " " + token.name.ljust(longest_token_name, ".")], self.config.tokens)
        self.print_base_table(self.add_first_column(base_table, self.config.base_description, self.config.base_address))

        print("")

        members_table = []
        for member in self.config.members:
            type = OasisMarketMakerKeeper(web3=self.web3, otc=self.otc, address=member.address)
            subtable = map(lambda token: [str(type.balance(token.address)) + " " + token.name.ljust(longest_token_name, "."), "", ""], self.config.tokens)

            members_table = members_table + self.add_first_column(subtable, member.description, member.address)
            members_table.append(["","","",""])

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't'])
        table.set_cols_align(['l', 'r', 'r', 'r'])
        table.set_cols_width([60, 35, 37, 33])
        table.add_rows([["Member accounts", "Balance", "Min", "Max"]] + members_table)

        print(table.draw())



if __name__ == '__main__':
    InventoryKeeper(sys.argv[1:]).main()
