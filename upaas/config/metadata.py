# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import logging

from upaas.config import base
from upaas.compat import unicode


log = logging.getLogger(__name__)


class RevisionEntry(base.ScriptEntry):

    def log_msg(self, msg):
        log.info("repository.revision autodetect - %s" % msg)

    def detect_revision(self):
        if os.path.isdir('.git'):
            self.log_msg("git detected")
            return ['git rev-parse HEAD']
        elif os.path.isdir('.svn'):
            self.log_msg("svn detected")
            return ["svn info -r 'HEAD' --non-interactive --trust-server-cert"
                    " | grep Revision | egrep -o '[0-9]+'"]
        elif os.path.isdir('.bzr'):
            self.log_msg("bazaar detected")
            return ['bzr revno']
        elif os.path.isdir('.hg'):
            self.log_msg("mercurial detected")
            return ['hg id -i']
        else:
            self.log_msg("unknown repository type, using root directory "
                         "modification time as revision number")
            return ['date +%s -r .']

    default = detect_revision


class AuthorEntry(base.ScriptEntry):

    def log_msg(self, msg):
        log.info("repository.author autodetect - %s" % msg)

    def detect_revision(self):
        if os.path.isdir('.git'):
            self.log_msg("git detected")
            return ["git log -1 --pretty='%aN <%aE>'"]
        elif os.path.isdir('.svn'):
            self.log_msg("svn detected")
            return ["svn info -r 'HEAD' --non-interactive --trust-server-cert "
                    "| grep 'Last Changed Author:' "
                    "| sed s/'^Last Changed Author: '/''/"]
        elif os.path.isdir('.bzr'):
            self.log_msg("bazaar detected")
            return ["bzr log -l 1 | grep 'committer:' "
                    "| sed s/'committer: '/''/"]
        elif os.path.isdir('.hg'):
            self.log_msg("mercurial detected")
            return ["hg log -r . --template='{author}'"]
        else:
            self.log_msg("unknown repository type, can't detect current "
                         "revision author")
            return ['anonymous']

    default = detect_revision


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
            "info": {
                "revision": RevisionEntry(),
                "author": AuthorEntry(),
                "date": base.ScriptEntry(),
                "description": base.ScriptEntry(),
                "changelog": base.ScriptEntry(),
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
        }
    }
