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
import inspect
import io

from . import local_vars
from .. import util
from .. import whiskey


@util.singleton
class UNUSED:

    def __repr__(self):
        return 'UNUSED'

    @staticmethod
    def __bool__():
        return False


def as_parser(value):
    if isinstance(value, str):
        return lit(value)
    elif isinstance(value, dict):
        return Symbols(value)
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

    def __init__(self, state_input, skipper=None):
        if isinstance(state_input, str):
            self.__input = io.StringIO(state_input)
        else:
            self.__input = state_input
        self.skipper = skipper
        self.__tx = None
        self.__scope = None

    @property
    def input(self):
        return self.__input

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
        return self.__tx

    @property
    def committed(self):
        return self._tx.commit

    @property
    def successful(self):
        return self._tx.success

    @property
    def value(self):
        return self._tx.value

    @property
    def scope(self):
        return self.__scope

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

    @contextlib.contextmanager
    def open_scope(self, *args, **kwargs):
        previous_scope = self.__scope
        self.__scope = local_vars.LocalScope(*args, **kwargs)
        try:
            yield self.__scope
        finally:
            self.__scope = previous_scope

    @contextlib.contextmanager
    def open_transaction(self):
        tx = self._tx
        self.__tx = ParserState.__Tx(self.__input.tell())
        try:
            yield self
        finally:
            if not self.committed:
                self.__input.seek(self._tx.pos)
            self.__tx = tx

    def invoke(self, value):
        scope = self.__scope
        args = scope.args if scope else ()
        kwargs = scope.kwargs if scope else {}
        vars = scope.vars if scope else local_vars.Vars()
        return whiskey.invoke(value, *args, vars=vars, **kwargs)


class AttrType(enum.Enum):

    UNUSED = 1
    OBJECT = 2
    STRING = 3
    TUPLE = 4

    def compatible(self, value):
        if self in (AttrType.UNUSED, AttrType.OBJECT):
            return True
        elif isinstance(value, str) and self == AttrType.STRING:
            return True
        elif isinstance(value, tuple) and self == AttrType.TUPLE:
            return True
        else:
            return False

    def check_compatible(self, value):
        if not self.compatible(value):
            raise TypeError('Value {} incompatible with AttrType.{}'.format(repr(value), self.name))

    @staticmethod
    def type_for(value):
        if value is UNUSED:
            return AttrType.UNUSED
        if isinstance(value, str):
            return AttrType.STRING
        elif isinstance(value, tuple):
            return AttrType.TUPLE
        else:
            return AttrType.OBJECT


class Parser:
    """Base class for parsers."""

    @property
    def attr_type(self):
        raise NotImplementedError

    def parse(self, parser_input, skipper=None):
        if skipper is not None and isinstance(parser_input, ParserState):
            raise TypeError('May not provide ParserState and new skipper')
        if not isinstance(parser_input, ParserState):
            parser_input = ParserState(parser_input, skipper)
        with parser_input.open_transaction() as state:
            if state.skipper:
                status = True
                skipper = state.skipper
                state.skipper = None
                try:
                    while status:
                        with state.open_transaction():
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
        return SemanticAction(self, func)

    def __neg__(self):
        return Repeat(0, 1)[self]

    def __pos__(self):
        return Repeat(1)[self]

    def __invert__(self):
        return predicate[self]


class Char(Parser):

    def __init__(self, chars=None):
        if chars is None:
            self.__chars = None
        elif isinstance(chars, whiskey.Action):
            self.__chars = chars
        else:
            self.__chars = set(chars)

    @property
    def attr_type(self):
        return AttrType.STRING

    @property
    def chars(self):
        return self.__chars

    def _parse(self, state):
        c = state.read(1)
        if c != '':
            local_chars = state.invoke(self.__chars)
            if local_chars is not None and not isinstance(local_chars, set):
                local_chars = set(local_chars)
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
        value = state.invoke(self.__string)
        string = state.read(len(value))
        if string == value:
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
            # TODO: Each value can be an action.
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
            # TODO: Each value can be an action.
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


class SemanticAction(Unary):

    def __init__(self, parser, func, attr_type=AttrType.OBJECT):
        super(SemanticAction, self).__init__(parser)
        self.__func = func
        self.__attr_type = attr_type

    @property
    def attr_type(self):
        return self.__attr_type

    @property
    def func(self):
        return self.__func

    def _parse(self, state):
        super(SemanticAction, self)._parse(state)
        if state.successful:
            if self.parser.attr_type == AttrType.UNUSED:
                params = ()
            else:
                params = state.value if isinstance(state.value, tuple) else (state.value,)


            if isinstance(self.__func, whiskey.Action):
                func = self.__func.invoke
            else:
                func = self.__func

            sig = inspect.signature(func)
            binding = None
            if state.scope:
                try:
                    binding = sig.bind(*params, vars=state.scope.vars)
                except TypeError:
                    pass

            if not binding:
                binding = sig.bind(*params)

            state.value = func(*binding.args, **binding.kwargs)


class Symbols(Parser):

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
                    attr_type = AttrType.type_for(value)
                else:
                    next_type = AttrType.type_for(value)
                    if attr_type != next_type:
                        attr_type = AttrType.OBJECT
                if attr_type == AttrType.OBJECT:
                    break
            self.__attr_type = attr_type

        self.__symbols = []
        for symbol, value in sorted(symbols.items()):
            self.__symbols.append((String(symbol), value))

    @property
    def attr_type(self):
        return self.__attr_type

    def _parse(self, state):
        for parser, value in self.__symbols:
            status, _ = parser.parse(state)
            if status:
                state.commit(value)
                break


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
            with state.open_transaction() as next_state:
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
    try:
        yield
    finally:
        state.skipper = skipper


@util.singleton
class lexeme:

    def __getitem__(self, parser):
        return as_string[object_lexeme[parser]]


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
