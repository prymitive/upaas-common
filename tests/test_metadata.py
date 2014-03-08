# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config.metadata import MetadataConfig


MetadataDetect = '''
interpreter:
  type: ruby
  versions:
    - 2.1.0

repository:
  clone: echo "Cloned"
  update: echo "Updated"
'''


MetadataManual = '''
interpreter:
  type: ruby
  versions:
    - 2.1.0

repository:
  clone: echo "Cloned"
  update: echo "Updated"
  info:
    revision: revision cmd
    author: author cmd
'''


def test_detect_revision():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.info.revision == ['git rev-parse HEAD']


def test_manual_revision():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.info.revision == ['revision cmd']


def test_detect_author():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.info.author == ["git log -1 --pretty='%aN <%aE>'"]


def test_manual_author():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.info.author == ['author cmd']
