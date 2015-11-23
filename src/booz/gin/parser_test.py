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

from booz.gin import parser


class ParserTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Parser()
        s = io.StringIO("test")
        s.seek(1)
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(1, s.tell())

    def test_lshift(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        self.assertEqual((p1, p2), (p1 << p2).parsers)

    def test_lshift_seq(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()

        seq = parser.Seq(p2, p3)

        self.assertEqual((p1, p2, p3), (p1 << seq).parsers)


class CharTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Char('abc')
        s = io.StringIO('abcd')
        self.assertEqual((True, 'a'), p.parse(s))
        self.assertEqual((True, 'b'), p.parse(s))
        self.assertEqual((True, 'c'), p.parse(s))
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(3, s.tell())

    def test_parse_default(self):
        p = parser.Char()
        s = io.StringIO('abcd')
        self.assertEqual((True, 'a'), p.parse(s))
        self.assertEqual((True, 'b'), p.parse(s))
        self.assertEqual((True, 'c'), p.parse(s))
        self.assertEqual((True, 'd'), p.parse(s))
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(4, s.tell())

    def test_chars(self):
        self.assertEqual({'a', 'b', 'c'}, parser.Char('abc').chars)
        self.assertEqual(None, parser.Char().chars)


class SeqTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Seq(parser.Char('abc'),
                       parser.Char('def'),
                       parser.Char('ghi'))
        s = io.StringIO('behknq')
        self.assertEqual((True, ('b', 'e', 'h')), p.parse(s))
        self.assertEqual(3, s.tell())

    def test_parse_fail(self):
        p = parser.Seq(parser.Char('abc'),
                       parser.Char('def'),
                       parser.Char('ghi'))
        s = io.StringIO('xyz')
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(0, s.tell())

    def test_parsers(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        seq = parser.Seq(p1, p2)
        self.assertEqual((p1, p2), seq.parsers)

    def test_lshift(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()
        seq = parser.Seq(p1, p2)
        self.assertEqual((p1, p2, p3), (seq << p3).parsers)

    def test_lshift_seq(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()
        p4 = parser.Parser()
        seq1 = parser.Seq(p1, p2)
        seq2 = parser.Seq(p3, p4)

        self.assertEqual((p1, p2, p3, p4), (seq1 << seq2).parsers)


if __name__ == '__main__':
    unittest.main()
