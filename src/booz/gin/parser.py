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


UNUSED = object()


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

    def __or__(self, other):
        if isinstance(other, Alt):
            return Alt(self, *other.parsers)
        else:
            return Alt(self, other)

    def __getitem__(self, func):
        return Action(self, func)


class Char(Parser):

    def __init__(self, chars=None):
        self.__chars = None if chars is None else set(chars)

    @property
    def chars(self):
        return self.__chars

    def _parse(self, input):
        c = input.read(1)
        if c == '':
            return False, None
        else:
            local_chars = self.__chars
            if local_chars is None:
                return True, c
            elif c in local_chars:
                return True, c
            else:
                return False, None


class _AggregateParser(Parser):

    def __init__(self, *parsers):
        self.__parsers = tuple(parsers)

    @property
    def parsers(self):
        return self.__parsers


class Seq(_AggregateParser):

    def _parse(self, input):
        values = []
        for parser in self.parsers:
            result, value = parser.parse(input)
            if not result:
                return False, None
            else:
                values.append(value)
        return True, tuple(values)

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(*(self.parsers + other.parsers))
        else:
            return Seq(*(self.parsers + (other,)))


class Alt(_AggregateParser):

    def _parse(self, input):
        for parser in self.parsers:
            result, value = parser.parse(input)
            if result:
                return True, value
        return False, None

    def __or__(self, other):
        if isinstance(other, Alt):
            return Alt(*(self.parsers + other.parsers))
        else:
            return Alt(*(self.parsers + (other,)))


class Action(Parser):

    def __init__(self, parser, func):
        self.__parser = parser
        self.__func = func

    @property
    def parser(self):
        return self.__parser

    @property
    def func(self):
        return self.__func

    def _parse(self, input):
        status, value = self.__parser.parse(input)
        if status:
            return True, self.__func(value)
        else:
            return False, None
