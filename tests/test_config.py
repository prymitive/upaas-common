# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from upaas.config import base
from upaas.compat import unicode


class BasicConfig(base.Config):
    schema = {
        "required_string": base.StringEntry(required=True),
        "folder1": {
            "subfolder1": {
                "required_int": base.IntegerEntry(required=True)
            },
            "optional_int": base.IntegerEntry(),
        },
        "chained": {
            "included": base.BooleanEntry()
        }
    }


class InvalidConfig(base.Config):
    schema = {
        "valid": base.IntegerEntry(),
        "invalid": int(),
    }


class ListConfig(base.Config):
    schema = {
        "mylist": base.ListEntry(value_type=int)
    }


class ListConfigNoType(base.Config):
    schema = {
        "mylist": base.ListEntry()
    }


class DictConfig(base.Config):
    schema = {
        "mydict": base.DictEntry(value_type=unicode)
    }


class DictConfigNoType(base.Config):
    schema = {
        "mydict": base.DictEntry()
    }


class BoolConfig(base.Config):
    schema = {
        "mybool_false": base.BooleanEntry(),
        "mybool_true": base.BooleanEntry(),
        "mybool_missing": base.BooleanEntry(),
    }


class IntConfig(base.Config):
    schema = {
        "int_with_min": base.IntegerEntry(min_value=10),
        "int_with_max": base.IntegerEntry(max_value=10),
        "int_with_min_max": base.IntegerEntry(min_value=10, max_value=20),
        "int_with_single_value": base.IntegerEntry(min_value=5, max_value=5),
    }


class NestedListBasicConfig(base.Config):
    schema = {
        "subconfig": base.ConfigListEntry(BasicConfig)
    }


class NestedListBoolConfig(base.Config):
    schema = {
        "subconfig": base.ConfigListEntry(BoolConfig)
    }


class NestedDictBasicConfig(base.Config):
    schema = {
        "subconfig": base.ConfigDictEntry(BasicConfig)
    }


class NestedDictBoolConfig(base.Config):
    schema = {
        "subconfig": base.ConfigDictEntry(BoolConfig)
    }


def test_empty():
    with pytest.raises(base.ConfigurationError):
        BasicConfig({})


def test_required_entries_from_dict():
    cfg = BasicConfig({
        "required_string": "abc",
        "folder1": {
            "subfolder1": {
                "required_int": 123
            }
        }
    })
    assert cfg.required_string == "abc"
    assert cfg.folder1.subfolder1.required_int == 123
    with pytest.raises(AttributeError):
        print((cfg.folder1.optional_int))


def test_required_entries_from_file():
    cfg = BasicConfig.from_file(os.path.join(os.path.dirname(__file__),
                                             "test_config.yml"))
    assert cfg.required_string == "abc"
    assert cfg.folder1.subfolder1.required_int == 123
    with pytest.raises(AttributeError):
        print((cfg.folder1.optional_int))
    assert cfg.chained.included is True


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
        "chained": {
            "included": True
        },
        "required_string": "abc",
        "folder1": {
            "subfolder1": {
                "required_int": 123
            }
        }
    }
    cfg = BasicConfig(options)
    assert cfg.dump() == options


def test_dump_string():
    options = {
        "required_string": "abc",
        "folder1": {
            "subfolder1": {
                "required_int": 123
            }
        }
    }
    cfg = BasicConfig(options)
    assert cfg.dump_string() == "folder1:\n  subfolder1: " \
                                "{required_int: 123}\nrequired_string: abc\n"


def test_default_value():
    class LocalConfig(base.Config):
        schema = {"myitem": base.StringEntry(default="default value")}

    cfg = LocalConfig({})
    assert cfg.myitem == "default value"


def test_list_entry_valid():
    cfg = ListConfig({"mylist": [1, 2, 3, 4]})
    assert cfg.mylist == [1, 2, 3, 4]

    cfg = ListConfig({})
    assert cfg.mylist == []


def test_list_entry_invalid():
    with pytest.raises(base.ConfigurationError):
        ListConfig({"mylist": {"a": 1}})

    with pytest.raises(base.ConfigurationError):
        ListConfig({"mylist": ["not an int", 1]})


def test_list_entry_no_type():
    cfg = ListConfigNoType({"mylist": [1, 'a', '', 4]})
    assert cfg.mylist == [1, 'a', '', 4]

    cfg = ListConfigNoType({})
    assert cfg.mylist == []


def test_dict_entry_valid():
    cfg = DictConfig({"mydict": {"keya": "valuea", "keyb": "valueb"}})
    assert cfg.mydict == {"keya": "valuea", "keyb": "valueb"}

    cfg = DictConfig({})
    assert cfg.mydict == {}


def test_dict_entry_invalid():
    with pytest.raises(base.ConfigurationError):
        DictConfig({"mydict": [1]})

    with pytest.raises(base.ConfigurationError):
        DictConfig({"mydict": {"not an unicode": 1}})


def test_dict_entry_no_type():
    cfg = DictConfigNoType({"mydict": {"keya": "valuea", "keyb": 1}})
    assert cfg.mydict == {"keya": "valuea", "keyb": 1}

    cfg = DictConfigNoType({})
    assert cfg.mydict == {}


def test_init_config_invalid_content():
    with pytest.raises(base.ConfigurationError):
        BasicConfig(123)


def test_init_config_invalid_schema():
    cfg = InvalidConfig({"valid": 1, "invalid": 2})
    assert cfg.valid == 1
    with pytest.raises(AttributeError):
        cfg.invalid == 2


def test_load_config_using_path():
    cfg = base.load_config(BasicConfig, 'test_config.yml',
                           directories=[os.path.dirname(__file__)])
    assert cfg is not None
    assert cfg.required_string == "abc"
    assert cfg.folder1.subfolder1.required_int == 123


def test_load_config_using_env():
    os.environ['UPAAS_CONFIG_DIR'] = os.path.dirname(__file__)
    cfg = base.load_config(BasicConfig, 'test_config.yml')
    assert cfg is not None
    assert cfg.required_string == "abc"
    assert cfg.folder1.subfolder1.required_int == 123


def test_load_config_invalid():
    cfg = base.load_config(BasicConfig, os.path.basename(__file__),
                           directories=[os.path.dirname(__file__)])
    assert cfg is None


def test_load_config_missing():
    cfg = base.load_config(BasicConfig, 'non existing file',
                           directories=['/non/existing/dir'])
    assert cfg is None


def test_bool_entry():
    cfg = BoolConfig({"mybool_false": False, "mybool_true": True})
    assert cfg.mybool_false is False
    assert cfg.mybool_true is True

    with pytest.raises(AttributeError):
        _ = cfg.mybool_missing


def test_bool_entry_invalid():
    with pytest.raises(base.ConfigurationError):
        BoolConfig({"mybool_false": 1})
    with pytest.raises(base.ConfigurationError):
        BoolConfig({"mybool_false": 'a'})


def test_integer_invalid_schema():
    with pytest.raises(ValueError):
        class InvalidIntConfig(base.Config):
            schema = {
                "int": base.IntegerEntry(min_value=2, max_value=1),
            }


def test_integer_min_value_valid():
    cfg = IntConfig({"int_with_min": 10})
    assert cfg.int_with_min == 10

    cfg = IntConfig({"int_with_min": 20})
    assert cfg.int_with_min == 20


def test_integer_min_value_invalid():
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_min": 5})


def test_integer_max_value_valid():
    cfg = IntConfig({"int_with_max": 1})
    assert cfg.int_with_max == 1

    cfg = IntConfig({"int_with_max": 10})
    assert cfg.int_with_max == 10


def test_integer_max_value_invalid():
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_max": 15})


def test_integer_min_max_value_valid():
    cfg = IntConfig({"int_with_min_max": 10})
    assert cfg.int_with_min_max == 10

    cfg = IntConfig({"int_with_min_max": 20})
    assert cfg.int_with_min_max == 20


def test_integer_min_max_value_invalid():
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_min_max": 9})
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_min_max": 21})


def test_integer_single_value_valid():
    cfg = IntConfig({"int_with_single_value": 5})
    assert cfg.int_with_single_value == 5


def test_integer_single_value_invalid():
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_single_value": 4})
    with pytest.raises(base.ConfigurationError):
        _ = IntConfig({"int_with_single_value": 6})


def test_nested_list_config_valid():
    options = [
        {
            "required_string": "a1",
            "folder1": {
                "subfolder1": {
                    "required_int": 123
                }
            }
        },
        {
            "required_string": "b2",
            "folder1": {
                "subfolder1": {
                    "required_int": 456
                }
            }
        },
        {
            "required_string": "c3",
            "folder1": {
                "subfolder1": {
                    "required_int": 789
                }
            }
        },
    ]
    cfg = NestedListBasicConfig({"subconfig": options})
    assert cfg.subconfig[0].required_string == "a1"
    assert cfg.subconfig[0].folder1.subfolder1.required_int == 123
    assert cfg.subconfig[1].required_string == "b2"
    assert cfg.subconfig[1].folder1.subfolder1.required_int == 456
    assert cfg.subconfig[2].required_string == "c3"
    assert cfg.subconfig[2].folder1.subfolder1.required_int == 789


def test_nested_list_config_dump():
    options = {
        "required_string": "abc",
        "folder1": {
            "subfolder1": {
                "required_int": 123
            }
        }
    }
    cfg = NestedListBasicConfig({"subconfig": [options, options, options]})
    dump = cfg.dump()
    assert isinstance(dump['subconfig'], list)
    assert len(dump['subconfig']) == 3
    assert dump['subconfig'][0]['required_string'] == 'abc'


def test_nested_list_config_empty():
    cfg = NestedListBoolConfig({"subconfig": []})
    assert cfg.subconfig == []


def test_nested_list_config_type_invalid():
    with pytest.raises(base.ConfigurationError):
        NestedListBoolConfig({"subconfig": {}})


def test_nested_list_config_value_invalid():
    with pytest.raises(base.ConfigurationError):
        NestedListBoolConfig({"subconfig": [{"mybool_false": 1}]})


def test_nested_dict_config_valid():
    options = {
        "a": {
            "required_string": "abc",
            "folder1": {
                "subfolder1": {
                    "required_int": 123
                }
            }
        },
        "b": {
            "required_string": "def",
            "folder1": {
                "subfolder1": {
                    "required_int": 456
                }
            }
        }
    }
    cfg = NestedDictBasicConfig({"subconfig": options})
    assert cfg.subconfig['a'].required_string == "abc"
    assert cfg.subconfig['a'].folder1.subfolder1.required_int == 123
    assert cfg.subconfig['b'].required_string == "def"
    assert cfg.subconfig['b'].folder1.subfolder1.required_int == 456


def test_nested_dict_config_empty():
    cfg = NestedDictBoolConfig({"subconfig": {}})
    assert cfg.subconfig == {}


def test_nested_dict_config_type_invalid():
    with pytest.raises(base.ConfigurationError):
        NestedDictBoolConfig({"subconfig": []})


def test_nested_dict_config_value_invalid():
    with pytest.raises(base.ConfigurationError):
        NestedDictBoolConfig({"subconfig": {'a': {"mybool_false": 1}}})
