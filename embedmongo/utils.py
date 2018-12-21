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

import logging
from pathlib import Path
import tarfile
from typing import Optional

import requests
import tqdm

from .exceptions import DownloadFileException
from .log import TqdmToLogger

logger = logging.getLogger(__name__)


def download_file(url: str, filename: str, dst: Path) -> None:
    with dst.open("wb") as local_file, requests.get(url, stream=True) as req:
        content_length = req.headers.get('content-length')
        total_size = None
        if content_length:
            total_size = int(content_length)

        if not req.ok:
            error_msg = "Package file {file} couldn't be downloaded from {url}. Status code: {code}. Msg: {msg}".format(
                url=url,
                file=filename,
                code=req.status_code,
                msg=req.text
            )
            raise DownloadFileException(error_msg)

        logger.debug('Downloaded file {name} size: {size}'.format(name=filename, size=total_size))
        with _progress_bar(filename, total_size) as pgbar:
            chunk_size = 1024*1024

            for chunk in req.iter_content(chunk_size=chunk_size):
                if chunk:
                    local_file.write(chunk)
                    pgbar.update(len(chunk))


def extract_file(src: Path, dst: Path, strip_level: Optional[int] = 0) -> None:
    if strip_level is not None and strip_level < 0:
        raise ValueError("strip_level argument should not be negative")

    with tarfile.open(str(src)) as tar:
        members = []
        if strip_level:
            for member in tar.getmembers():
                member.name = '/'.join(member.name.split('/')[strip_level:])
                if member.name:
                    members.append(member)
        else:
            members = tar.getmembers()

        tar.extractall(path=str(dst), members=members)


def _progress_bar(desc: str, total: Optional[int]) -> tqdm.tqdm:
    tqdm_out = TqdmToLogger(logger, level=logging.INFO)
    bar_format = "{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]"

    return tqdm.tqdm(
        total=total,
        miniters=1,
        unit_scale=True,
        unit='B',
        desc=desc,
        file=tqdm_out,
        bar_format=bar_format
    )
