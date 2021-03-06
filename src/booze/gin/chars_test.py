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

import io
import unittest

from booze.gin import chars
from booze.gin import parser


class PredicateCharTestCase(unittest.TestCase):

    def setUp(self):
        self.predicate = lambda c: ord(c) % 2
        self.parser = chars.PredicateChar(self.predicate)

    def test_parse(self):
        s = io.StringIO('a')
        self.assertEqual((True, 'a'), self.parser.parse(s))
        self.assertEqual(1, s.tell())

    def test_parse_fail(self):
        s = io.StringIO('b')
        self.assertEqual((False, None), self.parser.parse(s))
        self.assertEqual(0, s.tell())

    def test_attr_type(self):
        self.assertEqual(parser.AttrType.STRING, self.parser.attr_type)

    def test_predicate(self):
        self.assertEqual(self.predicate, self.parser.predicate)


class CharClassTestCase(unittest.TestCase):

    def do_test(self, test_parser, good, bad):
        for c in good:
            s = c + c
            self.assertEqual((True, c), test_parser.parse(s))

        for c in bad:
            s = c + c
            self.assertEqual((False, None), test_parser.parse(s))

    def test_alnum(self):
        self.do_test(chars.alnum, 'aA0', '_->')

    def test_alpha(self):
        self.do_test(chars.alpha, 'aA', '0_->')

    def test_blank(self):
        self.do_test(chars.blank, ' \t', 'a0\n>')

    def test_digit(self):
        self.do_test(chars.digit, '098', 'abc')

    def test_lower(self):
        self.do_test(chars.lower, 'abc', 'ABC123')

    def test_printable(self):
        self.do_test(chars.printable, 'abc098=->', '\0\a')
        self.do_test(chars.print_, 'abc098=->', '\0\a')

    def test_space(self):
        self.do_test(chars.space, ' \t\n\r', 'a0+_')

    def test_upper(self):
        self.do_test(chars.upper, 'ABC', 'abc123')

    def test_xdigit(self):
        self.do_test(chars.xdigit, '123abcABC', 'xyz')


if __name__ == '__main__':
    unittest.main()
