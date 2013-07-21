# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


def bytes_to_human(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if 1024.0 > num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def select_best_version(config, metadata):
    #TODO right now we just pick the first version from the list
    # that is described in configuration, make it more smart
    # so that we pick up the *highest* supported version
    for version in metadata.interpreter.versions:
        try:
            _ = config.interpreters[metadata.interpreter.type][version]
            return version
        except KeyError:
            pass
