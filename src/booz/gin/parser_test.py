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


class UnusedTestCase(unittest.TestCase):

    def test_repr(self):
        self.assertEqual('UNUSED', repr(parser.UNUSED))


class TupleToAttributres(unittest.TestCase):

    def test_empty_tuple(self):
        self.assertEqual(parser.UNUSED, parser.tuple_to_attributes(()))

    def test_unused_values(self):
        self.assertEqual(parser.UNUSED, parser.tuple_to_attributes((parser.UNUSED, parser.UNUSED)))

    def test_strip_unused(self):
        self.assertEqual('ok', parser.tuple_to_attributes((parser.UNUSED, 'ok', parser.UNUSED)))


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

    def test_or(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        self.assertEqual((p1, p2), (p1 | p2).parsers)

    def test_or_alt(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()

        alt = parser.Alt(p2, p3)

        self.assertEqual((p1, p2, p3), (p1 | alt).parsers)

    def test_getitem(self):
        func = lambda v: v + v
        p1 = parser.Parser()
        p2 = p1[func]
        self.assertEqual(p1, p2.parser)
        self.assertEqual(func, p2.func)

    def test_neg(self):
        p1 = parser.Parser()
        p2 = -p1
        self.assertEqual(p1, p2.parser)

    def test_pos(self):
        p1 = parser.Parser()
        p2 = +p1
        self.assertEqual(p1, p2.parser)
        self.assertEqual(1, p2.minimum)
        self.assertIsNone(p2.maximum)


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

    def test_neg(self):
        p1 = parser.Parser()
        p2 = -p1
        self.assertEqual(p1, p2.parser)
        self.assertEqual(0, p2.minimum)
        self.assertEqual(1, p2.maximum)


class AltTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Alt(parser.Char('abc'),
                       parser.Char('def'),
                       parser.Char('ghi'))
        s = io.StringIO('en')
        self.assertEqual((True, 'e'), p.parse(s))
        self.assertEqual(1, s.tell())

    def test_parse_fail(self):
        p = parser.Alt(parser.Char('abc'),
                       parser.Char('def'),
                       parser.Char('ghi'))
        s = io.StringIO('x')
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(0, s.tell())

    def test_parsers(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        alt = parser.Alt(p1, p2)
        self.assertEqual((p1, p2), alt.parsers)

    def test_or(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()
        alt = parser.Alt(p1, p2)
        self.assertEqual((p1, p2, p3), (alt | p3).parsers)

    def test_or_alt(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()
        p4 = parser.Parser()
        alt1 = parser.Alt(p1, p2)
        alt2 = parser.Alt(p3, p4)

        self.assertEqual((p1, p2, p3, p4), (alt1 | alt2).parsers)


class ActionTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Action(parser.Char('abc'), lambda v: v + v)
        s = io.StringIO('b')
        self.assertEqual((True, 'bb'), p.parse(s))
        self.assertEqual(1, s.tell())

    def test_parse_fail(self):
        p = parser.Action(parser.Char('abc'), lambda v: v + v)
        s = io.StringIO('x')
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(0, s.tell())

    def test_parser(self):
        p1 = parser.Char('abc')
        p2 = parser.Action(p1, lambda v: v + v)
        self.assertEqual(p1, p2.parser)

    def test_func(self):
        f = lambda v: v + v
        p2 = parser.Action(parser.Char('abc'), f)
        self.assertEqual(f, p2.func)


class RepeatUnitTest(unittest.TestCase):

    def test_parse_zero_or_more(self):
        p = parser.Repeat()[parser.Char('abc')]
        s = io.StringIO('abcabcdef')
        self.assertEqual((True, tuple('abcabc')), p.parse(s))
        self.assertEqual(6, s.tell())
        self.assertEqual((True, parser.UNUSED), p.parse(s))
        self.assertEqual(6, s.tell())

    def test_parse_minimum(self):
        p = parser.Repeat(2)[parser.Char('abc')]
        s = io.StringIO('abcdef')
        self.assertEqual((True, tuple('abc')), p.parse(s))
        self.assertEqual(3, s.tell())
        s.seek(2)
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(2, s.tell())

    def test_parse_maximum(self):
        p = parser.Repeat(0, 2)[parser.Char('abc')]
        s = io.StringIO('abcdef')
        self.assertEqual((True, tuple('ab')), p.parse(s))
        self.assertEqual(2, s.tell())

    def test_parser(self):
        p1 = parser.Parser()
        p2 = parser.Repeat()[p1]
        self.assertEqual(p1, p2.parser)

    def test_minimum(self):
        p = parser.Repeat(10, 20)[parser.Parser()]
        self.assertEqual(20, p.minimum)

    def test_maximum_default(self):
        p = parser.Repeat(10)[parser.Parser()]
        self.assertIsNone(p.maximum)

    def test_minimum(self):
        p = parser.Repeat(10, 20)[parser.Parser()]
        self.assertEqual(10, p.minimum)

    def test_kleene_optimization(self):
        p1 = parser.Parser()
        p2 = -+p1
        self.assertEqual(p1, p2.parser)
        self.assertEqual(0, p2.minimum)
        self.assertIsNone(p2.maximum)

    def test_kleene_optimization_with_maximum(self):
        p1 = parser.Parser()
        p2 = -parser.Repeat(1, 20)[p1]
        self.assertEqual(p1, p2.parser)
        self.assertEqual(0, p2.minimum)
        self.assertEqual(20, p2.maximum)

    def test_skip_kleene_optimization(self):
        p1 = parser.Parser()
        p2 = parser.Repeat(2)[p1]
        p3 = -p2
        self.assertEqual(p2, p3.parser)
        self.assertEqual(0, p3.minimum)
        self.assertEqual(1, p3.maximum)
        self.assertTrue(isinstance(p3, parser.Repeat.__parser_type__))


if __name__ == '__main__':
    unittest.main()
