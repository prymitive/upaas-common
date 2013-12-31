# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from upaas.config.base import ConfigurationError

log = logging.getLogger(__name__)


def find_storage_handler(config):
    """
    Will try to find storage handler class user has set in configuration,
    create instance of it and return that instance.
    """
    storage_handler = None
    name = config.storage.handler
    storage_module = ".".join(name.split(".")[0:len(name.split(".")) - 1])
    storage_class = name.split(".")[len(name.split(".")) - 1]
    try:
        exec("from %s import %s as storage_handler" % (
            storage_module, storage_class))
    except ImportError:
        msg = "Storage handler '%s' could not be " \
              "loaded" % config.storage.handler
        log.error(msg)
        raise ConfigurationError(msg)
    else:
        log.info("Loaded storage handler: "
                 "%s" % config.storage.handler)
        try:
            return storage_handler(config.storage.settings)
        except ConfigurationError:
            msg = "Storage handler failed to initialize with given " \
                  "configuration"
            log.error(msg)
            raise ConfigurationError(msg)
