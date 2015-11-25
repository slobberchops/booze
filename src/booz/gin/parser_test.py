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

import contextlib
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


class AsParserTestCase(unittest.TestCase):

    def test_parser(self):
        p = parser.as_parser(parser.Char('a'))
        s = io.StringIO('a')
        self.assertEqual((True, 'a'), p.parse(s))

    def test_string(self):
        p = parser.as_parser('parser')
        s = io.StringIO('parser')
        self.assertEqual((True, parser.UNUSED), p.parse(s))

    def test_non_parser(self):
        with self.assertRaises(TypeError):
            parser.as_parser(object())


class ParserStateTestCase(unittest.TestCase):

    def setUp(self):
        self.input = io.StringIO('abc')
        self.state = parser.ParserState(self.input)

    def test_initial_state(self):
        with self.assertRaises(IndexError):
            self.state.committed
        with self.assertRaises(IndexError):
            self.state.successful
        with self.assertRaises(IndexError):
            self.state.value

    def test_string_in_constructor(self):
        self.state = parser.ParserState('input')
        self.assertEqual('input', self.state.read())

    def test_read_and_rollback(self):
        with self.state:
            self.assertEqual('a', self.state.read(1))
            self.assertEqual(1, self.input.tell())
            self.assertEqual('b', self.state.read(1))
            self.assertEqual('c', self.state.read(1))
            self.assertEqual(3, self.input.tell())
            self.assertEqual('', self.state.read(1))
            self.assertFalse(self.state.committed)
            self.assertFalse(self.state.successful)
        self.assertEqual(0, self.input.tell())

    def test_read_and_commit(self):
        with self.state:
            self.assertEqual('a', self.state.read(1))
            self.assertEqual(1, self.input.tell())
            self.assertEqual('b', self.state.read(1))
            self.assertEqual('c', self.state.read(1))
            self.assertEqual(3, self.input.tell())
            self.assertEqual('', self.state.read(1))
            self.assertFalse(self.state.committed)
            self.assertFalse(self.state.successful)
            self.state.commit('a value')
            self.assertTrue(self.state.committed)
            self.assertTrue(self.state.successful)
        self.assertEqual(3, self.input.tell())

    def test_commit_no_transaction(self):
        with self.assertRaises(IndexError):
            self.state.commit('not ready')

    def test_commit(self):
        with self.state:
            self.state.commit('a value')
            self.assertTrue(self.state.committed)
            self.assertTrue(self.state.successful)
            self.assertEqual('a value', self.state.value)

    def test_set_value(self):
        with self.state:
            self.state.value = 'a value'
            self.assertFalse(self.state.committed)
            self.assertTrue(self.state.successful)
            self.assertEqual('a value', self.state.value)

    def test_rollback(self):
        with self.state:
            self.state.commit('a value')
            self.state.rollback()
            self.assertFalse(self.state.committed)
            self.assertFalse(self.state.successful)
            self.assertEqual(parser.UNUSED, self.state.value)

    def test_bad_skipper(self):
        with self.assertRaises(TypeError):
            parser.ParserState(' ', object())


class ParserTestCase(unittest.TestCase):

    def test_parse_string(self):
        p = parser.Char('a')
        self.assertEqual((True, 'a'), p.parse('a'))

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

    def test_lshift_string(self):
        s = io.StringIO('abc')
        self.assertEqual((True, 'a'), (parser.Char('a') << 'b').parse(s))
        self.assertEqual('c', s.read())

    def test_rlshift_string(self):
        s = io.StringIO('abc')
        self.assertEqual((True, 'b'), ('a' << parser.Char('b')).parse(s))
        self.assertEqual('c', s.read())

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

    def test_or_string(self):
        p = parser.Char('a') | 'b'
        s = io.StringIO('ab')
        self.assertEqual((True, 'a'), p.parse(s))
        self.assertEqual((True, parser.UNUSED), p.parse(s))

    def test_ror_string(self):
        p = 'a' | parser.Char('b')
        s = io.StringIO('ab')
        self.assertEqual((True, parser.UNUSED), p.parse(s))
        self.assertEqual((True, 'b'), p.parse(s))

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

    def test_skipping(self):
        p = parser.String('abc') << parser.String('def')
        self.assertEqual((True, ('abc', 'def')), p.parse('  abc  def  ', ' '))

    def test_skipping_parser(self):
        skipper = parser.String('()')
        p = parser.String('abc') << parser.String('def')
        self.assertEqual((True, ('abc', 'def')), p.parse('()()abc()()def()()', skipper))

    def test_skipper_and_parser_state(self):
        p = parser.Parser()
        s = parser.ParserState('state')
        with self.assertRaises(TypeError):
            p.parse(s, ' ')


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


class StringTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.String('abc')
        s = io.StringIO('abcdef')
        self.assertEqual((True, 'abc'), p.parse(s))
        self.assertEqual(3, s.tell())
        self.assertEqual((False, None), p.parse(s))
        self.assertEqual(3, s.tell())

    def test_string(self):
        self.assertEqual('abc', parser.String('abc').string)


class AggregateParserTestCase(unittest.TestCase):

    def test_parsers(self):
        p1 = parser.Parser()
        p2 = parser.Parser()
        p3 = parser.Parser()
        self.assertEqual((p1, p2, p3), parser.AggregateParser(p1, p2, p3).parsers)


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

    def test_non_parser(self):
        seq = parser.Seq('hello')
        self.assertEqual((True, parser.UNUSED), seq.parse('hello'))


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

    def test_non_parser(self):
        alt = parser.Alt('hello')
        s = io.StringIO('hello')
        self.assertEqual((True, parser.UNUSED), alt.parse(s))


class UnaryTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.Unary(parser.Char('a'))
        s = io.StringIO('aa')
        self.assertEqual((True, 'a'), p.parse(s))

    def test_parser(self):
        p1 = parser.Parser()
        p2 = parser.Unary(p1)
        self.assertIs(p1, p2.parser)


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


class DirectiveParserTest(unittest.TestCase):

    class Directive(parser.DirectiveParser):

        state = None
        pre = False
        post = False

        @contextlib.contextmanager
        def _direct(self, state):
            self.state = state
            yield
            self.post = True

    def test_parse_default(self):
        p = parser.DirectiveParser(parser.Char('a'))
        s = io.StringIO('abc')
        with self.assertRaises(NotImplementedError):
            p.parse(s)

    def test_parse(self):
        p = self.Directive(parser.Char('a'))
        s = io.StringIO('abc')
        self.assertEqual((True, 'a'), p.parse(s))
        self.assertIsInstance(p.state, parser.ParserState)
        self.assertTrue(p.post)

    def test_parse(self):
        p = self.Directive(parser.Char('a'))
        s = io.StringIO('xyz')
        self.assertEqual((False, None), p.parse(s))
        self.assertIsInstance(p.state, parser.ParserState)
        self.assertTrue(p.post)


class FuncDirectiveParserTestCase(unittest.TestCase):

    @contextlib.contextmanager
    def func(self, state):
        self.state = state
        yield
        self.post = True

    def setUp(self):
        self.state = None
        self.post = False
        self.parser = parser.FuncDirectiveParser(parser.Char('a'), self.func)

    def test_parse(self):
        s = io.StringIO('abc')
        self.assertEqual((True, 'a'), self.parser.parse(s))
        self.assertIsInstance(self.state, parser.ParserState)
        self.assertTrue(self.post)

    def test_parse_fail(self):
        s = io.StringIO('xyz')
        self.assertEqual((False, None), self.parser.parse(s))
        self.assertIsInstance(self.state, parser.ParserState)
        self.assertTrue(self.post)

    def test_func(self):
        self.assertEqual(self.func, self.parser.func)


class FuncDirectiveTestCase(unittest.TestCase):

    @contextlib.contextmanager
    def func(self, state):
        self.state = state
        yield
        self.post = True

    def setUp(self):
        self.state = None
        self.post = None
        self.func_directive = parser.FuncDirective(self.func)
        self.parser = self.func_directive[parser.Char('a')]

    def test_parse(self):
        s = io.StringIO('abc')
        self.assertEqual((True, 'a'), self.parser.parse(s))
        self.assertTrue(self.post)

    def test_parse_faile(self):
        s = io.StringIO('xyz')
        self.assertEqual((False, None), self.parser.parse(s))
        self.assertTrue(self.post)

    def test_func(self):
        self.assertEqual(self.func_directive.func, self.func)


class PostDirectiveTestCase(unittest.TestCase):

    def post_func(self, state):
        self.state = state
        self.committed = state.committed
        self.successful = state.successful
        self.value = state.value

    def setUp(self):
        self.state = None
        self.committed = None
        self.successful = None
        self.value = None
        self.directive = parser.post_directive(self.post_func)
        self.parser = self.directive[parser.Char('a')]

    def test_parse(self):
        s = io.StringIO('abc')
        self.assertEqual((True, 'a'), self.parser.parse(s))
        self.assertIsInstance(self.state, parser.ParserState)
        self.assertTrue(self.committed)
        self.assertTrue(self.successful)
        self.assertEqual('a', self.value)

    def test_parse_fail(self):
        s = io.StringIO('xyz')
        self.assertEqual((False, None), self.parser.parse(s))
        self.assertIsNone(self.state)
        self.assertIsNone(self.committed)
        self.assertIsNone(self.successful)
        self.assertIsNone(self.value)


class RepeatTestCase(unittest.TestCase):

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

    def test_maximum(self):
        p = parser.Repeat(10, 20)[parser.Parser()]
        self.assertEqual(20, p.maximum)

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


class OmitTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.omit[parser.Char('a')]
        s = io.StringIO('a')
        self.assertEqual((True, parser.UNUSED), p.parse(s))

    def test_parse_fail(self):
        p = parser.omit[parser.Char('a')]
        s = io.StringIO('b')
        self.assertEqual((False, None), p.parse(s))


class AsStringTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.as_string[parser.Char('a')]
        s = io.StringIO('a')
        self.assertEqual((True, 'a'), p.parse(s))

    def test_parse_fail(self):
        p = parser.as_string[parser.Parser()]
        s = io.StringIO('a')
        self.assertEqual((False, None), p.parse(s))

    def test_parse_unused(self):
        p = parser.as_string[parser.omit[parser.Char('a')]]
        s = io.StringIO('a')
        self.assertEqual((True, ''), p.parse(s))

    def test_parse_tuple(self):
        p = parser.as_string[+parser.Char('a')]
        s = io.StringIO('aaaa')
        self.assertEqual((True, 'aaaa'), p.parse(s))

    def test_parse_tuple_recursive(self):
        p = parser.as_string[+parser.Char('a') << +parser.Char('b')]
        s = io.StringIO('aaaabbbb')
        self.assertEqual((True, 'aaaabbbb'), p.parse(s))


class LitTestCase(unittest.TestCase):

    def test_parse(self):
        p = parser.lit('abcd')
        s = io.StringIO('abcd')
        self.assertEqual((True, parser.UNUSED), p.parse(s))

    def test_parse_fail(self):
        p = parser.lit('abcd')
        s = io.StringIO('abc')
        self.assertEqual((False, None), p.parse(s))


if __name__ == '__main__':
    unittest.main()
