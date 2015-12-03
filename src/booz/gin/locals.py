# Copyright 2015 Rafe Kaplan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .. import util
from .. import whiskey


class GetAttr(whiskey.Action):

    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def invoke(self, *args, locals=None, **kwargs):
        if locals is None:
            raise TypeError('Must provide \'locals\' parameter')
        return getattr(locals, whiskey.invoke(self.__name, *args, locals=locals, **kwargs))


@util.singleton
class l:

    def __getattr__(self, name):
        return GetAttr(name)
