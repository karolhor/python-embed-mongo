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

import pathlib
import typing


from .package import PackageDiscovery, PackageManager, Version


class EmbedMongo:
    def __init__(self, workspace_dir: typing.Union[str, pathlib.Path] = pathlib.Path.home() / ".pyembedmongo"):
        if isinstance(workspace_dir, str):
            workspace_dir = pathlib.Path(workspace_dir)

        self._workspace_dir = workspace_dir

    def prepare(self, version: Version) -> None:
        package = PackageDiscovery().create(version)

        manager = PackageManager(self._workspace_dir)
        local_pkg = manager.download(package)
        manager.extract(local_pkg)
