# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import subprocess
import signal
import logging


log = logging.getLogger(__name__)


class CommandTimeoutAlarm(Exception):
    pass


def execute(cmd, timeout=None, cwd=None, output_loglevel=logging.DEBUG, env=[]):
    """
    Execute given command in shell.

    :param timeout: Maximum time (in seconds) command can take to execute, if it
                    takes longer it will be killed. No timeout if None.
    :param cwd: If provided chdir() to this path before executing.
    :param output_loglevel: Logging level at which command output will be
                            logged.
    :raises: CommandTimeoutAlarm
    """
    def _alarm_handler(signum, frame):
        raise CommandTimeoutAlarm

    if cwd:
        wd = os.getcwd()
        log.info(u"Changing working directory to '%s'" % cwd)
        os.chdir(cwd)

    for e in env:
        ename = e.split("=")[0]
        evalue = "=".join(e.split("=")[1:])
        log.info(u"Setting ENV variable %s=%s" % (ename, evalue))
        os.environ[ename] = evalue

    if timeout:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True)
    try:
        while True:
            retcode = p.poll()
            line = p.stdout.readline()
            if line:
                log.log(output_loglevel, line.rstrip(os.linesep))
            if retcode is not None:
                break
    except CommandTimeoutAlarm:
        os.kill(p.pid, signal.SIGKILL)
        if cwd:
            os.chdir(wd)
        raise CommandTimeoutAlarm

    if cwd:
        os.chdir(wd)

    return retcode
