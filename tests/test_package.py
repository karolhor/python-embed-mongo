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

from embedmongo.exceptions import InvalidOSException, PackageNotFoundException
from embedmongo.package import PackageDiscovery, Version
from embedmongo.system import OSInfo


class TestPackageDiscovery:
    def test_create_unsupported_os_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):
            m.setattr(OSInfo, 'type', lambda: 'unknown')

            PackageDiscovery().create(Version.V4_0_LATEST)

    def test_create_unsupported_platform_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):
            m.setattr(OSInfo, 'type', lambda: 'linux')
            m.setattr(OSInfo, 'architecture', lambda: 'i386')

            PackageDiscovery().create(Version.V4_0_LATEST)

    def test_create_unsupported_version_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(PackageNotFoundException):
            m.setattr(OSInfo, 'type', lambda: 'linux')
            m.setattr(OSInfo, 'architecture', lambda: 'x86_64')

            discovery = PackageDiscovery()
            discovery._package_paths_map = {
                'linux': {}
            }

            discovery.create(Version.V3_0_LATEST)

    def test_create_return_external_package(self, monkeypatch):
        version = Version.V4_0_LATEST
        os_type = 'linux'
        expected_pkg_name = 'mongodb-linux-x86_64-v4.0-latest.tgz'

        with monkeypatch.context() as m:
            m.setattr(OSInfo, 'type', lambda: os_type)
            m.setattr(OSInfo, 'architecture', lambda: 'x86_64')

            pkg = PackageDiscovery().create(version)

        assert pkg.version == version
        assert pkg.os_type == os_type
        assert pkg.filename == expected_pkg_name
        assert pkg.url == 'http://downloads.mongodb.org/{os_type}/{pkg_name}'.format(os_type=os_type, pkg_name=expected_pkg_name)
