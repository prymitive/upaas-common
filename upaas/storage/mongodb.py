# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from pymongo import MongoClient

from gridfs import GridFS, NoFile

from upaas.config import base
from upaas.storage.base import BaseStorage
from upaas.storage.exceptions import StorageError, FileNotFound,\
    FileAlreadyExists


log = logging.getLogger(__name__)


class MongoDBStorage(BaseStorage):

    configuration_schema = {
        "host": base.StringEntry(default="localhost"),
        "port": base.IntegerEntry(default=27017),
        "database": base.StringEntry(default="upaas-storage"),
        "username": base.StringEntry(),
        "password": base.StringEntry(),
    }

    def connect(self):
        mongouri = "mongodb://"
        if self.settings.get('username'):
            mongouri += self.settings.username
            if self.settings.get('password'):
                mongouri += ':' + self.settings.password
            mongouri += "@"
        mongouri += "%s:%s" % (self.settings.host, self.settings.port)

        return MongoClient(mongouri)

    def get(self, remote_path, local_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])
        try:
            fsfile = fs.get_last_version(filename=remote_path)
            with open(local_path, "wb") as dest:
                log.info(u"[GET] Copying mongodb:%s to %s" % (remote_path,
                                                              local_path))
                while True:
                    data = fsfile.read(4096)
                    if not data:
                        break
                    dest.write(data)
        except NoFile:
            client.disconnect()
            log.error(u"[GET] File not found: mongodb:%s" % remote_path)
            raise FileNotFound(u"%s not found" % remote_path)
        except Exception, e:
            log.error(u"[GET] Unhandled error: %s" % e)
            client.disconnect()
            raise StorageError(e)

    def put(self, local_path, remote_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])

        if self.exists(remote_path):
            raise FileAlreadyExists(u"%s already exists" % remote_path)

        gridin = fs.new_file(filename=remote_path)
        try:
            with open(local_path, "rb") as source:
                log.info(u"[PUT] Copying %s to mongodb:%s" % (local_path,
                                                              remote_path))
                while True:
                    data = source.read(4096)
                    if not data:
                        break
                    gridin.write(data)
                gridin.close()
            client.disconnect()
        except Exception, e:
            log.error(u"[PUT] Unhandled error: %s" % e)
            client.disconnect()
            raise StorageError(e)

    def delete(self, remote_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])
        try:
            fsfile = fs.get_last_version(filename=remote_path)
            fs.delete(fsfile._id)
            log.info(u"[DELETE] File deleted: mongodb:%s" % remote_path)
        except NoFile:
            client.disconnect()
            log.error(u"[DELETE] File not found: mongodb:%s" % remote_path)
            raise FileNotFound(u"%s not found" % remote_path)
        except Exception, e:
            log.error(u"[DELETE] Unhandled error: %s" % e)
            client.disconnect()
            raise StorageError(e)

    def exists(self, remote_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])
        ret = fs.exists(filename=remote_path)
        client.disconnect()
        return ret

    def size(self, remote_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])
        try:
            fsfile = fs.get_last_version(filename=remote_path)
        except NoFile:
            client.disconnect()
            log.error(u"[DELETE] File not found: mongodb:%s" % remote_path)
            raise FileNotFound(e)
        except Exception, e:
            log.error(u"[DELETE] Unhandled error: %s" % e)
            client.disconnect()
            raise StorageError(e)
        else:
            size = fsfile.length
            client.disconnect()
            return size

    def mtime(self, remote_path):
        client = self.connect()
        fs = GridFS(client[self.settings.database])
        try:
            fsfile = fs.get_last_version(filename=remote_path)
        except NoFile, e:
            client.disconnect()
            log.error(u"[DELETE] File not found: mongodb:%s" % remote_path)
            raise FileNotFound(e)
        except Exception, e:
            log.error(u"[DELETE] Unhandled error: %s" % e)
            client.disconnect()
            raise StorageError(e)
        else:
            timestamp = fsfile.upload_date
            client.disconnect()
            return timestamp
