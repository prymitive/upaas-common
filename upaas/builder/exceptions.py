# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


class InvalidConfiguration(Exception):
    """
    Raised if upaas-builder configuration is invalid.
    """
    pass


class BuildError(Exception):
    """
    General class for catching any build error.
    """
    pass


class OSBootstrapError(BuildError):
    """
    Raised in case of errors during os image bootstraping.
    """
    pass


class PackageSystemError(BuildError):
    """
    Raised in case of system errors during package build. This does not cover
    errors caused by package configuration or any commands executed by package
    itself, only errors independent from package (os bootstrap error for
    example)
    """
    pass


class PackageUserError(BuildError):
    """
    Raised when executing package specific actions.
    """
    pass
