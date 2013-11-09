# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import shutil
import logging
import datetime

from upaas.config import base
from upaas.storage.base import BaseStorage
from upaas.storage.exceptions import StorageError, FileNotFound


log = logging.getLogger(__name__)


class LocalStorage(BaseStorage):

    configuration_schema = {
        "dir": base.FSPathEntry(required=True, must_exist=True),
    }

    def _join_paths(self, remote_path):
        return os.path.join(self.settings.dir, remote_path.lstrip('/'))

    def get(self, remote_path, local_path):
        if not self.exists(remote_path):
            log.error(u"[GET] File not found: %s" % remote_path)
            raise FileNotFound(u"%s not found" % remote_path)

        log.info(u"[GET] Copying %s to %s" % (self._join_paths(remote_path),
                                              local_path))
        try:
            shutil.copy(self._join_paths(remote_path), local_path)
        except Exception, e:
            raise StorageError(e)

    def put(self, local_path, remote_path):
        log.info(u"[PUT] Copying %s to %s" % (local_path,
                                              self._join_paths(remote_path)))
        try:
            shutil.copy(local_path, self._join_paths(remote_path))
        except Exception, e:
            raise StorageError(e)

    def delete(self, remote_path):
        if not self.exists(remote_path):
            log.error(u"[DELETE] File not found: %s" % remote_path)
            raise FileNotFound(u"%s not found" % remote_path)
        try:
            os.remove(self._join_paths(remote_path))
            log.info(u"[DELETE] File deleted: "
                     u"%s" % self._join_paths(remote_path))
        except Exception, e:
            raise StorageError(e)

    def exists(self, remote_path):
        return os.path.exists(self._join_paths(remote_path))

    def size(self, remote_path):
        return os.path.getsize(self._join_paths(remote_path))

    def mtime(self, remote_path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(
            self._join_paths(remote_path)))
