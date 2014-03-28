# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from collections import namedtuple

import pytest

from upaas.config.metadata import MetadataConfig
from upaas.utils import supported_versions


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


@pytest.fixture(scope="module")
def interpreters_config(request):
    configmock = namedtuple('ConfigMock', 'interpreters')
    return configmock(interpreters={
        'ruby': {'1.8': {}, '1.9': {}, '2.0': {}, '2.1': {}, '3.1': {}}})


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


def test_supported_versions_major(interpreters_config):
    metadata = MetadataConfig.from_string('''
interpreter:
  type: ruby
  versions:
    - '2'

repository:
  clone: echo "Cloned"
  update: echo "Updated"
''')
    valid = supported_versions(interpreters_config, metadata)
    assert len(valid.keys()) == 2
    assert '2.0' in valid
    assert '2.1' in valid


def test_supported_versions_minors(interpreters_config):
    metadata = MetadataConfig.from_string('''
interpreter:
  type: ruby
  versions:
    - '1.8'
    - '1.9'
    - '2.1'

repository:
  clone: echo "Cloned"
  update: echo "Updated"
''')
    valid = supported_versions(interpreters_config, metadata)
    assert len(valid.keys()) == 3
    assert '1.8' in valid
    assert '1.9' in valid
    assert '2.1' in valid
