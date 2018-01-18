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

import threading
from pprint import pformat

import os
from web3 import Web3

from inventory_keeper.type import OasisMarketMakerKeeper, RadarRelayMarketMakerKeeper, BiboxMarketMakerKeeper, \
    EtherDeltaMarketMakerKeeper
from pyexchange.bibox import BiboxApi
from pymaker import Address
from pymaker.etherdelta import EtherDelta
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket


class OasisCache:
    def __init__(self, web3: Web3):
        assert(isinstance(web3, Web3))

        self.web3 = web3
        self._cache = {}
        self._lock = threading.Lock()

    def get_otc(self, oasis_address: Address):
        assert(isinstance(oasis_address, Address))

        with self._lock:
            if oasis_address not in self._cache:
                self._cache[oasis_address] = MatchingMarket(web3=self.web3, address=oasis_address)

        return self._cache[oasis_address]


class Config:
    def __init__(self, data: dict):
        assert(isinstance(data, dict))

        self.tokens = [Token(key, Address(value)) for key, value in data['tokens'].items()]
        self.base_name = data['base']['name']
        self.base_address = Address(data['base']['address'])
        self.base_min_eth_balance = Wad.from_number(data['base']['minEthBalance'])
        self.members = [Member(item) for item in data['members']]

    def __repr__(self):
        return pformat(vars(self))


class Token:
    def __init__(self, name: str, address: Address):
        assert(isinstance(name, str))
        assert(isinstance(address, Address))

        self.name = name
        self.address = address

    def __repr__(self):
        return pformat(vars(self))


class Member:
    def __init__(self, data: dict):
        assert(isinstance(data, dict))

        self.name = data['name']
        self.type = data['type']
        self.config = data['config']
        self.tokens = [MemberToken(key, value) for key, value in data['tokens'].items()]
        self._type_object = None

    def implementation(self, web3: Web3, oasis_cache: OasisCache):
        assert(isinstance(web3, Web3))
        assert(isinstance(oasis_cache, OasisCache))

        if self._type_object is not None:
            return self._type_object

        if self.type == 'oasis-market-maker-keeper':
            oasis_address = Address(self.config['oasisAddress'])
            market_maker_address = Address(self.config['marketMakerAddress'])

            self._type_object = OasisMarketMakerKeeper(web3=web3,
                                                      otc=oasis_cache.get_otc(oasis_address),
                                                      address=market_maker_address)
        elif self.type == 'etherdelta-market-maker-keeper':
            etherdelta_address = Address(self.config['etherDeltaAddress'])
            market_maker_address = Address(self.config['marketMakerAddress'])

            self._type_object = EtherDeltaMarketMakerKeeper(web3=web3,
                                               etherdelta=EtherDelta(web3=web3, address=etherdelta_address),
                                               address=market_maker_address)
        elif self.type == 'radarrelay-market-maker-keeper':
            market_maker_address = Address(self.config['marketMakerAddress'])
            self._type_object = RadarRelayMarketMakerKeeper(web3=web3, address=market_maker_address)
        elif self.type == 'bibox-market-maker-keeper':
            bibox_api = BiboxApi(api_server="https://api.bibox.com",
                                 api_key=self._environ(self.config['apiKey']),
                                 secret=self._environ(self.config['secret']),
                                 timeout=9.5)
            self._type_object = BiboxMarketMakerKeeper(web3=web3, bibox_api=bibox_api)
        else:
            raise Exception(f"Unknown member type: '{self.type}'")

        return self._type_object

    @staticmethod
    def _environ(value: str):
        if value.startswith('$'):
            return os.environ[value[1:]]
        else:
            return value

    def __repr__(self):
        return pformat(vars(self))


class MemberToken:
    def __init__(self, token_name: str, data: dict):
        assert(isinstance(token_name, str))
        assert(isinstance(data, dict))

        self.token_name = token_name
        self.min_amount = Wad.from_number(data['minAmount']) if 'minAmount' in data else None
        self.avg_amount = Wad.from_number(data['avgAmount']) if 'avgAmount' in data else None
        self.max_amount = Wad.from_number(data['maxAmount']) if 'maxAmount' in data else None

    def __repr__(self):
        return pformat(vars(self))
