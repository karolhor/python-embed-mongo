# Copyright 2019 Karol Horowski
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

import pytest

from embedmongo.exceptions import InvalidOSException
from embedmongo.system import OSInfo, WorkingOSGuard


class TestOSInfo:
    def test_type_supported_linux(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr('platform.system', lambda: 'linux')

            assert OSInfo.type() == 'linux'

    def test_type_supported_osx(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr('platform.system', lambda: 'Darwin')

            assert OSInfo.type() == 'osx'


class TestWorkingOSGuard:
    @pytest.mark.parametrize("os_type", ['linux', 'osx'])
    def test_ensure_valid_type_with_supported_os(self, os_type, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(OSInfo, 'type', lambda: os_type)
            WorkingOSGuard.ensure_valid_type()

    def test_ensure_valid_type_raise_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):
            m.setattr(OSInfo, 'type', lambda: 'unknown')

            WorkingOSGuard.ensure_valid_type()

    def test_ensure_valid_architecture_with_supported_arch(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(OSInfo, 'architecture', lambda: 'x86_64')

            WorkingOSGuard.ensure_valid_architecture()

    def test_ensure_valid_architecture_raise_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):
            m.setattr(OSInfo, 'architecture', lambda: 'i386')

            WorkingOSGuard.ensure_valid_architecture()
