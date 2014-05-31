# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas.config.base import ConfigurationError
from upaas.utils import load_handler


def test_find_storage_invalid():
    with pytest.raises(ConfigurationError):
        load_handler('invalid.storage.module.Handler')
