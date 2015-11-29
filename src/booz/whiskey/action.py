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

    def invoke(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return Call(self, *args, **kwargs)

    def __pos__(self):
        return pos_(self)

    def __neg__(self):
        return neg_(self)

    def __invert__(self):
        return invert_(self)

    def __lt__(self, other):
        return lt_(self, other)

    def __le__(self, other):
        return le_(self, other)

    def __eq__(self, other):
        return eq_(self, other)

    def __ne__(self, other):
        return ne_(self, other)

    def __ge__(self, other):
        return ge_(self, other)

    def __gt__(self, other):
        return gt_(self, other)


def invoke(value, *args, **kwargs):
    if isinstance(value, Action):
        return value.invoke(*args, **kwargs)
    else:
        return value


class Arg(Action):

    def __init__(self, index):
        self.__index = index

    @property
    def index(self):
        return self.__index

    def invoke(self, *args, **kwargs):
        index = invoke(self.__index, *args, **kwargs)
        try:
            return args[index]
        except IndexError:
            raise TypeError('Positional argument {} out of range'.format(index))


class KwArg(Action):

    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def invoke(self, *args, **kwargs):
        return kwargs[self.__name]


@util.singleton
class p:

    def __getitem__(self, index):
        if isinstance(index, int):
            return Arg(index)
        elif isinstance(index, str):
            return KwArg(index)
        else:
            raise TypeError('Index must be int or str')

    def __getattr__(self, name):
        return KwArg(name)


class Call(Action):

    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    @property
    def func(self):
        return self.__func

    @property
    def args(self):
        return self.__args

    @property
    def kwargs(self):
        return dict(self.__kwargs)

    def invoke(self, *args, **kwargs):
        func = invoke(self.__func, *args, **kwargs)
        args = [invoke(a, *args, **kwargs) for a in self.args]
        kwargs = {k: invoke(v, *args, **kwargs) for k, v in self.kwargs.items()}
        return func(*args, **kwargs)


def func(func):
    class Func(Call):

        __func__ = func

        def __init__(self, *args, **kwargs):
            super(Func, self).__init__(func, *args, **kwargs)
    return Func


# Unary functions
pos_ = func(operator.pos)
neg_ = func(operator.neg)
invert_ = func(operator.invert)

# Comparison functions
lt_ = func(operator.lt)
le_ = func(operator.le)
eq_ = func(operator.eq)
ne_ = func(operator.ne)
ge_ = func(operator.ge)
gt_ = func(operator.gt)
