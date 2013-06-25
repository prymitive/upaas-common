# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import time

import pytest

from upaas.storage.mongodb import MongoDBStorage
from upaas.config.base import ConfigurationError


@pytest.fixture(scope="module")
def storage(request):
    storage = MongoDBStorage({"database": "testrun-%d" % time.time()})
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
