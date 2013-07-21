# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import time
import datetime

import pytest

from pymongo import MongoClient

from upaas.storage.mongodb import MongoDBStorage
from upaas.config.base import ConfigurationError


@pytest.fixture(scope="module")
def storage(request):
    dbname = "testrun-%d" % time.time()
    storage = MongoDBStorage({"database": dbname})

    def cleanup():
        client = MongoClient()
        client.drop_database(dbname)
    request.addfinalizer(cleanup)

    return storage


def test_valid_settings(storage):
    assert storage.settings.host == "localhost"
    assert storage.settings.port == 27017


def test_invalid_settings():
    with pytest.raises(ConfigurationError):
        MongoDBStorage({"port": "string"})


def test_not_exists(storage):
    assert storage.exists("missing_file") is False


def test_put_and_get(storage, empty_dir, empty_file):
    storage.put(empty_file, "abc")
    assert storage.exists("abc")

    local_path = os.path.join(empty_dir, "xyz")
    storage.get("abc", local_path)
    assert os.path.exists(local_path)


def test_put_and_delete(storage, empty_file):
    storage.put(empty_file, "delete.me")
    assert storage.exists("delete.me")

    storage.delete("delete.me")
    assert storage.exists("delete.me") is False


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
    assert isinstance(storage.mtime("mtime.check"), datetime.datetime)
    #FIXME basic check to verify if timestamp is from the past
    assert storage.mtime("mtime.check") < datetime.datetime.now()
