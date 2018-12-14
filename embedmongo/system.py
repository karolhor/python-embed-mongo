# Copyright 2018 Karol Horowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import platform

from .exceptions import InvalidOSException


class OSInfo:
    @staticmethod
    def type() -> str:
        os_type = platform.system().lower()
        if os_type == 'darwin':
            os_type = 'osx'

        return os_type

    @staticmethod
    def architecture() -> str:
        return platform.machine()


class WorkingOSGuard:
    @staticmethod
    def ensure_valid_type() -> None:
        system_name = OSInfo.type()
        if system_name not in {'linux', 'osx'}:
            raise InvalidOSException('System {os_name} is unsupported'.format(os_name=system_name))

    @staticmethod
    def ensure_valid_architecture() -> None:
        os_arch = OSInfo.architecture()
        if os_arch != 'x86_64':
            raise InvalidOSException('System architecture {os_arch} is unsupported.'.format(os_arch=os_arch))
