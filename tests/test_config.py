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


class ListConfigNoType(base.Config):
    schema = {
        u"mylist": base.ListEntry()
    }


class DictConfig(base.Config):
    schema = {
        u"mydict": base.DictEntry(value_type=unicode)
    }


class DictConfigNoType(base.Config):
    schema = {
        u"mydict": base.DictEntry()
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


def test_loading_from_missing_file():
    with pytest.raises(base.ConfigurationError):
        BasicConfig.from_file("/there/is/no/such/file.yaml")


def test_loading_from_string():
    options = "folder1:\n  subfolder1: {required_int: 123}\n" \
              "required_string: abc\n"
    cfg = BasicConfig.from_string(options)
    assert cfg.dump_string() == options


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


def test_dump_string():
    options = {
        u"required_string": u"abc",
        u"folder1": {
            u"subfolder1": {
                u"required_int": 123
            }
        }
    }
    cfg = BasicConfig(options)
    assert cfg.dump_string() == "folder1:\n  subfolder1: " \
                                "{required_int: 123}\nrequired_string: abc\n"


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


def test_list_entry_no_type():
    cfg = ListConfigNoType({u"mylist": [1, 'a', '', 4]})
    assert cfg.mylist == [1, 'a', '', 4]

    cfg = ListConfigNoType({})
    assert cfg.mylist == []


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


def test_dict_entry_no_type():
    cfg = DictConfigNoType({u"mydict": {u"keya": u"valuea", u"keyb": 1}})
    assert cfg.mydict == {u"keya": u"valuea", u"keyb": 1}

    cfg = DictConfigNoType({})
    assert cfg.mydict == {}


def test_load_config_using_path():
    cfg = base.load_config(BasicConfig, 'test_config.yml',
                           directories=[os.path.dirname(__file__)])
    assert cfg is not None
    assert cfg.required_string == u"abc"
    assert cfg.folder1.subfolder1.required_int == 123


def test_load_config_using_env():
    os.environ['UPAAS_CONFIG_DIR'] = os.path.dirname(__file__)
    cfg = base.load_config(BasicConfig, 'test_config.yml')
    assert cfg is not None
    assert cfg.required_string == u"abc"
    assert cfg.folder1.subfolder1.required_int == 123


def test_load_config_invalid():
    cfg = base.load_config(BasicConfig, os.path.basename(__file__),
                           directories=[os.path.dirname(__file__)])
    assert cfg is None
