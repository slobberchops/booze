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
from . import util


class Attr(parser.Parser):

    def __init__(self, value, attr_type=None):
        if value in (None, parser.UNUSED):
            raise TypeError('May not assign {} to Attr()'.format(value))
        if attr_type is parser.AttrType.UNUSED:
            raise ValueError('Attr may not be UNUSED')
        self.__value = value
        if attr_type is None:
            if isinstance(value, str):
                self.__attr_type = parser.AttrType.STRING
            elif isinstance(value, tuple):
                self.__attr_type = parser.AttrType.TUPLE
            else:
                self.__attr_type = parser.AttrType.OBJECT
        else:
            if not attr_type.compatible(value):
                raise TypeError('Value {} incompatible with AttrType.{}'.format(value, attr_type.name))
            self.__attr_type = attr_type

    @property
    def attr_type(self):
        return self.__attr_type

    @property
    def value(self):
        return self.__value

    def _parse(self, state):
        state.commit(self.__value)


@util.singleton
class eoi(parser.Parser):

    @property
    def attr_type(self):
        return parser.AttrType.UNUSED

    def _parse(self, state):
        if state.read(1) == '':
            state.succeed()


@util.singleton
class eps(parser.Parser):

    @property
    def attr_type(self):
        return parser.AttrType.UNUSED

    def _parse(self, state):
        state.succeed()

