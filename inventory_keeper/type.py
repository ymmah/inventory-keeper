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

import logging

from retry import retry
from web3 import Web3

from pyexchange.bibox import BiboxApi
from pyexchange.okex import OKEXApi
from pymaker import Address, eth_transfer
from pymaker.etherdelta import EtherDelta
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket
from pymaker.token import ERC20Token
from pymaker.util import eth_balance

RAW_ETH = Address('0x0000000000000000000000000000000000000000')


def consistent_read(func):
    while True:
        balance_1 = func()
        balance_2 = func()
        if balance_1 == balance_2:
            return balance_1


class EthereumAccount:
    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))

        if token_address is None:
            return Wad(0)
        elif token_address == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            return ERC20Token(web3=self.web3, address=token_address).balance_of(self.address)


class BaseAccount(EthereumAccount):
    def __init__(self, web3: Web3, address: Address, min_eth_balance: Wad):
        assert(isinstance(min_eth_balance, Wad))

        super(BaseAccount, self).__init__(web3, address)
        self.min_eth_balance = min_eth_balance


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
        assert(isinstance(token_address, Address) or (token_address is None))

        if token_address == RAW_ETH:
            return eth_balance(self.web3, self.address)
        else:
            return consistent_read(lambda: self._oasis_balance(token_address))

    def deposit(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        if token_address == RAW_ETH:
            max_amount = base.balance(token_name, token_address) - base.min_eth_balance
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return eth_transfer(web3=self.web3, to=self.address, amount=final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception("No ETH left in the base account")
        else:
            max_amount = base.balance(token_name, token_address)
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return ERC20Token(web3=self.web3, address=token_address).transfer(self.address, final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception(f"No {token_name} left in the base account")

    def withdraw(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        if token_address == RAW_ETH:
            raise Exception(f"ETH withdrawals from OasisDEX are not supported")
        else:
            return ERC20Token(web3=self.web3, address=token_address).transfer_from(self.address, base.address, amount) \
                .transact(from_address=base.address) \
                .successful


class EtherDeltaMarketMakerKeeper:
    def __init__(self, web3: Web3, etherdelta: EtherDelta, address: Address):
        self.web3 = web3
        self.etherdelta = etherdelta
        self.address = address

    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))

        if token_address == RAW_ETH:
            return eth_balance(self.web3, self.address) + self.etherdelta.balance_of(self.address)
        else:
            return ERC20Token(self.web3, token_address).balance_of(self.address) \
                   + self.etherdelta.balance_of_token(token_address, self.address)

    def deposit(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        if token_address == RAW_ETH:
            max_amount = base.balance(token_name, token_address) - base.min_eth_balance
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return eth_transfer(web3=self.web3, to=self.address, amount=final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception("No ETH left in the base account")
        else:
            max_amount = base.balance(token_name, token_address)
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return ERC20Token(web3=self.web3, address=token_address).transfer(self.address, final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception(f"No {token_name} left in the base account")

    def withdraw(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        raise Exception(f"Withdrawals from EtherDelta not supported")


class RadarRelayMarketMakerKeeper(EthereumAccount):
    def deposit(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        if token_address == RAW_ETH:
            max_amount = base.balance(token_name, token_address) - base.min_eth_balance
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return eth_transfer(web3=self.web3, to=self.address, amount=final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception("No ETH left in the base account")
        else:
            max_amount = base.balance(token_name, token_address)
            final_amount = min(amount, max_amount)

            if final_amount > Wad(0):
                return ERC20Token(web3=self.web3, address=token_address).transfer(self.address, final_amount) \
                    .transact(from_address=base.address) \
                    .successful
            else:
                raise Exception(f"No {token_name} left in the base account")

    def withdraw(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        if token_address == RAW_ETH:
            raise Exception(f"ETH withdrawals from RadarRelay are not supported")
        else:
            return ERC20Token(web3=self.web3, address=token_address).transfer_from(self.address, base.address, amount) \
                .transact(from_address=base.address) \
                .successful


class BiboxMarketMakerKeeper:
    def __init__(self, web3: Web3, bibox_api: BiboxApi):
        assert(isinstance(web3, Web3))
        assert(isinstance(bibox_api, BiboxApi))

        self.web3 = web3
        self.bibox_api = bibox_api

    @retry(tries=5, logger=logging.getLogger())
    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))

        all_balances = self.bibox_api.coin_list(retry=True)
        token_balance = next(filter(lambda coin: coin['symbol'] == token_name, all_balances))
        return Wad.from_number(token_balance['totalBalance'])

    def deposit(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        raise Exception(f"Deposits to Bibox not supported")

    def withdraw(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        raise Exception(f"Withdrawals from Bibox not supported")


class OkexMarketMakerKeeper:
    def __init__(self, web3: Web3, okex_api: OKEXApi):
        assert(isinstance(web3, Web3))
        assert(isinstance(okex_api, OKEXApi))

        self.web3 = web3
        self.okex_api = okex_api

    @retry(tries=5, logger=logging.getLogger())
    def balance(self, token_name: str, token_address: Address) -> Wad:
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))

        balances = self.okex_api.get_balances()

        return Wad.from_number(balances['free'][token_name.lower()]) + \
               Wad.from_number(balances['freezed'][token_name.lower()])

    def deposit(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        raise Exception(f"Deposits to OKEX not supported")

    def withdraw(self, base: BaseAccount, token_name: str, token_address: Address, amount: Wad) -> bool:
        assert(isinstance(base, BaseAccount))
        assert(isinstance(token_name, str))
        assert(isinstance(token_address, Address) or (token_address is None))
        assert(isinstance(amount, Wad))

        raise Exception(f"Withdrawals from OKEX not supported")
