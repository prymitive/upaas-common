# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import logging

from upaas.config import base
from upaas.compat import unicode


log = logging.getLogger(__name__)


class VCSLazyEntry(base.StringEntry):

    entry_name = None
    commands = {}

    def log_msg(self, msg):
        log.info("%s autodetect - %s" % (self.entry_name, msg))

    def detect(self):
        if os.path.isdir('.git'):
            self.log_msg("git detected, using '%s'" % self.commands['git'])
            return self.commands['git']
        elif os.path.isdir('.svn'):
            self.log_msg("svn detected using '%s'" % self.commands['svn'])
            return self.commands['svn']
        elif os.path.isdir('.bzr'):
            self.log_msg("bazaar detected using '%s'" % self.commands['bzr'])
            return self.commands['bzr']
        elif os.path.isdir('.hg'):
            self.log_msg("mercurial detected using '%s'" % self.commands['hg'])
            return self.commands['hg']
        else:
            self.log_msg("unknown repository type, using "
                         "'%s'" % self.commands['unknown'])
            return self.commands['unknown']

    default = detect


class VCSRevisionIDEntry(VCSLazyEntry):

    entry_name = 'repository.revision'

    commands = {
        'git': 'git log -1 --format=%H',
        'svn': "svn info --non-interactive --trust-server-cert "
               "| grep Revision | egrep -o '[0-9]+'",
        'bzr': 'bzr revno',
        'hg': 'hg id -i',
        'unknown': 'date +%s -r .',
    }


class VCSAuthorEntry(VCSLazyEntry):

    entry_name = 'repository.author'

    commands = {
        'git': "git log -1 --pretty='%aN <%aE>'",
        'svn': "svn info --non-interactive --trust-server-cert "
               "| grep 'Last Changed Author:' "
               "| sed s/'^Last Changed Author: '/''/",
        'bzr': "bzr log -l 1 | grep 'committer:' | sed s/'committer: '/''/",
        'hg': "hg log -r . --template='{author}'",
        'unknown': "echo 'no author information available'",
    }


class VCSDateEntry(VCSLazyEntry):

    entry_name = 'repository.date'

    commands = {
        'git': "git log -1 --pretty='%at'",
        'svn': "svn info --non-interactive --trust-server-cert "
               "| grep 'Last Changed Date:' "
               "| sed s/'^Last Changed Date: '/''/ "
               "| cut -d '(' -f 1",
        'bzr': "bzr version-info --custom --template '{date}'",
        'hg': "hg log -r . --template='{date}'",
        'unknown': 'date +%s -r .',
    }


class VCSDescriptionEntry(VCSLazyEntry):

    entry_name = 'repository.description'

    commands = {
        'git': "git log -1 --pretty='%B'",
        'svn': "svn log -l 1 --non-interactive --trust-server-cert "
               "| egrep -v '^\-+$' "
               "| tail -n +3",
        'bzr': "bzr log -l 1 | egrep -v '^-+$|^revno:|^committer:|"
               "^branch nick:|^timestamp:|^message:' | sed s/'^  '/''/",
        'hg': "hg log -r . --template='{desc}'",
        'unknown': "echo 'no description information available'",
    }


class VCSChangeLogEntry(VCSLazyEntry):

    entry_name = 'repository.description'

    commands = {
        'git': 'git log --no-merges --format=medium %old%..%new%',
        'svn': 'svn log -r%new%:%old% --non-interactive --trust-server-cert',
        'bzr': 'bzr log -r%old%..%new%',
        'hg': 'hg log -r %old%:%new%',
        'unknown': "echo 'no changelog information available'",
    }


class MetadataConfig(base.Config):

    schema = {
        "os": base.WildcardEntry(),
        "interpreter": {
            "type": base.StringEntry(required=True),
            "versions": base.ListEntry(unicode),
            "settings": base.DictEntry(value_type=unicode),
        },
        "repository": {
            "env": base.DictEntry(value_type=unicode),
            "clone": base.ScriptEntry(required=True),
            "update": base.ScriptEntry(required=True),
            "revision": {
                "id": VCSRevisionIDEntry(),
                "author": VCSAuthorEntry(),
                "date": VCSDateEntry(),
                "description": VCSDescriptionEntry(),
                "changelog": VCSChangeLogEntry(),
            }
        },
        "env": base.DictEntry(value_type=unicode),
        "actions": {
            "setup": {
                "before": base.ScriptEntry(),
                "main": base.ScriptEntry(),
                "after": base.ScriptEntry(),
            }
        },
        "files": base.DictEntry(value_type=unicode),
        "uwsgi": {
            "settings": base.ListEntry(value_type=unicode)
        },
        "cron": base.WildcardEntry(),
    }
