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

import enum
import logging
from pathlib import Path
import typing


from .exceptions import PackageNotFoundException
from .system import OSInfo, WorkingOSGuard
from .utils import download_file, extract_file

logger = logging.getLogger(__name__)


class Version(enum.Enum):
    V3_0_LATEST = '3.0-latest'
    V3_0_15 = '3.0.15'

    V3_1_9 = '3.1.9'

    V3_2_LATEST = '3.2-latest'
    V3_2_21 = '3.2.21'

    V3_3_15 = '3.3.15'

    V3_4_LATEST = '3.4-latest'
    V3_4_18 = '3.4.18'

    V3_5_13 = '3.5.13'

    V3_6_LATEST = '3.6-latest'
    V3_6_9 = '3.6.9'

    V3_7_9 = '3.7.9'

    V4_0_LATEST = '4.0-latest'
    V4_0_4 = '4.0.4'

    def __init__(self, version: str):
        self.version = version


ExternalPackage = typing.NamedTuple('ExternalPackage', [('version', Version), ('url', 'str'), ('os_type', 'str'), ('filename', 'str')])
LocalPackage = typing.NamedTuple('LocalPackage', [('version', Version), ('path', Path)])


class PackageManager:
    def __init__(self, workspace_dir: Path):
        WorkingOSGuard.ensure_valid_type()

        self._workspace_dir = workspace_dir
        self._workspace_dir.mkdir(parents=True, exist_ok=True)

    def download(self, pkg: ExternalPackage) -> LocalPackage:
        logger.info("Downloading {version} package from {url}".format(version=pkg.version.version, url=pkg.url))

        working_dir = self._package_working_dir(pkg.version)
        working_dir.mkdir(parents=True, exist_ok=True)
        local_pkg_path = working_dir / pkg.filename

        download_file(pkg.url, pkg.filename, local_pkg_path)

        return LocalPackage(version=pkg.version, path=local_pkg_path)

    def extract(self, pkg: LocalPackage) -> Path:
        dst_dir = self._package_working_dir(pkg.version) / pkg.path.stem
        logger.info("Extracting {pkg} to {dst}".format(pkg=pkg.path.name, dst=dst_dir))

        extract_file(pkg.path, dst_dir)

        bin_dir = dst_dir / 'bin'
        logger.info(bin_dir)

        return bin_dir

    def clean(self, pkg: LocalPackage) -> None:
        pass

    def _package_working_dir(self, version: Version) -> Path:
        return self._workspace_dir / version.version


class PackageDiscovery:
    _package_paths_map = {
        'osx': {
            Version.V3_0_LATEST: 'mongodb-osx-ssl-x86_64-v3.0-latest.tgz',
            Version.V3_0_15:     'mongodb-osx-ssl-x86_64-3.0.15.tgz',
            Version.V3_1_9:      'mongodb-osx-ssl-x86_64-3.1.9.tgz',
            Version.V3_2_LATEST: 'mongodb-osx-ssl-x86_64-v3.2-latest.tgz',
            Version.V3_2_21:     'mongodb-osx-ssl-x86_64-3.2.21.tgz',
            Version.V3_3_15:     'mongodb-osx-ssl-x86_64-3.3.15.tgz',
            Version.V3_4_LATEST: 'mongodb-osx-ssl-x86_64-v3.4-latest.tgz',
            Version.V3_4_18:     'mongodb-osx-ssl-x86_64-3.4.18.tgz',
            Version.V3_5_13:     'mongodb-osx-ssl-x86_64-3.5.13.tgz',
            Version.V3_6_LATEST: 'mongodb-osx-ssl-x86_64-v3.6-latest.tgz',
            Version.V3_6_9:      'mongodb-osx-ssl-x86_64-3.6.9.tgz',
            Version.V3_7_9:      'mongodb-osx-ssl-x86_64-3.7.9.tgz',
            Version.V4_0_LATEST: 'mongodb-osx-ssl-x86_64-v4.0-latest.tgz',
            Version.V4_0_4:      'mongodb-osx-ssl-x86_64-4.0.4.tgz',
        },

        'linux': {
            Version.V3_0_LATEST: 'mongodb-linux-x86_64-v3.0-latest.tgz',
            Version.V3_0_15:     'mongodb-linux-x86_64-3.0.15.tgz',
            Version.V3_1_9:      'mongodb-linux-x86_64-3.1.9.tgz',
            Version.V3_2_LATEST: 'mongodb-linux-x86_64-v3.2-latest.tgz',
            Version.V3_2_21:     'mongodb-linux-x86_64-3.2.21.tgz',
            Version.V3_3_15:     'mongodb-linux-x86_64-3.3.15.tgz',
            Version.V3_4_LATEST: 'mongodb-linux-x86_64-v3.4-latest.tgz',
            Version.V3_4_18:     'mongodb-linux-x86_64-3.4.18.tgz',
            Version.V3_5_13:     'mongodb-linux-x86_64-3.5.13.tgz',
            Version.V3_6_LATEST: 'mongodb-linux-x86_64-v3.6-latest.tgz',
            Version.V3_6_9:      'mongodb-linux-x86_64-3.6.9.tgz',
            Version.V3_7_9:      'mongodb-linux-x86_64-3.7.9.tgz',
            Version.V4_0_LATEST: 'mongodb-linux-x86_64-v4.0-latest.tgz',
            Version.V4_0_4:      'mongodb-linux-x86_64-4.0.4.tgz',
        }
    }

    def __init__(self, repo_url: str = "http://downloads.mongodb.org"):
        self._repo_url = repo_url

    def create(self, version: Version) -> ExternalPackage:
        WorkingOSGuard.ensure_valid_type()
        WorkingOSGuard.ensure_valid_architecture()

        os_type = OSInfo.type()
        package_path = self._package_paths_map[os_type].get(version, None)

        if not package_path:
            raise PackageNotFoundException("Predefined package for given OS and version not found.")

        package_url = "{repo_url}/{os_type}/{package_path}".format(
            repo_url=self._repo_url,
            os_type=os_type,
            package_path=package_path
        )

        return ExternalPackage(version=version, os_type=os_type, filename=package_path, url=package_url)
