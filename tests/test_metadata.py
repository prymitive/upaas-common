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
  revision:
    id: revision id cmd
    author: author cmd
    date: date cmd
    description: description cmd
    changelog: changelog cmd
'''


def test_revision_detect():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.revision.id() == 'git log -1 --format=%H'


def test_revision_command():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.revision.id == 'revision id cmd'


def test_author_detect():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.revision.author() == \
        "git log -1 --pretty='%aN <%aE>'"


def test_author_command():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.revision.author == 'author cmd'


def test_date_detect():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.revision.date() == "git log -1 --pretty='%at'"


def test_date_command():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.revision.date == 'date cmd'


def test_description_detect():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.revision.description() == "git log -1 --pretty='%B'"


def test_description_command():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.revision.description == 'description cmd'


def test_changelog_detect():
    meta = MetadataConfig.from_string(MetadataDetect)
    assert meta.repository.revision.changelog() == \
        'git log --no-merges --format=medium %old%..%new%'


def test_changelog_command():
    meta = MetadataConfig.from_string(MetadataManual)
    assert meta.repository.revision.changelog == 'changelog cmd'
