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

import functools


def singleton(cls):
    return cls()


def calculated_property(method):
    cached_value_name = '_cached_' + method.__name__
    @property
    @functools.wraps(method)
    def calculated_wrapper(self):
        try:
            return getattr(self, cached_value_name)
        except AttributeError:
            value = method(self)
            setattr(self, cached_value_name, value)
            return value
    return calculated_wrapper
