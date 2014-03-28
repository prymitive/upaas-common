# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas.storage.utils import find_storage_handler
from upaas.config.base import ConfigurationError


def test_find_storage_invalid():
    with pytest.raises(ConfigurationError):
        find_storage_handler('invalid.storage.module.Handler')
