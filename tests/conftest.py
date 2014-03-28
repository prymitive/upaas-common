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
