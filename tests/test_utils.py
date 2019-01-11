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

from http import HTTPStatus
import io
from pathlib import Path
import typing

import pytest

from embedmongo.exceptions import DownloadFileException
from embedmongo.utils import download_file, extract_file

if typing.TYPE_CHECKING:
    from _pytest._code import ExceptionInfo  # noqa: F401
    from requests_mock import Mocker

tar_file = Path(__file__).parent / 'res' / 'example.tgz'


def test_download_file_success(tmp_path: Path, requests_mock: 'Mocker'):
    url = 'https://example_url.com'
    file_content = b'example content'
    src_file = io.BytesIO(file_content)
    dst_file = tmp_path / "file"  # type: Path
    requests_mock.get(url, body=src_file, status_code=HTTPStatus.OK)

    download_file(url, dst_file)

    assert dst_file.exists()
    assert dst_file.read_bytes() == file_content


def test_download_with_etag(tmp_path: Path, requests_mock: 'Mocker'):
    url = 'https://example_url.com'
    dst_file = tmp_path / "file"  # type: Path
    expected_etag = "abcd"
    requests_mock.get(url, body=io.BytesIO(), headers={'ETag': expected_etag}, status_code=HTTPStatus.OK)

    result = download_file(url, dst_file)

    assert result.etag == expected_etag


@pytest.mark.parametrize('is_saved,status_code', [
    (True, HTTPStatus.OK),
    (True, HTTPStatus.CREATED),
    (False, HTTPStatus.NOT_MODIFIED),
])
def test_download_saved_matrix(tmp_path: Path, is_saved: bool, status_code: HTTPStatus, requests_mock: 'Mocker'):
    url = 'https://example_url.com'
    dst_file = tmp_path / "file"  # type: Path
    requests_mock.get(url, body=io.BytesIO(), status_code=status_code)

    result = download_file(url, dst_file)

    assert result.saved == is_saved


def test_download_file_fail(tmp_path: Path, requests_mock: 'Mocker'):
    url = 'https://example_url.com'
    filename = 'example.file'

    requests_mock.get(url, status_code=HTTPStatus.NOT_FOUND, text=HTTPStatus.NOT_FOUND.phrase)

    with pytest.raises(DownloadFileException) as excinfo:  # type: ExceptionInfo
        download_file(url, tmp_path / filename)

    assert "Package file {file} couldn't be downloaded from {url}. Status code: {code}. Msg: {msg}".format(
        file=filename,
        url=url,
        code=HTTPStatus.NOT_FOUND,
        msg=HTTPStatus.NOT_FOUND.phrase
    ) in str(excinfo.value)


def test_extract_illegal_strip_level():
    with pytest.raises(ValueError):
        extract_file(Path(), Path(), -1)


@pytest.mark.parametrize("strip_level,expected_path", [
    (0, 'a/b/c/file.ext'),
    (1, 'b/c/file.ext'),
    (2, 'c/file.ext'),
    (3, 'file.ext')
])
def test_extract_success(tmp_path: Path, strip_level: int, expected_path: str):
    expected_path = tmp_path / expected_path  # type: Path

    extract_file(tar_file, tmp_path, strip_level)

    assert expected_path.exists()


def test_extract_no_files(tmp_path: Path):
    file_depth = 4
    extract_file(tar_file, tmp_path, file_depth)

    dst_subitems = [child for child in tmp_path.iterdir()]

    assert len(dst_subitems) == 0
