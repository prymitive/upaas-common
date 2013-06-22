# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config import base


class UPaaSConfig(base.Config):

    schema = {
        "mongodb": {
            "host": base.StringEntry(required=True),
            "port": base.IntegerEntry(default=27017),
            "username": base.StringEntry(),
            "password": base.StringEntry(),
            "database": base.StringEntry(default="upaas"),
        },
    }


def load_main_config():
    return base.load_config(UPaaSConfig, 'upaas.yml')
