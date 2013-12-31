# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


try:
    unicode = unicode
    basestring = basestring
except NameError:
    unicode = str
    basestring = (str, bytes)
