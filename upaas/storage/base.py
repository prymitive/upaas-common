# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config import base


class BaseStorage(object):

    configuration_schema = {}

    def __init__(self, settings):
        self.settings = base.Config(settings,
                                    _schema=self.configuration_schema)

    def get(self, remote_path, local_path):
        """
        Get file from storage.

        :param remote_path: Path of the file we want to download from storage.
        :param local_path: Where to put downloaded file.
        """
        raise NotImplementedError

    def put(self, local_path, remote_path):
        """
        Upload file to storage.

        :param local_path: Path of the file to upload.
        :param remote_path: Path under uploaded file should be available.
        """
        raise NotImplementedError

    def delete(self, remote_path):
        """
        Delete file from storage.

        :param remote_path: Path of the remote file to be deleted from storage.
        """
        raise NotImplementedError

    def exists(self, remote_path):
        """
        Check if given path (file or directory) exists on storage.

        :param remote_path: Path of the remote file to be checked.
        """
        raise NotImplementedError

    def size(self, remote_path):
        """
        Return size of the file.

        :param remote_path: Path of the remote file.
        """
        raise NotImplementedError

    def mtime(self, remote_path):
        """
        Return modification time of the file as datetime object.

        :param remote_path: Path of the remote file to be checked.
        """
        raise NotImplementedError
