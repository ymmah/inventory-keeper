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

from pymaker import Address, Wad


class Config:
    def __init__(self):
        self.tokens = []
        self.base_address = None
        self.base_description = None
        self.members = []


class Token:
    def __init__(self, name: str, address: Address):
        self.name = name
        self.address = address


class Member:
    def __init__(self):
        self.type = None
        self.address = None
        self.description = None
        self.token_ranges = {}


class TokenRange:
    def __init__(self, token_name: str, min_amount: Wad, avg_amount: Wad, max_amount: Wad):
        assert(isinstance(min_amount, Wad))
        assert(isinstance(avg_amount, Wad))
        assert(isinstance(max_amount, Wad))

        self.token_name = token_name
        self.min_amount = min_amount
        self.avg_amount = avg_amount
        self.max_amount = max_amount
