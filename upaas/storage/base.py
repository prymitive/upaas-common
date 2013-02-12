# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.storage.exceptions import InvalidStorageConfiguration


class BaseStorage(object):

    def __init__(self, settings):
        self.settings = settings
        if not self.configure():
            raise InvalidStorageConfiguration

    def configure(self):
        """
        Parse storage configuration and return False if it's not valid.
        """
        return True

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
