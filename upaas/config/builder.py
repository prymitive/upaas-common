# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config import base


class BuilderConfig(base.Config):

    schema = {
        "paths": {
            "workdir": base.FSPathEntry(required=True, must_exist=True),
        },
        "storage": {
            "handler": base.StringEntry(required=True),
            "settings": base.WildcardEntry(),
        },
        "bootstrap": {
            "timelimit": base.IntegerEntry(required=True),
            "env": base.DictEntry(value_type=unicode),
            "commands": base.ScriptEntry(required=True),
        },
        "commands": {
            "timelimit": base.IntegerEntry(required=True),
            "install": {
                "env": base.DictEntry(value_type=unicode),
                "cmd": base.StringEntry(required=True),
            },
            "uninstall": {
                "env": base.DictEntry(value_type=unicode),
                "cmd": base.StringEntry(required=True),
            },
        },
        "interpreters": base.WildcardEntry(),
    }
