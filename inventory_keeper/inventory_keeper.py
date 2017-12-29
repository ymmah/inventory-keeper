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
import logging
import sys

from texttable import Texttable
from web3 import Web3, HTTPProvider

from pymaker.lifecycle import Web3Lifecycle


class InventoryKeeper:
    """Keeper acting as an inventory manager for market maker keeper on other bots."""

    logger = logging.getLogger('inventory-keeper')

    def __init__(self, args: list, **kwargs):
        self.clear_screen()
        self.print()

        parser = argparse.ArgumentParser(prog='inventory-keeper')

        parser.add_argument("--rpc-host", type=str, default="localhost",
                            help="JSON-RPC host (default: `localhost')")

        parser.add_argument("--rpc-port", type=int, default=8545,
                            help="JSON-RPC port (default: `8545')")

        parser.add_argument("--config", type=str, required=True,
                            help="Configuration file")

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
        self.web3.eth.defaultAccount = self.arguments.eth_from

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                            level=(logging.DEBUG if self.arguments.debug else logging.INFO))

    def main(self):
        with Web3Lifecycle(self.web3) as lifecycle:
            self.lifecycle = lifecycle

    def clear_screen(self):
        print("\033[H\033[J")

    def print(self):
        base = [["Base account", "62.412000000000000000 ETH_"],
                ["(0x4234234234234234234234234433232323234424)", "4,000.000000000000000000 WETH"],
                ["", "313,000.000000000000000000 SAI_"]]

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't'])
        table.set_cols_align(['l', 'r'])
        table.set_cols_width([60, 35])
        table.add_rows([["Base account", "Balance"]] + base)

        print(table.draw())
        print("")

        base = [["Oasis keeper 1", "62.412000000000000000 ETH_", "62.412000000000000000 ETH_", "62.412000000000000000 ETH_"],
                ["(0x2342342344242343332344244332323223423424)", "4,000.000000000000000000 WETH", "4,000.000000000000000000 WETH", "4,000.000000000000000000 WETH"],
                ["", "313,000.000000000000000000 SAI_", "313,000.000000000000000000 SAI_", "313,000.000000000000000000 SAI_"]]

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't'])
        table.set_cols_align(['l', 'r', 'r', 'r'])
        table.set_cols_width([60, 35, 37, 33])
        table.add_rows([["Member accounts", "Balance", "Min", "Max"]] + base)

        print(table.draw())



if __name__ == '__main__':
    InventoryKeeper(sys.argv[1:]).main()
