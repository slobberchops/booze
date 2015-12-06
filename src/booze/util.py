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
    """Define a singleton class.

    A singleton class has only one instance.

    Example:

        @singleton
        class my_singleton:

            __counter = 0

            def inc(self):
                self.__counter += 1
                return self.__counter

        assert my_singleton.inc() == 1
        assert my_singleton.inc() == 2

    Args:
        cls: Class for which there will be only one instance.

    Returns:
        Singleton class instance.
    """
    return cls()


def calculated_property(method):
    """Define a cached, read-only, calculated property.

    Example:

        class MyClass:

            call_count = 0

            @calculated_property
            def calc_property(self):
                self.call_count += 1
                return 10

        instance = MyClass()
        assert instance.calc_property == 10
        assert instance.call_count == 1
        assert instance.calc_property == 10
        assert instance.call_count == 1


    Args:
        method: Method definging calculated property.

    Returns:
        Calculated property with built in caching so that calculation only occurs once per instance.
    """
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
