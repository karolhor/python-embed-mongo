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
import json
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, NamedTuple, Optional

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


ExternalPackage = NamedTuple('ExternalPackage', [('version', Version), ('url', str), ('os_type', str), ('filename', str)])
LocalPackage = NamedTuple('LocalPackage', [('version', Version), ('path', Path), ('new_file', bool)])


class _PkgMetadata:
    def __init__(self, raw_data: Optional[Dict[str, Any]] = None):
        if not raw_data:
            raw_data = {}

        download_data = raw_data.get('download', {})

        self.download_etag = download_data.get('etag', None)
        self.download_url = download_data.get('url', None)
        self.download_filename = download_data.get('filename', None)

    def to_json(self) -> str:
        return json.dumps({
            'download': {
                'etag': self.download_etag,
                'url': self.download_url,
                'filename': self.download_filename
            }
        })


class _VersionDir:
    _METADATA_FILENAME = 'metadata.json'

    def __init__(self, workspace_dir: Path, version: Version, archive_filename: Optional[str]):
        self.version = version
        self.path = workspace_dir / self.version.version
        self.path.mkdir(parents=True, exist_ok=True)

        if archive_filename:
            self.archive_path = self.path / archive_filename
            self.extracted_dir = self.path / self.archive_path.stem
            self.metadata_path = self.path / self._METADATA_FILENAME

    def save_metadata(self, metadata: _PkgMetadata) -> None:
        self.metadata_path.write_text(metadata.to_json())

    def read_metadata(self) -> _PkgMetadata:
        if not self.metadata_path.exists():
            return _PkgMetadata()

        content = json.loads(self.metadata_path.read_text())

        return _PkgMetadata(content)

    @staticmethod
    def from_ext_package(workspace_dir: Path, pkg: ExternalPackage) -> '_VersionDir':
        return _VersionDir(workspace_dir, pkg.version, pkg.filename)

    @staticmethod
    def from_local_package(workspace_dir: Path, pkg: LocalPackage) -> '_VersionDir':
        return _VersionDir(workspace_dir, pkg.version, pkg.path.name)


class PackageManager:
    def __init__(self, workspace_dir: Path):
        WorkingOSGuard.ensure_valid_type()

        self._workspace_dir = workspace_dir
        self._workspace_dir.mkdir(parents=True, exist_ok=True)

    def download(self, pkg: ExternalPackage) -> LocalPackage:
        logger.info("Downloading {version} package from {url}".format(version=pkg.version.version, url=pkg.url))

        version_dir = _VersionDir.from_ext_package(self._workspace_dir, pkg)
        metadata = version_dir.read_metadata()
        if not metadata.download_etag or not version_dir.archive_path.exists():
            etag = None
        else:
            etag = metadata.download_etag

        download_result = download_file(pkg.url, version_dir.archive_path, etag)
        metadata.download_etag = download_result.etag
        metadata.download_url = pkg.url
        metadata.download_filename = pkg.filename
        version_dir.save_metadata(metadata)

        return LocalPackage(version=pkg.version, path=version_dir.archive_path, new_file=download_result.saved)

    def extract(self, pkg: LocalPackage) -> Path:
        version_dir = _VersionDir.from_local_package(self._workspace_dir, pkg)

        # we don't want to ignore errors on rmtree, so it's important to call this when extracted directory exists
        if pkg.new_file and version_dir.extracted_dir.exists():
            logger.info("New version of archive {pkg}. Removing old extracted directory {dst}.".format(pkg=pkg.path.name, dst=version_dir.extracted_dir))
            shutil.rmtree(str(version_dir.extracted_dir))

        if not version_dir.extracted_dir.exists():
            logger.info("Extracting {pkg} to {dst}".format(pkg=pkg.path.name, dst=version_dir.extracted_dir))
            extract_file(pkg.path, version_dir.extracted_dir, strip_level=1)
        else:
            logger.info("No change of archive detected. Skipping pkg extraction.".format(pkg=pkg.path.name, dst=version_dir.extracted_dir))

        bin_dir = version_dir.extracted_dir / 'bin'
        logger.info(bin_dir)

        return bin_dir

    def clean(self, version: Version, ignore_errors: bool = False) -> None:
        version_dir = _VersionDir(self._workspace_dir, version, archive_filename=None)
        shutil.rmtree(str(version_dir.path), ignore_errors=ignore_errors)


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
