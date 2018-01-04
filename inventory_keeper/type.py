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

from web3 import Web3

from pymaker import Address
from pymaker.bibox import BiboxApi
from pymaker.etherdelta import EtherDelta
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket
from pymaker.token import ERC20Token
from pymaker.util import eth_balance

RAW_ETH = Address('0x0000000000000000000000000000000000000000')


class EthereumAccount:
    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address))

        if token_address == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            return ERC20Token(web3=self.web3, address=token_address).balance_of(self.address)


class OasisMarketMakerKeeper:
    def __init__(self, web3: Web3, otc: MatchingMarket, address: Address):
        self.web3 = web3
        self.otc = otc
        self.address = address

    def _oasis_balance(self, token: Address):
        assert(isinstance(token, Address))

        # In order to calculate Oasis market maker keeper balance, we have add the balance
        # locked in keeper's open orders...
        our_orders = self.otc.get_orders_by_maker(self.address)
        our_sell_orders = filter(lambda order: order.pay_token == token, our_orders)
        balance_in_our_sell_orders = sum(map(lambda order: order.pay_amount, our_sell_orders), Wad(0))

        # ...and the balance left in the keeper accounnt
        balance_in_account = ERC20Token(web3=self.web3, address=token).balance_of(self.address)

        return balance_in_our_sell_orders + balance_in_account

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address))

        if token_address == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            while True:
                balance_1 = self._oasis_balance(token_address)
                balance_2 = self._oasis_balance(token_address)
                if balance_1 == balance_2:
                    return balance_1

    def can_deposit(self):
        return False

    def deposit(self, base: Address, token: Address, amount: Wad) -> bool:
        assert(isinstance(base, Address))
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))

        # TODO exception for RAW_ETH

        return ERC20Token(web3=self.web3, address=token).transfer(self.address, amount) \
            .transact({'from': base}) \
            .successful

    def can_withdraw(self):
        return False

    def withdraw(self, base: Address, token: Address, amount: Wad) -> bool:
        assert(isinstance(base, Address))
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))

        # TODO exception for RAW_ETH

        return ERC20Token(web3=self.web3, address=token).transfer(base, amount) \
            .transact({'from': self.address}) \
            .successful


class EtherDeltaMarketMakerKeeper:
    def __init__(self, web3: Web3, etherdelta: EtherDelta, address: Address):
        self.web3 = web3
        self.etherdelta = etherdelta
        self.address = address

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address))

        if token_address == RAW_ETH:
            return eth_balance(self.web3, self.address) + self.etherdelta.balance_of(self.address)
        else:
            return ERC20Token(self.web3, token_address).balance_of(self.address) \
                   + self.etherdelta.balance_of_token(token_address, self.address)

    def can_deposit(self):
        return False


class BiboxMarketMakerKeeper:
    def __init__(self, web3: Web3, bibox_api: BiboxApi):
        assert(isinstance(web3, Web3))
        assert(isinstance(bibox_api, BiboxApi))

        self.web3 = web3
        self.bibox_api = bibox_api

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address))

        all_balances = self.bibox_api.coin_list(retry=True)
        token_balance = next(filter(lambda coin: coin['symbol'] == token_name, all_balances))
        return Wad.from_number(token_balance['totalBalance'])

    def can_deposit(self):
        return False

    def can_withdraw(self):
        return False


class RadarRelayMarketMakerKeeper(EthereumAccount):
    pass

