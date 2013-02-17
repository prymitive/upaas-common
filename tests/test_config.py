# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging

import pytest

from upaas import config


class BasicConfig(config.Config):
    schema = {
        "required_string": config.StringEntry(required=True),
        "folder1": {
            "subfolder1": {
                "required_int": config.IntegerEntry(required=True)
            },
            "optional_int": config.IntegerEntry(),
        }
    }


def test_empty():
    with pytest.raises(config.ConfigurationError):
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
