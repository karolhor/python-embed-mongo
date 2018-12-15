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

import pytest

from embedmongo.utils import download_file
from embedmongo.exceptions import DownloadFileException


def test_download_file_success(tmp_path, requests_mock):
    url = 'https://example_url.com'
    file_content = b'example content'
    src_file = io.BytesIO(file_content)
    dst_file = tmp_path / "file"  # type: 'Path'
    requests_mock.get(url, body=src_file, status_code=HTTPStatus.OK)

    download_file(url, 'filename', dst_file)

    assert dst_file.exists()
    assert dst_file.read_bytes() == file_content


def test_download_file_fail(tmp_path, requests_mock):
    url = 'https://example_url.com'
    filename = 'example.file'

    requests_mock.get(url, status_code=HTTPStatus.NOT_FOUND, text=HTTPStatus.NOT_FOUND.phrase)

    with pytest.raises(DownloadFileException) as excinfo:
        download_file(url, filename, tmp_path / "file")

    assert "Package file {file} couldn't be downloaded from {url}. Status code: {code}. Msg: {msg}".format(
        file=filename,
        url=url,
        code=HTTPStatus.NOT_FOUND,
        msg=HTTPStatus.NOT_FOUND.phrase
    ) in str(excinfo.value)
