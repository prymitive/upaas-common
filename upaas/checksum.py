# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from hashlib import sha256


def calculate_file_sha256(path):
    hasher = sha256()
    with open(path, "rb") as sfile:
        while True:
            data = sfile.read(4096)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()


def calculate_string_sha256(content):
    hasher = sha256()
    hasher.update(content)
    return hasher.hexdigest()
