# Copyright 2015 Rafe Kaplan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import parser


class Symbols(parser.Parser):

    def __init__(self, symbols, attr_type=None):
        if not symbols:
            raise ValueError('Must provide some symbols')
        if attr_type:
            self.__attr_type = attr_type
            for value in symbols.values():
                attr_type.check_compatible(value)
        else:
            attr_type = None
            for value in symbols.values():
                if attr_type is None:
                    attr_type = parser.AttrType.type_for(value)
                else:
                    next_type = parser.AttrType.type_for(value)
                    if attr_type != next_type:
                        attr_type = parser.AttrType.OBJECT
                if attr_type == parser.AttrType.OBJECT:
                    break
            self.__attr_type = attr_type

        self.__symbols = []
        for symbol, value in sorted(symbols.items()):
            self.__symbols.append((parser.String(symbol), value))

    @property
    def attr_type(self):
        return self.__attr_type

    def _parse(self, state):
        for parser, value in self.__symbols:
            status, _ = parser.parse(state)
            if status:
                state.commit(value)
                break
