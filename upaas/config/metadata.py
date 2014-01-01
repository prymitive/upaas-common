# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config import base
from upaas.compat import unicode


class MetadataConfig(base.Config):

    schema = {
        "os": base.WildcardEntry(),
        "interpreter": {
            "type": base.StringEntry(required=True),
            "versions": base.ListEntry(unicode),
            "settings": base.DictEntry(value_type=unicode),
        },
        "repository": {
            "env": base.DictEntry(value_type=unicode),
            "clone": base.ScriptEntry(required=True),
            "update": base.ScriptEntry(required=True),
            "info": base.ScriptEntry(required=True),
            "changelog": base.ScriptEntry(required=True),
        },
        "env": base.DictEntry(value_type=unicode),
        "actions": {
            "setup": {
                "before": base.ScriptEntry(),
                "main": base.ScriptEntry(),
                "after": base.ScriptEntry(),
            }
        },
        "files": base.DictEntry(value_type=unicode),
        "uwsgi": {
            "settings": base.ListEntry(value_type=unicode)
        }
    }
