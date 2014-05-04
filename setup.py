#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from setuptools import setup, find_packages

try:
    from pip.req import parse_requirements
    required = {'install_requires': [str(r.req) for r in parse_requirements(
        'requirements.txt')]}
except ImportError:
    required = {}


setup(
    name='upaas-common',
    version='0.3',
    license='GPLv3',
    description='uPaaS common classes',
    author='Łukasz Mierzwa',
    author_email='l.mierzwa@gmail.com',
    url='https://github.com/prymitive/upaas-common',
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    platforms=['Linux'],
    **required
)
