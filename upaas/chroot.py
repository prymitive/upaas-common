# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


# code from
# http://www.thehosthelpers.com/how-tos-tips-tricks/protip-secure-your-rooted
# - python-script-(or-easy-chroot-class)/


from __future__ import unicode_literals

import os
import logging


log = logging.getLogger(__name__)


class Chroot(object):

    def __init__(self, root, workdir=None, umask=0o22):
        self.root = root
        self.dir = '/' if workdir is None else workdir
        self.umask = umask

    def __enter__(self):
        log.debug("Entering chroot at '%s', workdir is '%s'" % (self.root,
                                                                self.dir))
        self.realdir = os.getcwd()
        self.realroot = os.open('/', os.O_RDONLY)
        os.chroot(self.root)
        os.chdir(self.dir)
        self.old_umask = os.umask(self.umask)
        return self

    def __exit__(self, type, value, traceback):
        try:
            os.fchdir(self.realroot)
        except OSError:
            return
        os.chroot('.')
        os.close(self.realroot)
        os.chdir(self.realdir)
        os.umask(self.old_umask)
        log.debug("Exited from chroot at '%s'" % self.root)

    def escape(self):
        try:
            os.fchdir(self.realroot)
        except OSError:
            return
        while os.stat('.')[1] != os.stat('..')[1]:
            os.chdir('..')
        os.chroot('.')
        os.close(self.realroot)
        os.chdir(self.realdir)
        os.umask(self.old_umask)
