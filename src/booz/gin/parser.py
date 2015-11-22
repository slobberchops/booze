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


class Parser:
    """Base class for parsers."""

    def parse(self, input):
        pos = input.tell()
        result, value = False, None
        try:
            result, value = self._parse(input)
        finally:
            if not result:
                input.seek(pos)
        return result, value

    def _parse(self, input):
        return False, None

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(self, *other.parsers)
        else:
            return Seq(self, other)


class Seq(Parser):

    def __init__(self, *parsers):
        self.__parsers = tuple(parsers)

    @property
    def parsers(self):
        return self.__parsers

    def _parse(self, input):
        for parser in self.__parsers:
            result, value = parser.parse(input)
            if not result:
                return False, None
        return True, tuple(value)

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(*(self.parsers + other.parsers))
        else:
            return Seq(*(self.parsers + (other,)))
