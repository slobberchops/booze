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

from booz.gin import local_vars
from booz.whiskey import action


class MyNameAction(action.Action):

    def invoke(self, *args, **kwargs):
        return 'my_name'


class MyValueAction(action.Action):

    def invoke(self, *args, **kwargs):
        return 10


class GetAttrTestCase(unittest.TestCase):

    action = local_vars.GetAttr('my_name')

    def test_name(self):
        self.assertEqual('my_name', self.action.name)

    def test_invoke_with_no_locals(self):
        with self.assertRaises(TypeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_invoke_not_found(self):
        with self.assertRaises(AttributeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c', locals=object())

    def test_invoke(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        locals_instance.my_name = 10
        self.assertEqual(10, self.action.invoke(1, 2, 3, a='a', b='b', c='c', locals=locals_instance))

    def test_invoke_name_action(self):
        name_action = MyNameAction()
        test_action = local_vars.GetAttr(name_action)
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        locals_instance.my_name = 10
        self.assertEqual(10, test_action.invoke(1, 2, 3, a='a', b='b', c='c', locals=locals_instance))


class SetAttrTestCase(unittest.TestCase):

    action = local_vars.SetAttr('my_name', 10)

    def test_name(self):
        self.assertEqual('my_name', self.action.name)

    def test_value(self):
        self.assertEqual(10, self.action.value)

    def test_invoke_with_no_locals(self):
        with self.assertRaises(TypeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c')

    def test_invoke_not_found(self):
        with self.assertRaises(AttributeError):
            self.action.invoke(1, 2, 3, a='a', b='b', c='c', locals=object())

    def test_invoke(self):
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        self.assertEqual(10, self.action.invoke(1, 2, 3, a='a', b='b', c='c', locals=locals_instance))
        self.assertEqual(10, locals_instance.my_name)

    def test_invoke_name_and_value_action(self):
        name_action = MyNameAction()
        value_action = MyValueAction()
        test_action = local_vars.SetAttr(name_action, value_action)
        class SimpleLocals:
            pass
        locals_instance = SimpleLocals()
        self.assertEqual(10, test_action.invoke(1, 2, 3, a='a', b='b', c='c', locals=locals_instance))
        self.assertEqual(10, locals_instance.my_name)


class LTestCase(unittest.TestCase):

    def test_get_attr(self):
        action = local_vars.l.my_name
        self.assertIsInstance(action, local_vars.GetAttr)
        self.assertEqual('my_name', action.name)

    def test_set_attr(self):
        action = local_vars.l.my_name[10]
        self.assertIsInstance(action, local_vars.SetAttr)
        self.assertEqual('my_name', action.name)
        self.assertEqual(10, action.value)


class ScopeTest(unittest.TestCase):

    def test_iter_empty(self):
        self.assertEqual((), tuple(iter(local_vars.LocalScope())))

    def test_iter_values(self):
        scope = local_vars.LocalScope()
        scope.a = 10
        scope.b = 20
        self.assertSequenceEqual((('a', 10), ('b', 20)), tuple(iter(scope)))


if __name__ == '__main__':
    unittest.main()
