# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import shutil
import tempfile

import pytest
from _pytest.monkeypatch import monkeypatch


@pytest.fixture(scope="function")
def empty_dir(request):
    directory = tempfile.mkdtemp(prefix="upaas_testdir_")

    def cleanup():
        shutil.rmtree(directory)
    request.addfinalizer(cleanup)

    return directory


@pytest.fixture(scope="function")
def empty_file(request):
    path = tempfile.mkstemp(prefix="upaas_testfile_")[1]

    def cleanup():
        os.remove(path)
    request.addfinalizer(cleanup)

    return path


@pytest.fixture(scope="function")
def builder_config(request):

    directory = tempfile.mkdtemp(prefix="upaas_testdir_")

    class BuilderConfig:

        class paths:
            workdir = '/tmp'
            apps = '/tmp'
            vassals = '/tmp'

        class storage:
            handler = 'upaas.storage.local.LocalStorage'
            settings = {'dir': directory}

        class bootstrap:
            timelimit = 10
            maxage = 999
            env = {'LANG': 'C.UTF-8'}
            commands = ['/bin/touch bootstrapped.txt']
            packages = ['fakepackage']

        class commands:
            timelimit = 10

            class install:
                env = {'FAKEKEY': 'FAKEVALUE'}
                cmd = '/bin/echo'

            class uninstall:
                env = {'FAKEKEY': 'FAKEVALUE'}
                cmd = '/bin/echo'

        class apps:
            uid = 1000
            gid = 1000
            home = '/tmp'

        interpreters = {
            'ruby': {
                'any': {
                    'env': {},
                    'packages': ['fakerubypackage'],
                },
                '1.8.7': {
                    'packages': ['fakerubyversionpackage'],
                    'actions': {
                        'setup': {
                            'interpreter': ['/bin/echo interpreter action']
                        }
                    }
                }
            }
        }

    def cleanup():
        shutil.rmtree(directory)
    request.addfinalizer(cleanup)

    return BuilderConfig()


@pytest.fixture(scope="function")
def mock_chroot(request):
    class MockChroot(object):
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            pass

        def __exit__(self, type, value, traceback):
            pass

    mpatch = monkeypatch()
    mpatch.setattr('upaas.chroot.Chroot', MockChroot)
    mpatch.setattr('upaas.builder.builder.Chroot', MockChroot)
    request.addfinalizer(mpatch.undo)


@pytest.fixture(scope="function")
def mock_build_commands(request):
    from upaas.commands import execute as real_execute

    def mock_execute(cmd, *args, **kwargs):
        executable = cmd.split(' ')[0]
        if executable in ['git', 'chown', 'gem', 'rake', 'bundle']:
            return 0, []
        else:
            return real_execute(cmd, *args, **kwargs)

    mpatch = monkeypatch()
    mpatch.setattr('upaas.commands.execute', mock_execute)
    request.addfinalizer(mpatch.undo)
