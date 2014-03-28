# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import time
import signal
import shutil
import logging

from upaas.commands import execute
from upaas.utils import umount_filesystems

log = logging.getLogger(__name__)


def directory_pids(directory):
    """
    List pid of all processes running inside given directory.
    List will contain integers and will use ascending sorting.

    :param directory: Directory to scan for running processes.
    :type directory: str

    :returns: list of int -- [134, 245, 673, 964]
    """
    log.debug("Scanning for processes running in %s" % directory)
    ret = set()
    if os.path.exists(directory):
        (rcode, output) = execute('lsof -t +d %s' % directory,
                                  valid_retcodes=[0, 1])
        if output:
            for line in output:
                try:
                    ret.add(int(line))
                except ValueError:
                    log.debug("Could not convert PID value to int: "
                              "'%s'" % line)
            return sorted(list(ret))
    else:
        log.debug("No such directory: %s" % directory)
    return []


def is_pid_running(pid):
    """
    Check if we have running process with given PID.

    :param pid: PID of process to check.
    :type pid: int
    :returns: bool -- True if given PID is running, False otherwise.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def get_pid_command(pid):
    """
    Get command line of process with given PID. If command line cannot be
    found, then None is returned.

    :param pid: PID of process to lookup.
    :type pid: int

    :returns: str or None
    """
    try:
        with open("/proc/%d/cmdline" % pid, 'r') as proc:
            ret = proc.read()
        return ret or None
    except Exception as e:
        log.debug("Exception during /proc file parsing: %s" % e)


def wait_for_pid(pid, kill_after=600):
    """
    Wait for process to die, if it takes more than *kill_after* seconds than
    kill this process. Process is killed by sending SIGTERM and waiting 10
    seconds, if it's alive after that time SIGKILL is sent.

    :param pid: PID of process we wait to die.
    :type pid: int

    :param kill_after: Number of seconds to wait for process to die, after this
                       time it will be killed. Default is 600 seconds.
    :type kill_after: int
    """
    elapsed = 0
    while True:
        if is_pid_running(pid):
            log.debug("Waiting for pid %s to terminate (%s seconds "
                      "elapsed)" % (pid, elapsed))
            time.sleep(1)
            elapsed += 1
            if elapsed >= kill_after:
                log.info("%s seconds elapsed, killing process %s" % (elapsed,
                                                                     pid))
                os.kill(pid, signal.SIGKILL)
                elapsed = 0
                kill_after = 10
        else:
            break


def kill_pid(pid, timeout=60):
    """
    Kill running process by sending SIGTERM. If this process does not terminate
    after *timeout* seconds than it will be killed with SIGKILL signal.

    :param timeout: Number of seconds to wait before sending SIGKILL.
    :type timeout: int
    """
    if pid == os.getpid():
        log.debug("%d is my own PID, will not kill" % pid)
        return
    cmdline = get_pid_command(pid)
    log.info("Sending SIGTERM to %s [%s]" % (pid, cmdline or 'N/A'))
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        log.debug("PID %s already died" % pid)
    else:
        wait_for_pid(pid, kill_after=timeout)


def kill_and_remove_dir(directory):
    """
    Kill all processes running inside given directory and remove it.
    Used mostly for removing temporary directories.
    """
    found = True
    while found:
        for pid in directory_pids(directory):
            kill_pid(pid)
        else:
            found = False

    try:
        umount_filesystems(directory)
    except Exception as e:
        log.error("Error while unmounting filesystem inside "
                  "package: %s" % e)
    else:
        log.info("Removing directory: %s" % directory)
        shutil.rmtree(directory.encode('utf-8'))
