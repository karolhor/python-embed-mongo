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

from http import HTTPStatus
from pathlib import Path
import typing

import pytest

from embedmongo.exceptions import InvalidOSException, PackageNotFoundException
from embedmongo.package import _PkgMetadata, _VersionDir, ExternalPackage, PackageDiscovery, PackageManager, Version
from embedmongo.system import OSInfo

if typing.TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch  # noqa: F401
    from requests_mock import Mocker
    from requests.models import Request


class TestPackageDiscovery:
    def test_create_unsupported_os_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):  # type: MonkeyPatch
            m.setattr(OSInfo, 'type', lambda: 'unknown')

            PackageDiscovery().create(Version.V4_0_LATEST)

    def test_create_unsupported_platform_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(InvalidOSException):  # type: MonkeyPatch
            m.setattr(OSInfo, 'type', lambda: 'linux')
            m.setattr(OSInfo, 'architecture', lambda: 'i386')

            PackageDiscovery().create(Version.V4_0_LATEST)

    def test_create_unsupported_version_raises_exception(self, monkeypatch):
        with monkeypatch.context() as m, pytest.raises(PackageNotFoundException):  # type: MonkeyPatch
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

        with monkeypatch.context() as m:  # type: MonkeyPatch
            m.setattr(OSInfo, 'type', lambda: os_type)
            m.setattr(OSInfo, 'architecture', lambda: 'x86_64')

            pkg = PackageDiscovery().create(version)

        assert pkg.version == version
        assert pkg.os_type == os_type
        assert pkg.filename == expected_pkg_name
        assert pkg.url == 'http://downloads.mongodb.org/{os_type}/{pkg_name}'.format(os_type=os_type, pkg_name=expected_pkg_name)


_PKGFile = typing.NamedTuple("_PKGFile", [('local_path', Path), ('ref', typing.BinaryIO)])


class TestPackageManager:
    PKG_URL = "https://example_url.com/pkg/pkg-name.tgz"

    @pytest.fixture
    def workspace_dir(self, tmp_path: Path, monkeypatch) -> typing.Generator[Path, None, None]:
        with monkeypatch.context() as m:  # type: MonkeyPatch
            m.setattr(OSInfo, 'type', lambda: 'linux')
            m.setattr(OSInfo, 'architecture', lambda: 'x86_64')

            yield tmp_path

    @pytest.fixture
    def version_dir(self, workspace_dir: Path, external_file: _PKGFile, external_pkg: ExternalPackage) -> _VersionDir:
        return _VersionDir(workspace_dir, external_pkg)

    @pytest.fixture
    def loaded_version_dir(self, version_dir: _VersionDir, external_file: _PKGFile, external_pkg: ExternalPackage):
        version_dir.pkg_path.write_bytes(external_file.local_path.read_bytes())

        metadata = _PkgMetadata()
        metadata.download_filename = external_pkg.filename
        metadata.download_url = TestPackageManager.PKG_URL
        metadata.download_etag = "abcd"

        version_dir.save_metadata(metadata)

        return version_dir

    @pytest.fixture
    def external_pkg(self) -> ExternalPackage:
        return ExternalPackage(version=Version.V4_0_LATEST, url=TestPackageManager.PKG_URL, os_type='linux', filename="pkg-name.tgz")

    @pytest.fixture
    def external_file(self) -> typing.Generator[_PKGFile, None, None]:
        pkg_file = Path(__file__).parent / 'res' / 'mongo.tgz'  # type: Path
        with pkg_file.open("rb") as f:
            yield _PKGFile(local_path=pkg_file, ref=f)

    def test_download_empty_workspace_dir(self, workspace_dir: Path, external_file: _PKGFile, external_pkg: ExternalPackage, requests_mock: 'Mocker'):
        requests_mock.get(TestPackageManager.PKG_URL, status_code=HTTPStatus.OK, body=external_file.ref)
        expected_filepath = workspace_dir / external_pkg.version.version / external_pkg.filename

        PackageManager(workspace_dir).download(external_pkg)

        assert expected_filepath.exists()

    def test_download_create_metadata_file(self, version_dir: _VersionDir, external_file: _PKGFile, external_pkg: ExternalPackage, requests_mock: 'Mocker'):
        expected_metadata = _PkgMetadata()
        expected_metadata.download_url = TestPackageManager.PKG_URL
        expected_metadata.download_filename = external_pkg.filename
        expected_metadata.download_etag = 'abcd'

        requests_mock.get(TestPackageManager.PKG_URL, status_code=HTTPStatus.OK, headers={'ETag': expected_metadata.download_etag}, body=external_file.ref)

        PackageManager(version_dir.path.parent).download(external_pkg)

        assert version_dir.metadata_path.exists()
        actual_metadata = version_dir.read_metadata()

        assert actual_metadata.download_url == expected_metadata.download_url
        assert actual_metadata.download_filename == expected_metadata.download_filename
        assert actual_metadata.download_etag == expected_metadata.download_etag

    def test_download_overwrite_missing_metadata(self, loaded_version_dir: _VersionDir, external_file: _PKGFile, external_pkg: ExternalPackage,
                                                 requests_mock: 'Mocker'):
        expected_filepath = loaded_version_dir.pkg_path
        expected_size = expected_filepath.stat().st_size
        prev_file_mtime = expected_filepath.stat().st_mtime
        loaded_version_dir.metadata_path.unlink()

        requests_mock.get(TestPackageManager.PKG_URL, status_code=HTTPStatus.OK, additional_matcher=_without_etag_cache_matcher, body=external_file.ref)

        PackageManager(loaded_version_dir.path.parent).download(external_pkg)

        assert expected_filepath.exists()
        assert external_file.local_path.stat().st_size == expected_size
        assert external_file.local_path.stat().st_mtime != prev_file_mtime
        assert loaded_version_dir.metadata_path.exists()

    def test_download_overwrite_missing_pkg(self, loaded_version_dir: _VersionDir, external_file: _PKGFile, external_pkg: ExternalPackage,
                                            requests_mock: 'Mocker'):
        expected_filepath = loaded_version_dir.pkg_path
        expected_filepath.unlink()

        requests_mock.get(TestPackageManager.PKG_URL, status_code=HTTPStatus.OK, additional_matcher=_without_etag_cache_matcher, body=external_file.ref)

        PackageManager(loaded_version_dir.path.parent).download(external_pkg)

        assert expected_filepath.exists()
        assert loaded_version_dir.metadata_path.exists()

    def test_download_ignore_download(self, loaded_version_dir: _VersionDir, external_file: _PKGFile, external_pkg: ExternalPackage, requests_mock: 'Mocker'):
        expected_filepath = loaded_version_dir.pkg_path
        expected_pkg_mtime = expected_filepath.stat().st_mtime
        expected_metadata_path = loaded_version_dir.metadata_path

        expected_etag = loaded_version_dir.read_metadata().download_etag
        requests_mock.get(TestPackageManager.PKG_URL, status_code=HTTPStatus.NOT_MODIFIED, request_headers={'if-none-match': expected_etag},
                          body=external_file.ref)

        PackageManager(loaded_version_dir.path.parent).download(external_pkg)

        assert expected_filepath.exists()
        assert expected_filepath.stat().st_mtime == expected_pkg_mtime
        assert expected_metadata_path.exists()


def _without_etag_cache_matcher(request: 'Request'):
    return 'etag' not in request.headers and 'if-none-match' not in request.headers
