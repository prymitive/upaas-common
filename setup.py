#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import sys

from setuptools import setup, find_packages


setup(
    name='upaas',
    version='0.1-dev',
    license='GPLv3',
    description='uPaaS common classes',
    author='Łukasz Mierzwa',
    author_email='l.mierzwa@gmail.com',
    url='https://github.com/prymitive/upaas-common',
    packages=find_packages(),
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    platforms=['Linux'],
)
