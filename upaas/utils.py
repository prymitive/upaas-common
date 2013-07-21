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


def version_to_tuple(v):
    return tuple(map(int, (v.split("."))))


def select_best_version(config, metadata):
    """
    Return highest supported version or None.
    """
    valid_versions = {}

    for version in metadata.interpreter.versions:
        try:
            _ = config.interpreters[metadata.interpreter.type][version]
        except KeyError:
            pass
        else:
            valid_versions[version_to_tuple(version)] = version

    if valid_versions:
        return valid_versions[sorted(valid_versions.keys(), reverse=True)[0]]
