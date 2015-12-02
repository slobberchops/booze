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
        self.action1 = action.Action()
        self.action2 = action.Action()

    def test_invoke(self):
        with self.assertRaises(NotImplementedError):
            self.action1.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_call(self):
        c = self.action1(1, 2, 3, a='a', b='b', c='c')
        self.assertIsInstance(c, action.Call)
        self.assertIs(self.action1, c.func)
        self.assertEqual((1, 2, 3), c.args)
        self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, c.kwargs)

    def do_unary_test(self, action_impl, operator_func):
        instance = operator_func(self.action1)
        self.assertTrue(isinstance(instance, action_impl))
        self.assertEqual(1, len(instance.args))
        self.assertIs(self.action1, instance.args[0])

    def do_binop_test(self, action_impl, operator_func):
        instance = operator_func(self.action1, self.action2)
        self.assertTrue(isinstance(instance, action_impl))
        self.assertEqual(2, len(instance.args))
        self.assertIs(self.action1, instance.args[0])
        self.assertIs(self.action2, instance.args[1])

    def test_unary(self):
        self.do_unary_test(action.pos_, operator.pos)
        self.do_unary_test(action.neg_, operator.neg)
        self.do_unary_test(action.invert_, operator.invert)

    def test_comparison(self):
        self.do_binop_test(action.lt_, operator.lt)
        self.do_binop_test(action.le_, operator.le)
        self.do_binop_test(action.eq_, operator.eq)
        self.do_binop_test(action.ne_, operator.ne)
        self.do_binop_test(action.ge_, operator.ge)
        self.do_binop_test(action.gt_, operator.gt)

    def test_mathmatical(self):
        self.do_binop_test(action.add_, operator.add)
        self.do_binop_test(action.iadd_, operator.iadd)
        self.do_binop_test(action.sub_, operator.sub)
        self.do_binop_test(action.isub_, operator.isub)
        self.do_binop_test(action.mul_, operator.mul)
        self.do_binop_test(action.imul_, operator.imul)
        self.do_binop_test(action.floordiv_, operator.floordiv)
        self.do_binop_test(action.ifloordiv_, operator.ifloordiv)
        self.do_binop_test(action.mod_, operator.mod)
        self.do_binop_test(action.imod_, operator.imod)
        self.do_binop_test(action.pow_, operator.pow)
        self.do_binop_test(action.ipow_, operator.ipow)
        self.do_binop_test(action.truediv_, operator.truediv)
        self.do_binop_test(action.itruediv_, operator.itruediv)

    def test_logical(self):
        self.do_binop_test(action.and__, operator.and_)
        self.do_binop_test(action.iand_, operator.iand)
        self.do_binop_test(action.or__, operator.or_)
        self.do_binop_test(action.ior_, operator.ior)
        self.do_binop_test(action.lshift_, operator.lshift)
        self.do_binop_test(action.ilshift_, operator.ilshift)
        self.do_binop_test(action.rshift_, operator.rshift)
        self.do_binop_test(action.irshift_, operator.irshift)
        self.do_binop_test(action.xor_, operator.xor)
        self.do_binop_test(action.ixor_, operator.ixor)


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
        def f(): return None
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
        def f(p, a): return p, a
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

    def do_operator_test(self, action_impl, operator_func, value, result):
        self.assertTrue(issubclass(action_impl, action.Call))
        c = action_impl(action.p[0])
        self.assertEqual(operator_func, c.func)
        self.assertEqual(result, c.invoke(value))

    def test_operators(self):
        self.do_operator_test(action.pos_, operator.pos, -1, -1)
        self.do_operator_test(action.neg_, operator.neg, -1, 1)
        self.do_operator_test(action.invert_, operator.invert, -1, 0)


class BinaryOperatorsTestCase(unittest.TestCase):

    def do_operator_test(self, action_impl, operator_func, lvalue, rvalue, result):
        self.assertTrue(issubclass(action_impl, action.Call))
        c = action_impl(action.p[0], action.p[1])
        self.assertEqual(operator_func, c.func)
        self.assertEqual(result, c.invoke(lvalue, rvalue))

    def test_comparison(self):
        self.do_operator_test(action.lt_, operator.lt, 10, 20, True)
        self.do_operator_test(action.lt_, operator.lt, 20, 10, False)
        self.do_operator_test(action.lt_, operator.lt, 10, 10, False)

        self.do_operator_test(action.le_, operator.le, 10, 20, True)
        self.do_operator_test(action.le_, operator.le, 20, 10, False)
        self.do_operator_test(action.le_, operator.le, 10, 10, True)

        self.do_operator_test(action.eq_, operator.eq, 10, 10, True)
        self.do_operator_test(action.eq_, operator.eq, 20, 10, False)

        self.do_operator_test(action.ne_, operator.ne, 20, 10, True)
        self.do_operator_test(action.ne_, operator.ne, 10, 10, False)

        self.do_operator_test(action.ge_, operator.ge, 10, 20, False)
        self.do_operator_test(action.ge_, operator.ge, 20, 10, True)
        self.do_operator_test(action.ge_, operator.ge, 10, 10, True)

        self.do_operator_test(action.gt_, operator.gt, 10, 20, False)
        self.do_operator_test(action.gt_, operator.gt, 20, 10, True)
        self.do_operator_test(action.gt_, operator.gt, 10, 10, False)

    def test_mathematical(self):
        self.do_operator_test(action.add_, operator.add, 10, 20, 30)
        self.do_operator_test(action.iadd_, operator.iadd, 10, 20, 30)

        self.do_operator_test(action.sub_, operator.sub, 10, 20, -10)
        self.do_operator_test(action.isub_, operator.isub, 10, 20, -10)

        self.do_operator_test(action.mul_, operator.mul, 10, 20, 200)
        self.do_operator_test(action.imul_, operator.imul, 10, 20, 200)

        self.do_operator_test(action.floordiv_, operator.floordiv, 100, 33, 3)
        self.do_operator_test(action.ifloordiv_, operator.ifloordiv, 100, 33, 3)

        self.do_operator_test(action.mod_, operator.mod, 33, 10, 3)
        self.do_operator_test(action.imod_, operator.imod, 33, 10, 3)

        self.do_operator_test(action.pow_, operator.pow, 10, 3, 1000)
        self.do_operator_test(action.ipow_, operator.ipow, 10, 3, 1000)

        self.do_operator_test(action.truediv_, operator.truediv, 1, 2, 0.5)
        self.do_operator_test(action.itruediv_, operator.itruediv, 1, 2, 0.5)

    def test_logical(self):
        self.do_operator_test(action.and__, operator.and_, 3, 1, 1)
        self.do_operator_test(action.iand_, operator.iand, 3, 1, 1)

        self.do_operator_test(action.or__, operator.or_, 4, 1, 5)
        self.do_operator_test(action.ior_, operator.ior, 4, 1, 5)

        self.do_operator_test(action.lshift_, operator.lshift, 15, 2, 60)
        self.do_operator_test(action.ilshift_, operator.ilshift, 15, 2, 60)

        self.do_operator_test(action.rshift_, operator.rshift, 15, 2, 3)
        self.do_operator_test(action.irshift_, operator.irshift, 15, 2, 3)

        self.do_operator_test(action.xor_, operator.xor, 3, 7, 4)
        self.do_operator_test(action.ixor_, operator.ixor, 3, 7, 4)


if __name__ == '__main__':
    unittest.main()
