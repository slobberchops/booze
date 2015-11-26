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

import operator

from booz.gin import *

apply_action = lambda lval, op, rval: op(lval, rval)

arith_op  = Symbols({'+': operator.add,
                     '-': operator.sub})

mult_op   = Symbols({'*': operator.mul,
                     '/': operator.floordiv})

dec       = lexeme[+Char('0123456789')][int]

arith     = Rule()
mult      = Rule()
value     = Rule()
exp       = Rule(AttrType.OBJECT)
calc = exp

mult      %= ((value << mult_op << mult)       [apply_action]
           | value)
arith     %= ((mult << arith_op << arith)      [apply_action]
           | mult)
value     %= dec | '(' << exp << ')'
exp       %= arith

if __name__ == '__main__':
    import io
    def print_calc(string, parser=calc):
        s = io.StringIO(string)
        print (string, '=', parser.parse(s, ' ')[1])
        remaining = s.read()
        if remaining:
            print ('Parse Error: ' + remaining)

    print_calc('1')
    print_calc('1 + 1')
    print_calc('2 * 5 + 20')
    print_calc('2 * (5 + 20)')
    print_calc('2 * 3 * 4 + 10 * 20 * 30')
    print_calc('2 + 3 + 4 * 10 + 20 + 30')
