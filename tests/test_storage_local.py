# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import shutil
import tempfile
import datetime

import pytest

from upaas.storage.local import LocalStorage
from upaas.storage.exceptions import FileNotFound
from upaas.storage.utils import find_storage_handler
from upaas.config.base import ConfigurationError


@pytest.fixture(scope="module")
def storage(request):
    directory = tempfile.mkdtemp(prefix="upaas_teststorage_")
    storage = LocalStorage({'dir': directory})

    def cleanup():
        shutil.rmtree(storage.settings.dir)
    request.addfinalizer(cleanup)

    return storage


def test_find_storage():
    assert find_storage_handler(
        'upaas.storage.local.LocalStorage', settings={'dir': '/'}) is not None


def test_find_storage_invalid():
    with pytest.raises(ConfigurationError):
        find_storage_handler('upaas.storage.local.LocalStorage')


def test_valid_settings(storage):
    assert storage.settings.dir is not None


def test_invalid_settings():
    with pytest.raises(ConfigurationError):
        LocalStorage({})


def test_config_dir_exists(storage):
    assert os.path.isdir(storage.settings.dir)


def test_config_dir_missing():
    with pytest.raises(ConfigurationError):
        LocalStorage({"dir": "/non-existing-dir"})


def test_file_exists(storage):
    file_name = "file_exists"
    open(os.path.join(storage.settings.dir, file_name), "w").close()
    assert storage.exists(file_name) is True


def test_dir_exists(storage):
    dir_name = "dir_exists"
    os.mkdir(os.path.join(storage.settings.dir, dir_name))
    assert storage.exists(dir_name) is True


def test_not_exists(storage):
    assert storage.exists("missing_file") is False


def test_get_not_exists(storage):
    with pytest.raises(FileNotFound):
        storage.get("missing file", "output")


def test_put_and_get(storage, empty_dir, empty_file):
    storage.put(empty_file, "abc")
    assert os.path.isfile(os.path.join(storage.settings.dir, "abc"))

    local_path = os.path.join(empty_dir, "xyz")
    storage.get("abc", local_path)
    assert os.path.exists(local_path)


def test_delete_not_exists(storage):
    with pytest.raises(FileNotFound):
        storage.delete("missing file")


def test_put_and_delete(storage, empty_file):
    storage.put(empty_file, "delete.me")
    assert os.path.isfile(os.path.join(storage.settings.dir, "delete.me"))

    storage.delete("delete.me")
    assert os.path.isfile(
        os.path.join(storage.settings.dir, "delete.me")) is False


def test_size_empty(storage, empty_file):
    storage.put(empty_file, "empty.file")
    assert storage.size("empty.file") == 0


def test_size_not_empty(storage, empty_file):
    with open(empty_file, 'w') as f:
        f.write('123456789')

    storage.put(empty_file, "not-empty.file")
    assert storage.size("not-empty.file") == 9


def test_mtime(storage, empty_file):
    storage.put(empty_file, "mtime.check")
    assert storage.mtime("mtime.check") == datetime.datetime.fromtimestamp(
        os.path.getmtime(os.path.join(storage.settings.dir, "mtime.check")))
