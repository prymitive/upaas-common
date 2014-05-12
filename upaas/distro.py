# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import platform


def distro_name():
    return platform.dist()[0]


def distro_version():
    return platform.dist()[1]


def distro_codename():
    return platform.dist()[2]


def distro_arch():
    return platform.architecture()[0]


def distro_image_filename():
    # FIXME tar.gz is hardcoded?
    path = "%s-%s-%s.tar.gz" % (distro_name(), distro_version(), distro_arch())
    return path.replace('/', '-')
