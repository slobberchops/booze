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

import operator

from .. import util


class Action:
    """Base class for defining constructed lambda-like actions.

    Actions are objects that act like a lambda-function through it's invoke() method (not through their call operator).
    This base class has specially overloaded operators to make it easy to build compound Action instances for performing
    calculations on invoke() parameters.

    Example:

        from booze.whiskey import *

        # Calculate what percent p[0] is of p[1].
        percent_of = (p[0] * 100) / p[1]

        assert percent_of.invoke(50, 100) == 50
        assert percent_of.invoke(10, 40) == 25
    """

    def invoke(self, *args, **kwargs):
        """Invoke action.

        Subclass must override.

        Args:
            args: Positional arguments delegated to action implementation.
            kwargs: Keyword arguments delegated to action implementation.
        """
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        """Define a function call action."""
        return Call(self, *args, **kwargs)

    def __pos__(self):
        """Define a + unary operation action."""
        return pos_(self)

    def __neg__(self):
        """Define a - unary operation action."""
        return neg_(self)

    def __invert__(self):
        """Define a ~ unary operation action."""
        return invert_(self)

    # Comparison operators
    def __lt__(self, other):
        """Define a < comparison operation action."""
        return lt_(self, other)

    def __le__(self, other):
        """Define a <= comparison operation action."""
        return le_(self, other)

    def __eq__(self, other):
        """Define a == comparison operation action."""
        return eq_(self, other)

    def __ne__(self, other):
        """Define a != comparison operation action."""
        return ne_(self, other)

    def __ge__(self, other):
        """Define a >= comparison operation action."""
        return ge_(self, other)

    def __gt__(self, other):
        """Define a > comparison operation action."""
        return gt_(self, other)

    # Mathematical operators
    def __add__(self, other):
        """Define a + binary operation action."""
        return add_(self, other)

    def __iadd__(self, other):
        """Define an inverted + binary operation action."""
        return iadd_(self, other)

    def __sub__(self, other):
        """Define a - binary operation action."""
        return sub_(self, other)

    def __isub__(self, other):
        """Define an inverted - binary operation action."""
        return isub_(self, other)

    def __mul__(self, other):
        """Define a * binary operation action."""
        return mul_(self, other)

    def __imul__(self, other):
        """Define an inverted * binary operation action."""
        return imul_(self, other)

    def __floordiv__(self, other):
        """Define a // binary operation action."""
        return floordiv_(self, other)

    def __ifloordiv__(self, other):
        """Define an inverted // binary operation action."""
        return ifloordiv_(self, other)

    def __mod__(self, other):
        """Define a % binary operation action."""
        return mod_(self, other)

    def __imod__(self, other):
        """Define an inverted % binary operation action."""
        return imod_(self, other)

    def __pow__(self, other):
        """Define a ** binary operation action."""
        return pow_(self, other)

    def __ipow__(self, other):
        """Define an inverted ** binary operation action."""
        return ipow_(self, other)

    def __truediv__(self, other):
        """Define a / binary operation action."""
        return truediv_(self, other)

    def __itruediv__(self, other):
        """Define an inverted / binary operation action."""
        return itruediv_(self, other)

    # Bitwise functions
    def __and__(self, other):
        """Define a & binary operation action."""
        return and__(self, other)

    def __iand__(self, other):
        """Define an inverted & binary operation action."""
        return iand_(self, other)

    def __or__(self, other):
        """Define a & binary operation action."""
        return or__(self, other)

    def __ior__(self, other):
        """Define an inverted | binary operation action."""
        return ior_(self, other)

    def __lshift__(self, other):
        """Define a << binary operation action."""
        return lshift_(self, other)

    def __ilshift__(self, other):
        """Define an inverted << binary operation action."""
        return ilshift_(self, other)

    def __rshift__(self, other):
        """Define a >> binary operation action."""
        return rshift_(self, other)

    def __irshift__(self, other):
        """Define an inverted >> binary operation action."""
        return irshift_(self, other)

    def __xor__(self, other):
        """Define a ^ binary operation action."""
        return xor_(self, other)

    def __ixor__(self, other):
        """Define an inverted ^ binary operation action."""
        return ixor_(self, other)


def invoke(value, *args, **kwargs):
    """Get value of invoking against a value with arguments.

    Useful as short hand for condition invocation.  For example:

        if isinstance(value, Action):
            value.invoke(1, 2, 3, a='a', b='b', c='c')

    is the same as:

        invoke(value, 1, 2, 3, a='a', b='b', c='c')

    Args:
        value: Value to be invoked against.  May be Action or non-action.
        args: Index based arguments.
        kwargs: Keyword based arguments.

    Returns:
        Result from invoking value if value is action, else just the value.
    """
    if isinstance(value, Action):
        return value.invoke(*args, **kwargs)
    else:
        return value


class Arg(Action):
    """Action returning the value of a positional.

    Use in conjunction with other actions to return the value of a positional parameter.

    More typically, arguments are accessed via the p singleton.  So:

        Arg(0) is equivalent to p[0]
        Arg(1) is equivalent to p[1]
        Arg(2) is equivalent to p[2]

    Examples:
        from booze.whiskey import *

        assert Arg(0).invoke(10, 'a', ()) == 10
        assert Arg(1).invoke(10, 'a', ()) == 'a'
        assert Arg(2).invoke(10, 'a', ()) == ()
    """

    def __init__(self, index):
        """Constructor.

        Args:
            index: Index of returned parameter.
        """
        self.__index = index

    @property
    def index(self):
        """Index of argument."""
        return self.__index

    def invoke(self, *args, **kwargs):
        """Invoke argument action.

        Args:
            args: Index based arguments.
            kwargs: Ignored.

        Returns:
            The value of the parameter of args at this instances index.
        """
        index = invoke(self.__index, *args, **kwargs)
        try:
            return args[index]
        except IndexError:
            raise TypeError('Positional argument {} out of range'.format(index))


class KwArg(Action):
    """Action returning the value of a named argument.

    Use in conjunction with other actions to return the value of a keyword argument.

    More typically, arguments are accessed via the p singleton.  So:

        KwArg('a') is equivalent to p.a
        KwArg('b') is equivalent to p.b
        KwArg('c') is equivalent to p.c

    Alternatively, but less often:

        KwArg('a') is equivalent to p['a']
        KwArg('b') is equivalent to p['b']
        KwArg('c') is equivalent to p['c']

    Examples:
        from booze.whiskey import *

        assert KwArg('a').invoke(a=10, b='a', c=()) == 10
        assert KwArg('b').invoke(a=10, b='a', c=()) == 'a'
        assert KwArg('c').invoke(a=10, b='a', c=()) == ()
    """

    def __init__(self, name):
        """Constructor.

        Args:
            name: Name of returned parameter.
        """
        self.__name = name

    @property
    def name(self):
        """Name of argument."""
        return self.__name

    def invoke(self, *args, **kwargs):
        """Invoke keyword argument action.

        Args:
            args: Ignored.
            kwargs: Keyword based arguments.

        Returns:
            The value of the parameter of kwargs at this instances name.
        """
        return kwargs[self.__name]


@util.singleton
class p:
    """Syntax sugar argument to make creating argument actions easier.

    Main instance used for generating both positional and named parameter access.  It overloads the getitem and
    getattr operators used for creating index argument actions and keyword argument actions respectively (although
    the getitem form may also be used for creating keyword argument actions.

    Examples:
        from booze.whiskey import *

        assert invoke(p[0], 10, 'a', ()) == 10
        assert invoke(p[1], 10, 'a', ()) == 'a'
        assert invoke(p[2], 10, 'a', ()) == ()
        assert invoke(p.a, a=10, b='a', c=()) == 10
        assert invoke(p.b, a=10, b='a', c=()) == 'a'
        assert invoke(p.c, a=10, b='a', c=()) == ()
    """

    def __getitem__(self, index):
        """Create positional or named argument action.

        Args:
            index: Integer or string representing index of positional parameter or name of keword argument to create
                action for.

        Returns:
            Arg(index) if index is integer else KwArg(index) if index is string.

        Raises:
            TypeError when receives neither string nor integer.
        """
        # TODO: Allow action types.
        if isinstance(index, int):
            return Arg(index)
        elif isinstance(index, str):
            return KwArg(index)
        else:
            raise TypeError('Index must be int or str')

    def __getattr__(self, name):
        """Create named argument action.

        Args:
            name: String representing name of keyword argument to create action for.

        Returns:
            KwArg(name) if index is string.

        Raises:
            Implicitly raises TypeError when receives something other than string via getattr().
        """
        return KwArg(name)


class Call(Action):
    """Action that delegates to calling other actions.

    Used to create actions that are calls to other actions with potentially different parameters than the original
    invocation.

    Examples:
        from booze.whiskey import *
        import operator

        one_func = p[0](1, 1)

        assert invoke(one_func, operator.add) == 2
        assert invoke(one_func, operator.mul) == 1
        assert invoke(one_func, operator.xor) == 0
    """

    def __init__(self, real_func, *args, **kwargs):
        """Constructor.

        real_func: Callable or action.
        args: Positional arguments that are forwarded to real_func upon invocation.  May be constant or action.
        kwargs: Keyword arguments that are forwarded to real_func upon invocation.  May be constant or action.
        """
        self.__func = real_func
        self.__args = args
        self.__kwargs = kwargs

    @property
    def func(self):
        """Original function delegated to by this action."""
        return self.__func

    @property
    def args(self):
        """Positional arguments sent to func upon invocation."""
        return self.__args

    @property
    def kwargs(self):
        """Arguments sent to func upon invocation."""
        return dict(self.__kwargs)

    def invoke(self, *args, **kwargs):
        """Invoke call action.

        Arguments:
            args: Positional arguments used to resolve real values for any action values of self.func, self.args
                or self.kwargs.
            kwargs: Keyword arguments used to resolve real values for any action values of self.func, self.args
                or self.kwargs.

        Returns:
            Result of invoking func with self.args and self.kwargs.
        """
        real_func = invoke(self.__func, *args, **kwargs)
        args = [invoke(a, *args, **kwargs) for a in self.args]
        kwargs = {k: invoke(v, *args, **kwargs) for k, v in self.kwargs.items()}
        return real_func(*args, **kwargs)


def func(real_func):
    """Helper to quickly define an action class around a function.

    Args:
        real_func: Real callable or action.
    """

    class Func(Call):

        __func__ = real_func

        def __init__(self, *args, **kwargs):
            super(Func, self).__init__(real_func, *args, **kwargs)
    return Func


# Unary functions
pos_ = func(operator.pos)
neg_ = func(operator.neg)
invert_ = func(operator.invert)
abs_ = func(operator.abs)

# Comparison functions
lt_ = func(operator.lt)
le_ = func(operator.le)
eq_ = func(operator.eq)
ne_ = func(operator.ne)
ge_ = func(operator.ge)
gt_ = func(operator.gt)

# Mathematical functions
add_ = func(operator.add)
iadd_ = func(operator.iadd)
sub_ = func(operator.sub)
isub_ = func(operator.isub)
mul_ = func(operator.mul)
imul_ = func(operator.imul)
floordiv_ = func(operator.floordiv)
ifloordiv_ = func(operator.ifloordiv)
mod_ = func(operator.mod)
imod_ = func(operator.imod)
pow_ = func(operator.pow)
ipow_ = func(operator.ipow)
truediv_ = func(operator.truediv)
itruediv_ = func(operator.itruediv)

# Bitwise functions
and__ = func(operator.and_)
iand_ = func(operator.iand)
or__ = func(operator.or_)
ior_ = func(operator.ior)
lshift_ = func(operator.lshift)
ilshift_ = func(operator.ilshift)
rshift_ = func(operator.rshift)
irshift_ = func(operator.irshift)
xor_ = func(operator.xor)
ixor_ = func(operator.ixor)
