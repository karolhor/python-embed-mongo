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
import embedmongo
from embedmongo import EmbedMongo, Version

logger = logging.getLogger(embedmongo.__name__)


def main() -> None:
    workspace = Path.home() / 'embemongo'
    workspace.mkdir(parents=True, exist_ok=True)
    em = EmbedMongo(workspace_dir=workspace)
    for v in Version:
        em.prepare(v)


if __name__ == '__main__':
    logging.basicConfig()

    logger.setLevel(logging.DEBUG)

    main()
