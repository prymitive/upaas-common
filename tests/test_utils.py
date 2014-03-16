# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas import utils


def test_version_fuzzy_compare():
    assert utils.version_fuzzy_compare('5', '5.1') is True
    assert utils.version_fuzzy_compare('5.1.4', '5.1') is True
    assert utils.version_fuzzy_compare('5.1', '5.2') is False
    assert utils.version_fuzzy_compare('5.1.2', '5.2') is False


def test_bytes_to_human():
    assert utils.bytes_to_human(1) == '1.0 bytes'
    assert utils.bytes_to_human(1024) == '1.0 KB'
    assert utils.bytes_to_human(1024 * 1.5) == '1.5 KB'
    assert utils.bytes_to_human(1024 * 1024 * 4.4) == '4.4 MB'
    assert utils.bytes_to_human(1024 * 1024 * 1024 * 16.9) == '16.9 GB'
    assert utils.bytes_to_human(1024 * 1024 * 1024 * 1024 * 1.06) == '1.1 TB'
    assert utils.bytes_to_human(1024 * 1024 * 1024 * 1024 * 1024) == '1.0 PB'
    assert utils.bytes_to_human(1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 9) \
        == '9.0 EB'


def test_version_to_tuple():
    assert utils.version_to_tuple('1') == (1,)
    assert utils.version_to_tuple('1.9') == (1, 9)
    assert utils.version_to_tuple('1.4.5') == (1, 4, 5)


def test_version_tuple_to_string():
    assert utils.version_tuple_to_string((1,)) == '1'
    assert utils.version_tuple_to_string((1, 9)) == '1.9'
    assert utils.version_tuple_to_string((1, 4, 5)) == '1.4.5'
