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

import string

from . import parser


class PredicateChar(parser.Parser):
    """Character parser that determines character inclusion using predicate."""

    def __init__(self, func):
        self.__func = func

    @property
    def attr_type(self):
        return parser.AttrType.STRING

    @property
    def predicate(self):
        return self.__func

    def _parse(self, state):
        c = state.read(1)
        if self.__func(c):
            state.commit(c)


alnum = PredicateChar(str.isalnum)
alpha = PredicateChar(str.isalpha)
blank = parser.Char(' \t')
digit = PredicateChar(str.isdigit)
lower = PredicateChar(str.islower)
printable = PredicateChar(str.isprintable)
print_ = printable
space = PredicateChar(str.isspace)
upper = PredicateChar(str.isupper)
xdigit = parser.Char(string.hexdigits)
