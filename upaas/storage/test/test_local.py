# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import shutil
import tempfile
import logging

import pytest

from upaas.storage.local import LocalStorage
from upaas.storage.exceptions import InvalidStorageConfiguration


logging.basicConfig(level=logging.FATAL)
log = logging.getLogger()


@pytest.fixture(scope="module")
def storage(request):
    dir = tempfile.mkdtemp(prefix="upaas_teststorage_")
    storage = LocalStorage({'dir': dir})

    def cleanup():
        shutil.rmtree(storage.dir)
    request.addfinalizer(cleanup)

    return storage


@pytest.fixture(scope="function")
def empty_dir(request):
    dir = tempfile.mkdtemp(prefix="upaas_testdir_")

    def cleanup():
        shutil.rmtree(dir)

    request.addfinalizer(cleanup)
    return dir


@pytest.fixture(scope="function")
def empty_file(request):
    path = tempfile.mkstemp(prefix="upaas_testfile_")[1]

    def cleanup():
        os.remove(path)

    request.addfinalizer(cleanup)
    return path


def test_valid_settings(storage):
    assert storage.dir is not None


def test_invalid_settings():
    with pytest.raises(InvalidStorageConfiguration):
        storage = LocalStorage({})


def test_dir_exists(storage):
    assert os.path.isdir(storage.dir)


def test_dir_missing():
    with pytest.raises(InvalidStorageConfiguration):
        storage = LocalStorage({'dir': '/non-existing-dir'})


def test_put_and_get(storage, empty_dir, empty_file):
    storage.put(empty_file, "abc")
    assert os.path.isfile(os.path.join(storage.dir, "abc"))

    local_path = os.path.join(empty_dir, "xyz")
    storage.get("abc", local_path)
    assert os.path.exists(local_path)
