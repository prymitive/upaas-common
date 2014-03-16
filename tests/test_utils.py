# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.utils import version_fuzzy_compare


def test_version_fuzzy_compare():
    assert version_fuzzy_compare('5', '5.1') is True
    assert version_fuzzy_compare('5.1.4', '5.1') is True
    assert version_fuzzy_compare('5.1', '5.2') is False
    assert version_fuzzy_compare('5.1.2', '5.2') is False
