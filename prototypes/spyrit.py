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

__author__ = 'rafe'

import operator

class attr:

    def call(self, *args):
        return None

    def __add__(self, other):
        return binop(operator.add, self, make_attr(other))

    def __sub__(self, other):
        return binop(operator.sub, self, make_attr(other))

    def __mul__(self, other):
        return binop(operator.mul, self, make_attr(other))

    def __div__(self, other):
        return binop(operator.div, self, make_attr(other))

    def __call__(self, *params):
        return invoke(self, *params)


class default_attr(attr):


    def call(self, *args):
        if not args:
            return None
        if len(args) == 1:
            return args[0]
        else:
            return args


class parser:

    attrval = default_attr()

    def call_attr(self, *params):
        params = tuple(p for p in (params or ()) if p is not None)
        return self.attrval.call(*params)

    def __getitem__(self, attr):
        self.attrval = make_attr(attr)
        return self

    def __and__(self, other):
        return seq(self, other)

    def __rand__(self, other):
        return seq(other, self)

    def __or__(self, other):
        return alt(self, other)

    def __ror__(self, other):
        return alt(other, self)

    def __neg__(self):
        return opt(self)

    def __invert__(self):
        return kleene(self)

    def __pos__(self):
        return self & ~self

    def parse(self, s):
        return True, self.call_attr(), None


class lit(parser):
    attrval = attr

    def __init__(self, char):
        self._char = char

    def parse(self, s):
        if s.startswith(self._char):
            return True, self.call_attr(self._char), s[len(self._char):]
        else:
            return False, None, s

l = lit


class seq(parser):

    def __init__(self, *parsers):
        self._parsers = []
        for parser in parsers:
            if isinstance(parser, str):
                parser = lit(parser)
            if type(parser) == seq:
                self._parsers.extend(parser._parsers)
            else:
                self._parsers.append(parser)

    def parse(self, s):
        result = []
        status = True
        for parser in self._parsers:
            status, attr, remaining = parser.parse(s)
            if not status:
                return False, result, s
            if attr is not None:
                result.append(attr)
            s = remaining
        else:
            status = True
        return True, self.call_attr(*result), s


class alt(parser):

    def __init__(self, *parsers):
        self._parsers = []
        for parser in parsers:
            if type(parser) == alt:
                self._parsers.extend(parser._parsers)
            else:
                self._parsers.append(parser)

    def parse(self, s):
        for parser in self._parsers:
            status, attr, remaining = parser.parse(s)
            if status:
                return True, self.call_attr(attr), remaining
        return False, None, s


class opt(parser):
    def __init__(self, parser):
        self._parser = parser

    def parse(self, s):
        status, attr, remaining = self._parser.parse(s)
        if status:
            return status, self.call_attr(attr), remaining
        else:
            return True, None, s


class kleene(parser):
    def __init__(self, parser):
        self._parser = parser

    def parse(self, s):
        result = []
        status = True
        while status:
            status, attr, remaining = self._parser.parse(s)
            if status:
                if attr is not None:
                    result.append(attr)
                s = remaining
        return True, self.call_attr(result) or None, s


class grammar(parser):

    def parse(self, s):
        return self.start.parse(s)


class rule(parser):

    def __init__(self, name=None):
        self._name = name

    def __repr__(self):
        return '<grammar {}>'.format(self._name)

    def set(self, parser):
        self._parser = parser

    def __ilshift__(self, parser):
        self.set(parser)
        return self

    def parse(self, s):
        return self._parser.parse(s)


class _dec(parser):

    def __getitem__(self, attr):
        return super(_dec, _dec()).__getitem__(attr)

    def parse(self, s):
        result = None
        while s and s[0] in '01234567890':
            result = (result or 0) * 10
            result += int(s[0])
            s = s[1:]
        if result is None:
            return False, None, s
        else:
            return True, self.call_attr(result), s

dec = _dec()

class sym(alt):

    def __init__(self, *syms):
        parsers = []
        for name, value in syms:
            parsers.append(lit(name)[const(value)])
        super(sym, self).__init__(*parsers)



def make_attr(value):
    if isinstance(value, attr):
        return value
    elif callable(value):
        return fn(value)
    else:
        return const(value)


class fn(attr):
    def __init__(self, fn):
        self._fn = fn

    def call(self, *args):
        return self._fn(*args)

class binop(attr):

    def __init__(self, op, left, right):
        self._op = op
        self._left = left
        self._right = right

    def call(self, *args):
        left = self._left.call(*args)
        right = self._right.call(*args)
        return self._op(left, right)


class const(attr):

    def __init__(self, val):
        self.val = val

    def call(self, *args):
        return self.val


class subscr(attr):

    def __init__(self, index):
        self._index = index

    def call(self, *args):
        return args[self._index]


class invoke(attr):

    def __init__(self, fn, *params):
        self._fn = make_attr(fn)
        self._params = [make_attr(p) for p in params]

    def call(self, *args):
        fn = self._fn.call(*args)
        params = [p.call(*args) for p in self._params]
        return fn(*params)

class _p:
    def __getitem__(self, index):
        return subscr(index)
p = _p()

def apply(x, op, y=0):
    return op(x, y)

class exp(grammar):

    arith_op  = sym(('+', operator.add),
                    ('-', operator.sub))
    mult_op   = sym(('*', operator.mul),
                    ('/', operator.floordiv))

    arith     = rule()
    mult      = rule()
    value     = rule()
    exp       = rule()
    start     = exp

    mult      <<= ((value & mult_op & exp)       [p[1](p[0], p[2])]
                | value)
    arith     <<= ((mult & arith_op & exp)       [p[1](p[0], p[2])]
                | mult)
    value     <<= dec | '(' & exp & ')'
    exp       <<= arith

double_vision = dec[p[0] * 2]
print (double_vision << '3')

print (exp().parse("(2+3)*100"))
print (exp().parse("4-7"))
print (exp().parse("3+4-7"))
print (exp().parse("2*2*(6+4)*6+3+4-7/8*7*7"))
print (exp().parse("4*(2+5)+9*7+8-8"))
