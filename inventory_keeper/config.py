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

from pprint import pformat

from pymaker import Address
from pymaker.numeric import Wad


class Config:
    def __init__(self, data: dict):
        assert(isinstance(data, dict))

        self.tokens = [Token(key, Address(value)) for key, value in data['tokens'].items()]
        self.base_address = Address(data['base']['address'])
        self.base_description = data['base']['description']
        self.members = map(lambda item: Member(item), data['members'])

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

        self.type = data['type']
        self.address = Address(data['address'])
        self.description = data['description']
        self.tokens = [MemberToken(key, value) for key, value in data['tokens'].items()]

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
