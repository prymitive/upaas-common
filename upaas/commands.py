# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import subprocess
import signal
import logging


log = logging.getLogger(__name__)


SAFE_ENVS = [
    'HOME',
    'LOGNAME',
    'USER',
    'TERM',
    'PATH',
    'LANG',
    'LC_ALL',
    'TZ',
    'SHELL',
    'PWD',
]


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
            valid_retcodes=[0], strip_envs=False):
    """
    Execute given command in shell.

    :param timeout: Maximum time (in seconds) command can take to execute, if
                    it takes longer it will be killed. No timeout if None.
    :param cwd: If provided chdir() to this path before executing.
    :param output_loglevel: Logging level at which command output will be
                            logged.
    :param env: Dictionary with environment variables for this command.
    :param valid_retcodes: List of return codes that can be returned by this
                           command. Other return codes will be interpreted as
                           error and exception will be raised.
    :param strip_envs: If True all unsafe env variables will be removed
                       before executing command.
    :returns: tuple -- (return code, output as list of strings)
    """
    def _alarm_handler(signum, frame):
        raise CommandTimeout("Command timeout reached")

    def _cleanup(workdir, original_env):
        if workdir:
            log.debug("Switching back to workdir at '%s'" % workdir)
            os.chdir(workdir)
        for key, value in list(original_env.items()):
            if value:
                log.debug("Restoring original ENV variable %s=%s" % (key,
                                                                     value))
                os.environ[key] = value
            else:
                log.debug("Deleting extra ENV variable %s" % key)
                try:
                    del os.environ[key]
                except KeyError:
                    pass

    log.info("Executing command: %s" % cmd, extra={"force_flush": True})

    wd = None
    if cwd:
        wd = os.getcwd()
        log.info("Changing working directory to '%s'" % cwd)
        os.chdir(cwd)

    original_env = {}
    if strip_envs:
        for ename, evalue in list(os.environ.items()):
            if ename not in (list(env.keys()) + SAFE_ENVS):
                log.debug("Removing unsafe ENV variable %s=%s" % (ename,
                                                                  evalue))
                original_env[ename] = evalue
                del os.environ[ename]

    for ename, evalue in list(env.items()):
        log.debug("Setting ENV variable %s=%s" % (ename, evalue))
        orgval = os.environ.get(ename)
        log.debug("Saving original ENV value %s=%s" % (ename, orgval))
        original_env[ename] = orgval
        os.environ[ename] = evalue

    if timeout:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout)
        log.debug("Timeout for command is %d seconds" % timeout)

    output = []
    log.debug("Running ...")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True)
    try:
        while True:
            retcode = p.poll()
            line = p.stdout.readline().decode('utf-8')
            if line:
                output.append(line)
                log.log(output_loglevel, line.rstrip(os.linesep))
            if retcode is not None:
                break
    except CommandTimeout:
        os.kill(p.pid, signal.SIGKILL)
        _cleanup(wd, original_env)
        raise CommandTimeout("Command timeout reached")
    except KeyboardInterrupt as e:
        if timeout:
            signal.alarm(0)
        os.kill(p.pid, signal.SIGKILL)
        _cleanup(wd, original_env)
        raise CommandFailed(e)
    except Exception:
        signal.alarm(0)
        raise

    if timeout:
        signal.alarm(0)

    _cleanup(wd, original_env)

    if retcode not in valid_retcodes:
        msg = "Command failed with status %d" % retcode
        log.error(msg)
        raise CommandFailed(msg)

    return retcode, output
