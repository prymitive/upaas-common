# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os

import pytest

from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder


@pytest.mark.usefixtures("mock_chroot", "mock_build_commands")
def test_builder(builder_config):
    metadata_path = os.path.join(os.path.dirname(__file__),
                                 'mock_metadata.yml')
    metadata = MetadataConfig.from_file(metadata_path)
    builder = Builder(builder_config, metadata)
    for build_result in builder.build_package():
        continue
    assert build_result.progress == 100
    assert build_result.parent is None
    assert build_result.interpreter_version == '1.8.7'
    assert build_result.filename
    assert build_result.checksum
    assert build_result.bytes > 0
