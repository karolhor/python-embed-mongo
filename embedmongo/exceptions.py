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


class EmbedMongoException(Exception):
    """General module exception."""


class PackageManagerException(EmbedMongoException):
    """General exception for package management."""


class PackageNotFoundException(PackageManagerException):
    """Predefined package version not found."""


class InvalidOSException(EmbedMongoException):
    """Errors related with working OS, e.g. unsupported type."""


class DownloadFileException(EmbedMongoException):
    """Errors when file couldn't be downloaded."""
