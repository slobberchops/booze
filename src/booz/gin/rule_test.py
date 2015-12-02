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


class RuleTestCase(unittest.TestCase):

    def test_default_state(self):
        r = booz.gin.rule.Rule()
        with self.assertRaises(AttributeError):
            r.parse('')

    def test_parse(self):
        r = booz.gin.rule.Rule()
        r %= 'hello'
        self.assertEqual((True, parser.UNUSED), r.parse('hello'))

    def test_set_parser(self):
        p = parser.Parser()
        r = booz.gin.rule.Rule()
        r.parser = p
        self.assertEqual(p, r.parser)

    def test_set_bad_parser(self):
        r = booz.gin.rule.Rule()
        with self.assertRaises(TypeError):
            r.parser = object()

    def test_uninitialized_attr_type(self):
        with self.assertRaises(NotImplementedError):
            booz.gin.rule.Rule().attr_type

    def test_initialized_attr_type(self):
        r = booz.gin.rule.Rule()
        r %= parser.Char('a')
        self.assertEqual(parser.AttrType.STRING, r.attr_type)
        r %= parser.lit('a')
        self.assertEqual(parser.AttrType.UNUSED, r.attr_type)

    def test_expected_attr_type(self):
        r = booz.gin.rule.Rule(parser.AttrType.STRING)
        self.assertEqual(parser.AttrType.STRING, r.attr_type)

    def test_assign_to_expected_attr(self):
        r = booz.gin.rule.Rule(parser.AttrType.STRING)
        r %= parser.Char('a')
        self.assertEqual(parser.AttrType.STRING, r.attr_type)

    def test_illegal_assign_to_expected_attr(self):
        r = booz.gin.rule.Rule(parser.AttrType.STRING)
        p = parser.lit('a')
        with self.assertRaises(ValueError):
            r %= p

if __name__ == '__main__':
    unittest.main()
