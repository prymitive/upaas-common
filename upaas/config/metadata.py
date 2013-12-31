# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config import base


class MetadataConfig(base.Config):

    schema = {
        "os": base.WildcardEntry(),
        "interpreter": {
            "type": base.StringEntry(required=True),
            "versions": base.ListEntry(str),
            "settings": base.DictEntry(value_type=str),
        },
        "repository": {
            "env": base.DictEntry(value_type=str),
            "clone": base.ScriptEntry(required=True),
            "update": base.ScriptEntry(required=True),
            "info": base.ScriptEntry(required=True),
            "changelog": base.ScriptEntry(required=True),
        },
        "env": base.DictEntry(value_type=str),
        "actions": {
            "setup": {
                "before": base.ScriptEntry(),
                "main": base.ScriptEntry(),
                "after": base.ScriptEntry(),
            }
        },
        "files": base.DictEntry(value_type=str),
        "uwsgi": {
            "settings": base.ListEntry(value_type=str)
        }
    }
