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
from booz.gin import string


class SymbolsTestCase(unittest.TestCase):

    def test_parse(self):
        symbols = string.Symbols({'animal': 1, 'book': 2})
        self.assertEqual((True, 1), symbols.parse('animal'))
        self.assertEqual((True, 2), symbols.parse('book'))

    def test_parse_fail(self):
        symbols = string.Symbols({'animal': 1, 'book': 2})
        s = io.StringIO('planet')
        self.assertEqual((False, None), symbols.parse(s))
        self.assertEqual(0, s.tell())

    def test_empty_symbols(self):
        with self.assertRaises(ValueError):
            string.Symbols({})

    def test_wrong_values_attr_type_provided(self):
        with self.assertRaises(TypeError):
            string.Symbols({'animal': 20}, parser.AttrType.STRING)

    def test_attr_type_provided(self):
        self.assertEqual(parser.AttrType.OBJECT,
                         string.Symbols({'a': '1', 'b': '2'}, parser.AttrType.OBJECT).attr_type)

    def test_attr_type_string(self):
        self.assertEqual(parser.AttrType.STRING, string.Symbols({'a': '1', 'b': '2'}).attr_type)

    def test_attr_type_tuple(self):
        self.assertEqual(parser.AttrType.TUPLE, string.Symbols({'a': (1, 2), 'b': (3, 4)}).attr_type)

    def test_attr_type_object(self):
        self.assertEqual(parser.AttrType.OBJECT, string.Symbols({'a': 'a string', 'b': (3, 4)}).attr_type)


if __name__ == '__main__':
    unittest.main()
