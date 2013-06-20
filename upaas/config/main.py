# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging

from upaas.config import base


log = logging.getLogger()


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
    """
    Try to load main config, return None in case of errors.
    """

    upaas_config = None

    for path in ['upaas.yml', '/etc/upaas/upaas.yml', '/etc/upaas.yml']:
        if os.path.isfile(path):
            try:
                upaas_config = UPaaSConfig.from_file(path)
            except base.ConfigurationError:
                log.error("Invalid config file at %s" % path)
                return None
            else:
                break

    if not upaas_config:
        log.error("No config file found")

    return upaas_config
