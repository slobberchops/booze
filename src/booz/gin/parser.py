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

import contextlib
import enum
import io

from . import util


@util.singleton
class UNUSED:

    def __repr__(self):
        return 'UNUSED'

    def __bool__(self):
        return False


def as_parser(value):
    if isinstance(value, str):
        return lit(value)
    elif isinstance(value, Parser):
        return value
    else:
        raise TypeError('Unexpected parser type: {}'.format(type(value)))


class ParserState:

    class __Tx:

        commit = False
        success = False
        value = UNUSED

        def __init__(self, pos):
            self.pos = pos

    def __init__(self, input, skipper=None):
        if isinstance(input, str):
            self.__input = io.StringIO(input)
        else:
            self.__input = input
        self.skipper = skipper
        self.__txs = []

    @property
    def skipper(self):
        return self.__skipper

    @skipper.setter
    def skipper(self, skipper):
        if isinstance(skipper, str):
            self.__skipper = Char(skipper)
        elif isinstance(skipper, Parser) or skipper is None:
            self.__skipper = skipper
        else:
            raise TypeError('Unexpected parser {}'.format(type(skipper)))

    @property
    def _tx(self):
        return self.__txs[-1]

    @property
    def committed(self):
        return self._tx.commit

    @property
    def successful(self):
        return self._tx.success

    @property
    def value(self):
        return self._tx.value

    @value.setter
    def value(self, value):
        self._tx.value = value
        self._tx.success = True

    def read(self, *args, **kwargs):
        return self.__input.read(*args, **kwargs)

    def commit(self, value=UNUSED):
        self.value = value
        self._tx.commit = True

    def succeed(self, value=UNUSED):
        self.value = value
        self._tx.commit = False

    def rollback(self):
        self._tx.commit = False
        self._tx.success = False
        del self._tx.value

    def uncommit(self):
        self._tx.commit = False

    def __enter__(self):
        pos = self.__input.tell()
        self.__txs.append(self.__Tx(pos))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.committed:
            self.__input.seek(self._tx.pos)
        del self.__txs[-1]
        return False


class AttrType(enum.Enum):

    UNUSED = 1
    OBJECT = 2
    STRING = 3
    TUPLE = 4


class Parser:
    """Base class for parsers."""

    @property
    def attr_type(self):
        raise NotImplementedError

    def parse(self, input, skipper=None):
        if skipper is not None and isinstance(input, ParserState):
            raise TypeError('May not provide ParserState and new skipper')
        if not isinstance(input, ParserState):
            input = ParserState(input, skipper)
        with input as state:
            if state.skipper:
                status = True
                skipper = state.skipper
                state.skipper = None
                try:
                    while status:
                        with state:
                            status, _ = skipper.parse(state)
                            if status:
                                state.commit()
                finally:
                    state.skipper = skipper
            self._parse(state)
            return state.successful, state.value if state.successful else None

    def _parse(self, state):
        pass

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(self, *other.parsers)
        else:
            return Seq(self, other)

    def __rlshift__(self, other):
        return as_parser(other) << self

    def __or__(self, other):
        if isinstance(other, Alt):
            return Alt(self, *other.parsers)
        else:
            return Alt(self, other)

    def __ror__(self, other):
        return as_parser(other) | self

    def __getitem__(self, func):
        return Action(self, func)

    def __neg__(self):
        return Repeat(0, 1)[self]

    def __pos__(self):
        return Repeat(1)[self]

    def __invert__(self):
        return predicate[self]


class Char(Parser):

    def __init__(self, chars=None):
        self.__chars = None if chars is None else set(chars)

    @property
    def attr_type(self):
        return AttrType.STRING

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
    def attr_type(self):
        return AttrType.STRING

    @property
    def string(self):
        return self.__string

    def _parse(self, state):
        string = state.read(len(self.__string))
        if string == self.__string:
            state.commit(string)


class AggregateParser(Parser):

    def __init__(self, *parsers):
        self.__parsers = tuple(as_parser(p) for p in parsers)

    @property
    def parsers(self):
        return self.__parsers


class Seq(AggregateParser):

    @util.calculated_property
    def attr_type(self):
        types = self.__attr_types
        if isinstance(types, tuple):
            return AttrType.TUPLE
        else:
            return types

    @util.calculated_property
    def __attr_types(self):
        all_types = tuple(p.attr_type for p in self.parsers if p.attr_type is not AttrType.UNUSED)
        if len(all_types) == 0:
            return AttrType.UNUSED
        elif len(all_types) == 1:
            return all_types[0]
        else:
            return all_types


    def _parse(self, state):
        values = []
        for parser in self.parsers:
            result, value = parser.parse(state)
            if not result:
                return
            elif parser.attr_type != AttrType.UNUSED:
                values.append(value)

        if len(values) == 0:
            state.commit(UNUSED)
        elif len(values) == 1:
            state.commit(values[0])
        else:
            state.commit(tuple(values))

    def __lshift__(self, other):
        if isinstance(other, Seq):
            return Seq(*(self.parsers + other.parsers))
        else:
            return Seq(*(self.parsers + (other,)))


class Alt(AggregateParser):

    @util.calculated_property
    def attr_type(self):
        all_types = tuple(p.attr_type for p in self.parsers)
        if len(all_types) == 0:
            return AttrType.UNUSED
        else:
            found_type = all_types[0]
            return found_type if all(t == found_type for t in all_types[1:]) else AttrType.OBJECT

    def _parse(self, state):
        for parser in self.parsers:
            result, value = parser.parse(state)
            if result:
                state.commit(value)
                break

    def __or__(self, other):
        if isinstance(other, Alt):
            return Alt(*(self.parsers + other.parsers))
        else:
            return Alt(*(self.parsers + (other,)))


class Unary(Parser):

    def __init__(self, parser):
        self.__parser = parser

    @property
    def attr_type(self):
        return self.__parser.attr_type

    @property
    def parser(self):
        return self.__parser

    def _parse(self, state):
        self.parser._parse(state)


class Action(Unary):

    def __init__(self, parser, func, attr_type=AttrType.OBJECT):
        super(Action, self).__init__(parser)
        self.__func = func
        self.__attr_type = attr_type

    @property
    def attr_type(self):
        return self.__attr_type

    @property
    def func(self):
        return self.__func

    def _parse(self, state):
        super(Action, self)._parse(state)
        if state.successful:
            if self.parser.attr_type == AttrType.UNUSED:
                params = ()
            else:
                params = state.value if isinstance(state.value, tuple) else (state.value,)
            state.value = self.__func(*params)


def directive_class(unary_parser):
    class Directive:

        __parser_type__ = unary_parser

        def __init__(self, *args, **kwargs):
            self.__args = args
            self.__kwargs = kwargs

        def __getitem__(self, parser):
            return unary_parser(parser, *self.__args, **self.__kwargs)
    return Directive


class DirectiveParser(Unary):

    def _direct(self, state):
        raise NotImplementedError

    def _parse(self, state):
        with self._direct(state):
            super(DirectiveParser, self)._parse(state)


class FuncDirectiveParser(DirectiveParser):

    def __init__(self, parser, func, attr_type=None):
        super(FuncDirectiveParser, self).__init__(parser)
        self.__func = func
        self.__attr_type = attr_type if attr_type else parser.attr_type

    @property
    def attr_type(self):
        return self.__attr_type

    @property
    def func(self):
        return self.__func

    def _direct(self, state):
        return self.func(state)


class FuncDirective:

    def __init__(self, func, attr_type=None):
        self.__func = func
        self.__attr_type = attr_type

    @property
    def attr_type(self):
        return self.__attr_type

    @property
    def func(self):
        return self.__func

    def __getitem__(self, parser):
        return FuncDirectiveParser(parser, self.__func, self.__attr_type if self.__attr_type else parser.attr_type)


def func_directive(attr_type=None):
    def func_directive_decorator(func):
        return FuncDirective(func, attr_type)
    return func_directive_decorator


def post_directive(attr_type=None):
    def post_directive_decorator(post_func):
        @func_directive(attr_type)
        @contextlib.contextmanager
        def directive(state):
            yield
            if state.successful:
                post_func(state)
            return False
        return directive
    return post_directive_decorator



@directive_class
class Repeat(Unary):

    def __init__(self, parser, minimum=0, maximum=None):
        super(Repeat.__parser_type__, self).__init__(parser)
        self.__minimum = minimum
        self.__maximum = maximum

    @util.calculated_property
    def attr_type(self):
        if self.is_optional:
            return self.parser.attr_type
        else:
            return AttrType.UNUSED if self.parser.attr_type == AttrType.UNUSED else AttrType.TUPLE

    @util.calculated_property
    def is_optional(self):
        return self.__minimum == 0 and self.__maximum == 1

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
            with state as next_state:
                super(Repeat.__parser_type__, self)._parse(next_state)
                if next_state.successful:
                    values.append(next_state.value)
                else:
                    break
            count += 1
        if self.is_optional:
            state.commit(values[0] if values else UNUSED)
        elif count >= self.__minimum:
            state.commit(UNUSED if self.attr_type == AttrType.UNUSED else tuple(values))

    def __neg__(self):
        if self.__minimum == 1:
            return Repeat(0, self.__maximum)[self.parser]
        else:
            return super(Repeat.__parser_type__, self).__neg__()


@post_directive(AttrType.UNUSED)
def omit(state):
    state.value = UNUSED


def _as_string(value):
    if value is UNUSED:
        value = ''
    elif isinstance(value, tuple):
        value = ''.join(_as_string(v) for v in value)
    return str(value)


@post_directive(AttrType.STRING)
def as_string(state):
    state.value = _as_string(state.value)


def lit(string):
    return omit[String(string)]


@func_directive()
@contextlib.contextmanager
def object_lexeme(state):
    skipper = state.skipper
    state.skipper = None
    yield
    state.skipper = skipper
    return False


@util.singleton
class lexeme:

    def __getitem__(self, parser):
        return as_string[object_lexeme[parser]]


class Rule(Parser):

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
    def parser(self, parser):
        if self.__expected_attr_type and self.__expected_attr_type != parser.attr_type:
            raise ValueError('Unexpected attribute type')
        self.__parser = as_parser(parser)

    def _parse(self, state):
        return self.__parser._parse(state)

    def __imod__(self, other):
        self.parser = other
        return self


@post_directive(AttrType.UNUSED)
def predicate(state):
    state.value = UNUSED
    state.uncommit()


@func_directive(AttrType.UNUSED)
@contextlib.contextmanager
def not_predicate(state):
    yield
    if state.successful:
        state.rollback()
    else:
        state.succeed()

not_ = not_predicate
