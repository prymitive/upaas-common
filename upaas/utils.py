# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import shutil
import logging

from upaas import commands


log = logging.getLogger(__name__)


def bytes_to_human(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if 1024.0 > num > -1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'EB')


def version_to_tuple(v):
    return tuple(map(int, (v.split("."))))


def version_tuple_to_string(version):
    return '.'.join(str(v) for v in version)


def version_fuzzy_compare(v1, v2):
    """
    Fuzzy version matching, checks if given 2 version strings are equal.
    It compares most major parts of each version.
    Example:
    5 == 5.4 => true
    5.3 == 5.4 => false
    5.1.4 == 5.1 => true
    """
    v1t = version_to_tuple(v1)
    v2t = version_to_tuple(v2)
    match_items = min(len(v1t), len(v2t))
    return v1t[0:match_items] == v2t[0:match_items]


def supported_versions(config, metadata):
    """
    Return list of versions from metadata that are supported localy.
    """
    valid_versions = {}
    for version in metadata.interpreter.versions:
        for iversion in config.interpreters[metadata.interpreter.type]:
            if iversion.lower() != 'any':
                if version_fuzzy_compare(version, iversion):
                    valid_versions[iversion] = version_to_tuple(iversion)
    return valid_versions


def select_best_version(config, metadata):
    """
    Return highest supported version or None.
    """
    valid_versions = supported_versions(config, metadata)
    if valid_versions:
        return version_tuple_to_string(
            sorted(list(valid_versions.values()), reverse=True)[0])


def rmdirs(*args):
    for directory in args:
        if os.path.isdir(directory):
            log.info("Removing directory '%s'" % directory)
            shutil.rmtree(directory)


def umount_filesystems(workdir, timeout=60):
    mounts = []
    if os.path.isfile("/proc/mounts"):
        with open("/proc/mounts") as mtab:
            for line in mtab:
                try:
                    mount = line.split()[1]
                except IndexError:
                    pass
                else:
                    if mount.startswith(workdir.rstrip('/') + '/'):
                        mounts.append(mount)
    for mount in mounts:
        log.info("Found mounted filesystem at '%s', unmounting" % mount)
        commands.execute("umount %s" % mount, timeout=timeout)
