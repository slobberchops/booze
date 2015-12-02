# Copyright 2015 Rafe Kaplan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from . import parser


class Rule(parser.Parser):

    def __init__(self, expected_attr_type=None):
        self.__expected_attr_type = expected_attr_type

    @property
    def attr_type(self):
        if self.__expected_attr_type:
            return self.__expected_attr_type
        else:
            try:
                parser = self.__parser
            except AttributeError:
                raise NotImplementedError
            else:
                return parser.attr_type

    @property
    def parser(self):
        return self.__parser

    @parser.setter
    def parser(self, value):
        if self.__expected_attr_type and self.__expected_attr_type != value.attr_type:
            raise ValueError('Unexpected attribute type')
        self.__parser = parser.as_parser(value)

    def _parse(self, state):
        return self.__parser._parse(state)

    def __imod__(self, other):
        self.parser = other
        return self
