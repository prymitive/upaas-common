# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging

from upaas import commands


log = logging.getLogger(__name__)


def pack_tar(dir, archive_path, timeout=None):
    """
    Pack files at given directory into tar archive.

    :param dir: Directory which content should be packed.
    :param archive_path: Path at which tar archive file will be created.
    :param timeout: Timeout in seconds.
    """
    def _cleanup(archive_path):
        try:
            log.debug(u"Removing incomplete tar archive '%s' if "
                      u"present" % archive_path)
            os.remove(archive_path)
        except OSError:
            pass

    try:
        commands.execute("tar -czpf %s *" % archive_path, timeout=timeout,
                         cwd=dir)
    except commands.CommandTimeoutAlarm:
        log.error(u"Tar command was taking too long and it was killed")
        _cleanup(archive_path)
        return False
    except commands.CommandFailed:
        log.error(u"Tar command failed")
        _cleanup(archive_path)
        return False
    else:
        return True


def unpack_tar(archive_path, destination, timeout=None):
    """
    Unpack tar archive in destination directory.

    :param archive_path: Path to tar file.
    :param destination: Destination directory in which we will unpack tar file.
    :param timeout: Timeout in seconds.
    """
    try:
        commands.execute("tar -xzpf %s" % archive_path, timeout=timeout,
                         cwd=dir)
    except commands.CommandTimeoutAlarm:
        log.error(u"Tar command was taking too long and it was killed")
        return False
    except commands.CommandFailed:
        log.error(u"Tar command failed")
        return False
    else:
        return True
