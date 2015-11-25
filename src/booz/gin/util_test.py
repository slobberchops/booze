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

from booz.gin import util


class SingletonTestCase(unittest.TestCase):

    def test_singleton(self):
        class Cls:
            pass

        singleton = util.singleton(Cls)
        self.assertIsInstance(singleton, Cls)


class CalculatedPropertyTestCase(unittest.TestCase):

    def test_caclulated_property(self):
        class Cls:

            call_count = 0

            @util.calculated_property
            def prop(self):
                self.call_count += 1
                return 100

        instance = Cls()
        self.assertEqual(100, instance.prop)
        self.assertEqual(1, instance.call_count)
        self.assertEqual(100, instance.prop)
        self.assertEqual(1, instance.call_count)


if __name__ == '__main__':
    unittest.main()
