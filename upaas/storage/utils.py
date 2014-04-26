# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from upaas.config.base import ConfigurationError

log = logging.getLogger(__name__)


def import_handler(module_name, cls_name):
    """
    Import class from module by name.
    """
    mod = __import__(module_name)
    components = module_name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return getattr(mod, cls_name)


def find_storage_handler(name, settings=None):
    """
    Will try to find storage handler class user has set in configuration,
    create instance of it and return that instance.
    """
    storage_module = ".".join(name.split(".")[0:len(name.split(".")) - 1])
    storage_class = name.split(".")[len(name.split(".")) - 1]
    log.debug("Trying to import '%s' from '%s'" % (storage_class,
                                                   storage_module))
    try:
        storage_handler = import_handler(storage_module, storage_class)
    except ImportError:
        msg = "Storage handler '%s' could not be loaded" % name
        log.error(msg)
        raise ConfigurationError(msg)
    else:
        log.debug("Loaded storage handler '%s', initializing with settings: "
                  "%s" % (name, (settings or {}).keys()))
        try:
            return storage_handler(settings)
        except ConfigurationError:
            msg = "Storage handler failed to initialize with given " \
                  "configuration"
            log.error(msg)
            raise ConfigurationError(msg)
