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

import requests
import tqdm
import logging

import io
logger = logging.getLogger(__name__)


class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''

    def __init__(self, logger, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip('\r\n\t ')

    def flush(self):
        self.logger.log(self.level, self.buf)


def download_package(url):
    package_name = url.split("/")[-1]

    with open(package_name, "wb") as f, requests.get(url, stream=True) as r:
        logger.info("Downloading {}".format(url))
        chunk_size = 1024*1024
        tqdm_out = TqdmToLogger(logger,level=logging.INFO)
        bar_format = "{desc}: {percentage:3.0f}% | {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]"
        with tqdm.tqdm(total=int(r.headers.get('content-length')), miniters=1, unit_scale=True, unit='B', desc=package_name, file=tqdm_out, bar_format=bar_format) as pbar:

            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def main():
    download_package("http://downloads.mongodb.org/osx/mongodb-osx-ssl-x86_64-4.0.0.tgz")


if __name__ == '__main__':
    logging.basicConfig()

    # logger.setLevel(logging.DEBUG)

    main()
