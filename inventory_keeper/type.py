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
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket
from pymaker.token import ERC20Token
from pymaker.util import eth_balance

RAW_ETH = Address('0x0000000000000000000000000000000000000000')


class EthereumAccount:
    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address

    def balance(self, token: Address) -> Wad:
        assert(isinstance(token, Address))

        if token == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            return ERC20Token(web3=self.web3, address=token).balance_of(self.address)


class OasisMarketMakerKeeper:
    def __init__(self, web3: Web3, otc: MatchingMarket, address: Address):
        self.web3 = web3
        self.otc = otc
        self.address = address

    def _oasis_balance(self, token: Address):
        assert(isinstance(token, Address))

        # In order to calculate Oasis market maker keeper balance, we have add the balance
        # locked in keeper's open orders...
        our_orders = filter(lambda order: order.maker == self.address, self.otc.get_orders())
        our_sell_orders = filter(lambda order: order.pay_token == token, our_orders)
        balance_in_our_sell_orders = sum(map(lambda order: order.pay_amount, our_sell_orders), Wad(0))

        # ...and the balance left in the keeper accounnt
        balance_in_account = ERC20Token(web3=self.web3, address=token).balance_of(self.address)

        return balance_in_our_sell_orders + balance_in_account

    def balance(self, token: Address) -> Wad:
        assert(isinstance(token, Address))

        if token == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            while True:
                balance_1 = self._oasis_balance(token)
                balance_2 = self._oasis_balance(token)
                if balance_1 == balance_2:
                    return balance_1

    def deposit(self, base: Address, token: Address, amount: Wad) -> bool:
        assert(isinstance(base, Address))
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))

        # TODO exception for RAW_ETH

        return ERC20Token(web3=self.web3, address=token).transfer(self.address, amount) \
            .transact({'from': base}) \
            .successful

    def withdraw(self, base: Address, token: Address, amount: Wad) -> bool:
        assert(isinstance(base, Address))
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))

        # TODO exception for RAW_ETH

        return ERC20Token(web3=self.web3, address=token).transfer(base, amount) \
            .transact({'from': self.address}) \
            .successful


class RadarRelayMarketMakerKeeper(EthereumAccount):
    pass

