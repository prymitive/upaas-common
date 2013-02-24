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


class CommandError(Exception):
    """
    Generic command execution error.
    """
    pass


class CommandTimeout(CommandError):
    """
    Command was executing longer than allowed.
    """
    pass


class CommandFailed(CommandError):
    """
    Command exited with return code indicating error.
    """
    pass


def execute(cmd, timeout=None, cwd=None, output_loglevel=logging.DEBUG, env={},
            valid_retcodes=[0]):
    """
    Execute given command in shell.

    :param timeout: Maximum time (in seconds) command can take to execute, if
                    it takes longer it will be killed. No timeout if None.
    :param cwd: If provided chdir() to this path before executing.
    :param output_loglevel: Logging level at which command output will be
                            logged.
    :param valid_retcodes: List of return codes that can be returned by this
                           command. Other return codes will be interpreted as
                           error and exception will be raised.
    :returns: tuple -- (return code, output as list of strings)
    """
    def _alarm_handler(signum, frame):
        raise CommandTimeout

    log.info(u"About to execute command: %s" % cmd)

    if cwd:
        wd = os.getcwd()
        log.info(u"Changing working directory to '%s'" % cwd)
        os.chdir(cwd)

    for ename, evalue in env.items():
        log.info(u"Setting ENV variable %s=%s" % (ename, evalue))
        os.environ[ename] = evalue

    if timeout:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)
        log.info(u"Timeout for command is %d seconds" % timeout)

    output = []
    log.info(u"Running ...")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True)
    try:
        while True:
            retcode = p.poll()
            line = p.stdout.readline()
            if line:
                output.append(line)
                log.log(output_loglevel, line.rstrip(os.linesep))
            if retcode is not None:
                break
    except CommandTimeout:
        os.kill(p.pid, signal.SIGKILL)
        if cwd:
            os.chdir(wd)
        raise CommandTimeout
    except KeyboardInterrupt:
        os.kill(p.pid, signal.SIGKILL)
        if cwd:
            os.chdir(wd)
        raise CommandFailed

    if cwd:
        os.chdir(wd)

    if retcode not in valid_retcodes:
        log.error(u"Command failed with status %d" % retcode)
        raise CommandFailed

    return retcode, output
