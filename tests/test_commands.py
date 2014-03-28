# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas import commands

import pytest


def test_failed_command():
    with pytest.raises(commands.CommandFailed):
        commands.execute("non existing command")


def test_cwd_and_output(empty_dir):
    _, output = commands.execute("pwd", cwd=empty_dir)
    assert output == [empty_dir + "\n"]


def test_timeout():
    with pytest.raises(commands.CommandTimeout):
        commands.execute("sleep 2", timeout=1)


def test_return_code():
    rcode, _ = commands.execute("exit 123", valid_retcodes=[123])
    assert rcode == 123


def test_env_and_output():
    _, output = commands.execute("echo $MYENV", env={"MYENV": "MYVALUE"})
    assert output == ["MYVALUE\n"]
