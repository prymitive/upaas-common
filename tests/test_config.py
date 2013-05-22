# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os

import pytest

from upaas.config import base


class BasicConfig(base.Config):
    schema = {
        "required_string": base.StringEntry(required=True),
        "folder1": {
            "subfolder1": {
                "required_int": base.IntegerEntry(required=True)
            },
            "optional_int": base.IntegerEntry(),
        }
    }


class ListConfig(base.Config):
    schema = {
        u"mylist": base.ListEntry(value_type=int)
    }


class DictConfig(base.Config):
    schema = {
        u"mydict": base.DictEntry(value_type=unicode)
    }


def test_empty():
    with pytest.raises(base.ConfigurationError):
        BasicConfig({})


def test_required_entries_from_dict():
    cfg = BasicConfig({
        u"required_string": u"abc",
        u"folder1": {
            u"subfolder1": {
                u"required_int": 123
            }
        }
    })
    assert cfg.required_string == u"abc"
    assert cfg.folder1.subfolder1.required_int == 123
    with pytest.raises(AttributeError):
        print(cfg.folder1.optional_int)


def test_required_entries_from_file():
    cfg = BasicConfig.from_file(os.path.join(os.path.dirname(__file__),
                                             "test_config.yml"))
    assert cfg.required_string == u"abc"
    assert cfg.folder1.subfolder1.required_int == 123
    with pytest.raises(AttributeError):
        print(cfg.folder1.optional_int)


def test_dump():
    options = {
        u"required_string": u"abc",
        u"folder1": {
            u"subfolder1": {
                u"required_int": 123
            }
        }
    }
    cfg = BasicConfig(options)
    assert cfg.dump() == options


def test_default_value():
    class LocalConfig(base.Config):
        schema = {u"myitem": base.StringEntry(default=u"default value")}

    cfg = LocalConfig({})
    assert cfg.myitem == u"default value"


def test_list_entry_valid():
    cfg = ListConfig({u"mylist": [1, 2, 3, 4]})
    assert cfg.mylist == [1, 2, 3, 4]

    cfg = ListConfig({})
    assert cfg.mylist == []


def test_list_entry_invalid():
    with pytest.raises(base.ConfigurationError):
        ListConfig({u"mylist": {"a": 1}})

    with pytest.raises(base.ConfigurationError):
        ListConfig({u"mylist": [u"not an int", 1]})


def test_dict_entry_valid():
    cfg = DictConfig({u"mydict": {u"keya": u"valuea", u"keyb": u"valueb"}})
    assert cfg.mydict == {u"keya": u"valuea", u"keyb": u"valueb"}

    cfg = DictConfig({})
    assert cfg.mydict == {}


def test_dict_entry_invalid():
    with pytest.raises(base.ConfigurationError):
        DictConfig({u"mydict": [1]})

    with pytest.raises(base.ConfigurationError):
        DictConfig({u"mydict": {u"not an unicode": 1}})
