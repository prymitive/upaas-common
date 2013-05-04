# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas import config


class MetadataConfig(config.Config):

    schema = {
        "os": config.WildcardEntry(),
        "interpreter": {
            "type": config.StringEntry(required=True),
            "versions": config.ListEntry(unicode),
        },
        "repository": {
            "env": config.DictEntry(value_type=unicode),
            "clone": config.ScriptEntry(required=True),
            "update": config.ScriptEntry(required=True),
            "info": config.ScriptEntry(required=True),
            "changelog": config.ScriptEntry(required=True),
        },
        "env": config.DictEntry(value_type=unicode),
        "actions": {
            "setup": {
                "before": config.ScriptEntry(),
                "main": config.ScriptEntry(),
                "after": config.ScriptEntry(),
            }
        }
    }
