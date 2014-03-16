# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas.config.metadata import MetadataConfig


@pytest.fixture(scope="module")
def metadata_detect(request):
    return MetadataConfig.from_string('''
interpreter:
  type: ruby
  versions:
    - 2.1.0

repository:
  clone: echo "Cloned"
  update: echo "Updated"
''')


@pytest.fixture(scope="module")
def metadata_manual(request):
    return MetadataConfig.from_string('''
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
''')


def test_revision_detect(metadata_detect):
    assert metadata_detect.repository.revision.id() == 'git log -1 --format=%H'


def test_revision_command(metadata_manual):
    assert metadata_manual.repository.revision.id == 'revision id cmd'


def test_author_detect(metadata_detect):
    assert metadata_detect.repository.revision.author() == \
        "git log -1 --pretty='%aN <%aE>'"


def test_author_command(metadata_manual):
    assert metadata_manual.repository.revision.author == 'author cmd'


def test_date_detect(metadata_detect):
    assert metadata_detect.repository.revision.date() == \
        "git log -1 --pretty='%at'"


def test_date_command(metadata_manual):
    assert metadata_manual.repository.revision.date == 'date cmd'


def test_description_detect(metadata_detect):
    assert metadata_detect.repository.revision.description() == \
        "git log -1 --pretty='%B'"


def test_description_command(metadata_manual):
    assert metadata_manual.repository.revision.description == 'description cmd'


def test_changelog_detect(metadata_detect):
    assert metadata_detect.repository.revision.changelog() == \
        'git log --no-merges --format=medium %old%..%new%'


def test_changelog_command(metadata_manual):
    assert metadata_manual.repository.revision.changelog == 'changelog cmd'
