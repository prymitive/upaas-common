# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


class InvalidStorageConfiguration(Exception):
    pass


class StorageError(Exception):
    pass


class FileNotFound(StorageError):
    pass


class FileAlreadyExists(StorageError):
    pass
