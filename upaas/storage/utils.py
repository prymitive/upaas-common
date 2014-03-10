# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from upaas.config.base import ConfigurationError

log = logging.getLogger(__name__)


def find_storage_handler(name, settings=None):
    """
    Will try to find storage handler class user has set in configuration,
    create instance of it and return that instance.
    """
    storage_handler = None
    storage_module = ".".join(name.split(".")[0:len(name.split(".")) - 1])
    storage_class = name.split(".")[len(name.split(".")) - 1]
    try:
        exec("from %s import %s as storage_handler" % (
            storage_module, storage_class))
    except ImportError:
        msg = "Storage handler '%s' could not be loaded" % name
        log.error(msg)
        raise ConfigurationError(msg)
    else:
        log.info("Loaded storage handler '%s', initializing with settings: "
                 "%s" % (name, (settings or {}).keys()))
        try:
            return storage_handler(settings)
        except ConfigurationError:
            msg = "Storage handler failed to initialize with given " \
                  "configuration"
            log.error(msg)
            raise ConfigurationError(msg)
