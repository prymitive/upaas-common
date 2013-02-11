# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import shutil
import logging

from upaas_storage.base import BaseStorage


log = logging.getLogger(__name__)


class LocalStorage(BaseStorage):

    def configure(self):
        self.dir = self.settings.get('dir')

        if self.dir is None:
            log.error(u"Storage directory needs to be configured")
            return False

        if not os.path.isdir(self.dir):
            log.error(u"Storage directory '%s' does not exist" % self.dir)
            return False

        return True

    def join_paths(self, remote_path):
        return os.path.join(self.dir, remote_path.lstrip('/'))

    def get(self, remote_path, local_path):
        log.info(u"[GET] Copying %s to %s" % (self.join_paths(remote_path),
                                             local_path))
        shutil.copy(self.join_paths(remote_path), local_path)

    def put(self, local_path, remote_path):
        log.info(u"[PUT] Copying %s to %s" % (local_path,
                                              self.join_paths(remote_path)))
        shutil.copy(local_path, self.join_paths(remote_path))
