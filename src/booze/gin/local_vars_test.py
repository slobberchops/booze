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

import unittest

from booze import whiskey
from booze.gin import local_vars
from booze.whiskey import action


class MyNameAction(action.Action):

    def invoke(self, *args, **kwargs):
        return 'my_name'


class MyValueAction(action.Action):

    def invoke(self, *args, **kwargs):
        return 10


class GetVarAttrTestCase(unittest.TestCase):

    action = local_vars.GetVarAttr('my_name')

    def test_name(self):
        self.assertEqual('my_name', self.action.name)

    def test_invoke_with_no_locals(self):
        with self.assertRaises(TypeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_invoke_not_found(self):
        with self.assertRaises(AttributeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c', vars=object())

    def test_invoke(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        locals_instance.my_name = 10
        self.assertEqual(10, self.action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))

    def test_invoke_name_action(self):
        name_action = MyNameAction()
        test_action = local_vars.GetVarAttr(name_action)
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        locals_instance.my_name = 10
        self.assertEqual(10, test_action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))


class SetVarAttrTestCase(unittest.TestCase):

    action = local_vars.SetVarAttr('my_name', 10)

    def test_name(self):
        self.assertEqual('my_name', self.action.name)

    def test_value(self):
        self.assertEqual(10, self.action.value)

    def test_invoke_with_no_locals(self):
        with self.assertRaises(TypeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_invoke_not_found(self):
        with self.assertRaises(AttributeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c', vars=object())

    def test_invoke(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        self.assertEqual(10, self.action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))
        self.assertEqual(10, locals_instance.my_name)

    def test_invoke_name_action(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()

        test_action = local_vars.SetVarAttr(whiskey.p[0], 10)
        self.assertEqual(10, test_action.invoke('one', 2, 3, a='a', b='b', c='c', vars=locals_instance))
        self.assertEqual(10, locals_instance.one)

        test_action = local_vars.SetVarAttr(whiskey.p.a, 20)
        self.assertEqual(20, test_action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))
        self.assertEqual(20, locals_instance.a)

    def test_invoke_value_action(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()

        test_action = local_vars.SetVarAttr('my_name', whiskey.p[0])
        self.assertEqual(1, test_action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))
        self.assertEqual(1, locals_instance.my_name)

        test_action = local_vars.SetVarAttr('my_name', whiskey.p.a)
        self.assertEqual('a', test_action.invoke(1, 2, 3, a='a', b='b', c='c', vars=locals_instance))
        self.assertEqual('a', locals_instance.my_name)


class LTestCase(unittest.TestCase):

    def test_get_attr(self):
        action = local_vars.l.my_name
        self.assertIsInstance(action, local_vars.GetVarAttr)
        self.assertEqual('my_name', action.name)

    def test_set_attr(self):
        action = local_vars.l.my_name[10]
        self.assertIsInstance(action, local_vars.SetVarAttr)
        self.assertEqual('my_name', action.name)
        self.assertEqual(10, action.value)


class VarsTestCase(unittest.TestCase):

    def test_init(self):
        vars = local_vars.Vars(a='a', b='b', c='c')
        self.assertEqual('a', vars.a)
        self.assertEqual('b', vars.b)
        self.assertEqual('c', vars.c)

    def test_init_invalid(self):
        with self.assertRaises(ValueError):
            local_vars.Vars(_a='a')

    def test_setattr(self):
        vars = local_vars.Vars()
        vars.a = 'a'
        vars.b = 'b'
        vars.c = 'c'
        self.assertEqual('a', vars.a)
        self.assertEqual('b', vars.b)
        self.assertEqual('c', vars.c)

    def test_setattr_invalid(self):
        vars = local_vars.Vars()
        with self.assertRaises(ValueError):
            vars._a = 'a'

    def test_dir(self):
        self.assertListEqual(['a', 'b', 'c'], dir(local_vars.Vars(a='a', b='b', c='c')))

    def test_iter(self):
        self.assertListEqual([('a', 1), ('b', 2), ('c', 3)], list(local_vars.Vars(a=1, b=2, c=3)))

    def test_eq(self):
        self.assertEqual(local_vars.Vars(), local_vars.Vars())
        self.assertEqual(local_vars.Vars(a='a', b='b', c='c'), local_vars.Vars(a='a', b='b', c='c'))
        self.assertNotEqual(local_vars.Vars(a='a', b='b', c='c'), local_vars.Vars(a=1, b='b', c='c'))
        self.assertNotEqual({'a': 'a', 'b': 'b', 'c': 'c'}, local_vars.Vars(a='a', b='b', c='c'))

    def test_str(self):
        self.assertEqual('<Vars>', str(local_vars.Vars()))
        self.assertEqual('<Vars a, b, c>', str(local_vars.Vars(a='a', b='b', c='c')))

    def test_repr(self):
        self.assertEqual('<Vars>', repr(local_vars.Vars()))
        self.assertEqual('<Vars a, b, c>', repr(local_vars.Vars(a='a', b='b', c='c')))


class LocalScopeTest(unittest.TestCase):

    def test_args(self):
        scope = local_vars.LocalScope(1, 2, 3)
        self.assertSequenceEqual((1, 2, 3), scope.args)

    def test_kwargs(self):
        scope = local_vars.LocalScope(a='a', b='b', c='c')
        self.assertDictEqual({'a': 'a', 'b': 'b', 'c': 'c'}, scope.kwargs)

    def test_kwargs_immutable(self):
        scope = local_vars.LocalScope(a='a', b='b', c='c')
        scope.kwargs['a'] = 'aa'
        self.assertDictEqual({'a': 'a', 'b': 'b', 'c': 'c'}, scope.kwargs)

    def test_vars(self):
        scope = local_vars.LocalScope()
        self.assertIsInstance(scope.vars, local_vars.Vars)


if __name__ == '__main__':
    unittest.main()
