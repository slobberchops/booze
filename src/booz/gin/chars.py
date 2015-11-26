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


class FuncChar(parser.Parser):

    def __init__(self, func):
        self.__func = func

    @property
    def attr_type(self):
        return parser.AttrType.STRING

    @property
    def func(self):
        return self.__func

    def _parse(self, state):
        c = state.read(1)
        if self.__func(c):
            state.commit(c)


alnum = FuncChar(str.isalnum)
alpha = FuncChar(str.isalpha)
blank = parser.Char(' \t')
digit = FuncChar(str.isdigit)
lower = FuncChar(str.islower)
printable = FuncChar(str.isprintable)
print_ = printable
space = FuncChar(str.isspace)
upper = FuncChar(str.isupper)
xdigit = parser.Char(string.hexdigits)
