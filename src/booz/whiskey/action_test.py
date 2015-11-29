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
import unittest

from booz.whiskey import action


class MyFuncAction(action.Action):
    def __init__(self, value):
        self.value = value

    def invoke(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self.value


class MyValueAction(action.Action):
    def __init__(self, value):
        self.value = value

    def invoke(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self.value * 3


class ActionTestCase(unittest.TestCase):

    def setUp(self):
        self.action = action.Action()

    def test_invoke(self):
        with self.assertRaises(NotImplementedError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_call(self):
        c = self.action(1, 2, 3, a='a', b='b', c='c')
        self.assertIsInstance(c, action.Call)
        self.assertEqual(self.action, c.func)
        self.assertEqual((1, 2, 3), c.args)
        self.assertEqual({'a': 'a', 'b':'b', 'c':'c'}, c.kwargs)

    def test_pos(self):
        p = +self.action
        self.assertIsInstance(p, action.pos_)
        self.assertEqual(operator.pos, p.func)

    def test_neg(self):
        p = -self.action
        self.assertIsInstance(p, action.neg_)
        self.assertEqual(operator.neg, p.func)

    def test_invert(self):
        p = ~self.action
        self.assertIsInstance(p, action.invert_)
        self.assertEqual(operator.invert, p.func)


class InvokeTest(unittest.TestCase):

    def test_invoke(self):
        class InvokeMe(action.Action):

            invoked = False
            args = None
            kwargs = None

            def invoke(self, *args, **kwargs):
                self.invoked = True
                self.args = args
                self.kwargs = kwargs

        invoke_me = InvokeMe()
        action.invoke(invoke_me, 1, 2, 3, a='a', b='b', c='c')
        self.assertTrue(invoke_me.invoked)
        self.assertEqual((1, 2, 3), invoke_me.args)
        self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, invoke_me.kwargs)

    def test_invoke_constants(self):
        self.assertEqual('constant', action.invoke('constant', 1, 2, 3, a='a', b='b', c='c'))


class ArgTestCase(unittest.TestCase):

    def test_index(self):
        arg = action.Arg(4)
        self.assertEqual(4, arg.index)

    def test_invoke(self):
        self.assertEqual(1, action.Arg(0).invoke(1, 2, 3, a='a', b='b', c='c'))
        self.assertEqual(2, action.Arg(1).invoke(1, 2, 3, a='a', b='b', c='c'))
        self.assertEqual(3, action.Arg(2).invoke(1, 2, 3, a='a', b='b', c='c'))
        self.assertEqual(3, action.Arg(action.Arg(1)).invoke(1, 2, 3, a='a', b='b', c='c'))

    def test_invoke_out_of_range(self):
        a = action.Arg(1)
        with self.assertRaises(TypeError):
            a.invoke(1)


class KwArgTestCase(unittest.TestCase):

    def test_name(self):
        arg = action.KwArg('a')
        self.assertEqual('a', arg.name)

    def test_invoke(self):
        self.assertEqual('a', action.KwArg('a').invoke(1, 2, 3, a='a', b='b', c='c'))
        self.assertEqual('b', action.KwArg('b').invoke(1, 2, 3, a='a', b='b', c='c'))
        self.assertEqual('c', action.KwArg('c').invoke(1, 2, 3, a='a', b='b', c='c'))

    def test_invoke_out_of_range(self):
        a = action.Arg(1)
        with self.assertRaises(TypeError):
            a.invoke(1)


class PTestCase(unittest.TestCase):

    def test_args(self):
        a1 = action.p[0]
        self.assertIsInstance(a1, action.Arg)
        self.assertEqual(0, a1.index)
        a2 = action.p[1]
        self.assertIsInstance(a2, action.Arg)
        self.assertEqual(1, a2.index)

    def test_kwargs(self):
        a1 = action.p['a']
        self.assertIsInstance(a1, action.KwArg)
        self.assertEqual('a', a1.name)
        a2 = action.p['b']
        self.assertIsInstance(a2, action.KwArg)
        self.assertEqual('b', a2.name)

    def test_unexpected(self):
        with self.assertRaises(TypeError):
            action.p[object()]

    def test_get_attr(self):
        a1 = action.p.a
        self.assertIsInstance(a1, action.KwArg)
        self.assertEqual('a', a1.name)
        a2 = action.p.b
        self.assertIsInstance(a2, action.KwArg)
        self.assertEqual('b', a2.name)


class CallTestCase(unittest.TestCase):

    def test_func(self):
        f = lambda: None
        self.assertEqual(f, action.Call(f).func)

    def test_args(self):
        self.assertEqual((1, 2, 3), action.Call(None, 1, 2, 3).args)

    def test_kwargs(self):
        self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, action.Call(None, a='a', b='b', c='c').kwargs)

    def test_kwargs_copied(self):
        call = action.Call(None, a='a', b='b', c='c')
        call.kwargs['a'] = 'aa'
        self.assertEqual('a', call.kwargs['a'])

    def test_invoke_constants(self):
        f = lambda p, *, a: (p, a)
        call = action.Call(f, 1, a='a')
        self.assertEqual((1, 'a'), call.invoke(10, a='aa'))

    def test_invoke_actions(self):
        def func(*args, **kwargs):
            return tuple(v + v for v in args) + ({k: v + v for k, v in kwargs.items()},)

        f = MyFuncAction(func)
        p = MyValueAction(1)
        a = MyValueAction('a')

        call = action.Call(f, p, a=a)
        self.assertEqual((6, {'a': 'aaaaaa'}), call.invoke(10, a='aa'))


class FuncTestCase(unittest.TestCase):

    def setUp(self):
        self.f = lambda: None
        self.f_action = action.func(self.f)

    def test_func(self):
        self.assertTrue(issubclass(self.f_action, action.Call))
        self.assertEqual(self.f, self.f_action.__func__)
        c = self.f_action(1, 2, 3, a='a', b='b', c='c')
        self.assertEqual(self.f, c.func)
        self.assertEqual((1, 2, 3), c.args)
        self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, c.kwargs)

    def test_call(self):
        def func(*args, **kwargs):
            return tuple(v + v for v in args) + ({k: v + v for k, v in kwargs.items()},)

        f = MyFuncAction(func)
        p = MyValueAction(1)
        a = MyValueAction('a')

        call = action.Call(f, p, a=a)
        self.assertEqual((6, {'a': 'aaaaaa'}), call.invoke(10, a='aa'))


class UnaryOperatorsTestCase(unittest.TestCase):

    def test_pos(self):
        self.assertTrue(issubclass(action.pos_, action.Call))
        c = action.pos_(action.p[0])
        self.assertEqual(operator.pos, c.func)
        self.assertEqual(-1, c.invoke(-1))

    def test_neg(self):
        self.assertTrue(issubclass(action.pos_, action.Call))
        c = action.neg_(action.p[0])
        self.assertEqual(operator.neg, c.func)
        self.assertEqual(1, c.invoke(-1))

    def test_invert(self):
        self.assertTrue(issubclass(action.pos_, action.Call))
        c = action.invert_(action.p[0])
        self.assertEqual(operator.invert, c.func)
        self.assertEqual(0, c.invoke(-1))


if __name__ == '__main__':
    unittest.main()
