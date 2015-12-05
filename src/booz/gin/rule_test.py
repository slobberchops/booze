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

import booz.gin
from booz.gin import parser
from booz.gin import rule


class RuleTestCase(unittest.TestCase):

    def test_default_state(self):
        r = rule.Rule()
        with self.assertRaises(AttributeError):
            r.parse('')

    def test_parse(self):
        r = rule.Rule()
        r %= 'hello'
        self.assertEqual((True, parser.UNUSED), r.parse('hello'))

    def test_set_parser(self):
        p = parser.Parser()
        r = rule.Rule()
        r.parser = p
        self.assertEqual(p, r.parser)

    def test_set_bad_parser(self):
        r = rule.Rule()
        with self.assertRaises(TypeError):
            r.parser = object()

    def test_uninitialized_attr_type(self):
        with self.assertRaises(NotImplementedError):
            rule.Rule().attr_type

    def test_initialized_attr_type(self):
        r = rule.Rule()
        r %= parser.Char('a')
        self.assertEqual(parser.AttrType.STRING, r.attr_type)
        r %= parser.lit('a')
        self.assertEqual(parser.AttrType.UNUSED, r.attr_type)

    def test_expected_attr_type(self):
        r = rule.Rule(parser.AttrType.STRING)
        self.assertEqual(parser.AttrType.STRING, r.attr_type)

    def test_assign_to_expected_attr(self):
        r = rule.Rule(parser.AttrType.STRING)
        r %= parser.Char('a')
        self.assertEqual(parser.AttrType.STRING, r.attr_type)

    def test_illegal_assign_to_expected_attr(self):
        r = rule.Rule(parser.AttrType.STRING)
        p = parser.lit('a')
        with self.assertRaises(ValueError):
            r %= p

    def test_call(self):
        rule_call = rule.Rule()(1, 2, 3, a='a', b='b', c='c')
        self.assertIsInstance(rule_call, rule.RuleCall)
        self.assertSequenceEqual((1, 2, 3), rule_call.args)
        self.assertDictEqual({'a': 'a', 'b': 'b', 'c': 'c'}, rule_call.kwargs)


class RuleCallTestCase(unittest.TestCase):

    def setUp(self):
        self.rule = rule.Rule()
        self.rule_call = self.rule(1, 2, 3, a='a', b='b', c='c')

    def test_parse(self):
        parser_state = parser.ParserState('a')

        def check_state(chr):
            self.assertEqual((1, 2, 3), parser_state.scope.args)
            self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, parser_state.scope.kwargs)
            return 'called - ' + chr

        self.rule %= parser.Char('a')[check_state]
        self.assertEqual((True, 'called - a'), self.rule_call.parse(parser_state))

    def test_wrong_rule_type(self):
        with self.assertRaisesRegex(TypeError, 'Expected rule to be type Rule, was Char'):
            rule.RuleCall(parser.Char('a'))

    def test_args(self):
        self.assertSequenceEqual((1, 2, 3), self.rule_call.args)

    def test_kwargs(self):
        self.assertSequenceEqual({'a': 'a', 'b': 'b', 'c': 'c'}, self.rule_call.kwargs)

    def test_kwargs_immutable(self):
        self.rule_call.kwargs['a'] = 'd'
        self.assertSequenceEqual({'a': 'a', 'b': 'b', 'c': 'c'}, self.rule_call.kwargs)

if __name__ == '__main__':
    unittest.main()
