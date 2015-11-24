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

from . import util

class UNUSED:

    def __repr__(self):
        return 'UNUSED'

UNUSED = UNUSED()


def tuple_to_attributes(tpl):
    tpl = tuple(v for v in tpl if v != UNUSED)
    if not tpl:
        return UNUSED
    else:
        if len(tpl) == 1:
            return tpl[0]
        else:
            return tpl


class ParserState:

    def __init__(self, input):
        if isinstance(input, ParserState):
            input = input.__input
        self.__input = input
        self.__pos = self.__input.tell()
        self.__commit = False
        self.__success = False
        self.__value = UNUSED

    @property
    def committed(self):
        return self.__commit

    @property
    def successful(self):
        return self.__success

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value
        self.__success = True

    def read(self, *args, **kwargs):
        return self.__input.read(*args, **kwargs)

    def commit(self, value):
        self.value = value
        self.__commit = True

    def rollback(self):
        self.__commit = False
        self.__success = False
        self.__value = UNUSED

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.committed:
            self.__input.seek(self.__pos)
        return False


class Parser:
    """Base class for parsers."""

    def parse(self, input):
        with ParserState(input) as state:
            self._parse(state)
            return state.successful, state.value if state.successful else None

    def _parse(self, state):
        pass

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

    def __neg__(self):
        return Repeat(0, 1)[self]

    def __pos__(self):
        return Repeat(1)[self]


class Char(Parser):

    def __init__(self, chars=None):
        self.__chars = None if chars is None else set(chars)

    @property
    def chars(self):
        return self.__chars

    def _parse(self, state):
        c = state.read(1)
        if c != '':
            local_chars = self.__chars
            if local_chars is None or c in local_chars:
                state.commit(c)


class String(Parser):

    def __init__(self, string):
        self.__string = string

    @property
    def string(self):
        return self.__string

    def _parse(self, state):
        string = state.read(len(self.__string))
        if string == self.__string:
            state.commit(string)


class AggregateParser(Parser):

    def __init__(self, *parsers):
        self.__parsers = tuple(parsers)

    @property
    def parsers(self):
        return self.__parsers


class Seq(AggregateParser):

    def _parse(self, state):
        values = []
        for parser in self.parsers:
            result, value = parser.parse(state)
            if not result:
                return
            else:
                values.append(value)
        state.commit(tuple_to_attributes(values))

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(*(self.parsers + other.parsers))
        else:
            return Seq(*(self.parsers + (other,)))


class Alt(AggregateParser):

    def _parse(self, state):
        for parser in self.parsers:
            result, value = parser.parse(state)
            if result:
                state.commit(value)

    def __or__(self, other):
        if isinstance(other, Alt):
            return Alt(*(self.parsers + other.parsers))
        else:
            return Alt(*(self.parsers + (other,)))


class _Unary(Parser):

    def __init__(self, parser):
        self.__parser = parser

    @property
    def parser(self):
        return self.__parser

    def _parse(self, state):
        self.parser._parse(state)


class Action(_Unary):

    def __init__(self, parser, func):
        super(Action, self).__init__(parser)
        self.__func = func

    @property
    def func(self):
        return self.__func

    def _parse(self, state):
        super(Action, self)._parse(state)
        if state.successful:
            state.value = self.__func(state.value)


def directive_class(unary_parser):
    class Directive:

        __parser_type__ = unary_parser

        def __init__(self, *args, **kwargs):
            self.__args = args
            self.__kwargs = kwargs

        def __getitem__(self, parser):
            return unary_parser(parser, *self.__args, **self.__kwargs)
    return Directive


@directive_class
class Repeat(_Unary):

    def __init__(self, parser, minimum=0, maximum=None):
        super(Repeat.__parser_type__, self).__init__(parser)
        self.__minimum = minimum
        self.__maximum = maximum

    @property
    def minimum(self):
        return self.__minimum

    @property
    def maximum(self):
        return self.__maximum

    def _parse(self, state):
        count = 0
        values = []
        while self.__maximum is None or count < self.__maximum:
            with ParserState(state) as next_state:
                super(Repeat.__parser_type__, self)._parse(next_state)
                if next_state.successful:
                    values.append(next_state.value)
                else:
                    break
            count += 1
        if count >= self.__minimum:
            state.commit(tuple_to_attributes(values))

    def __neg__(self):
        if self.__minimum == 1:
            return Repeat(0, self.__maximum)[self.parser]
        else:
            return super(Repeat.__parser_type__, self).__neg__()


@util.singleton
@directive_class
class omit(_Unary):

    def _parse(self, state):
        super(omit.__parser_type__, self)._parse(state)
        if state.successful:
            state.value = UNUSED


def _as_string(value):
    if value is UNUSED:
        value = ''
    elif isinstance(value, tuple):
        value = ''.join(_as_string(v) for v in value)
    return str(value)


@util.singleton
@directive_class
class as_string(_Unary):

    def _parse(self, state):
        super(as_string.__parser_type__, self)._parse(state)
        if state.successful:
            state.value = _as_string(state.value)
