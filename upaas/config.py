# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging

import yaml
from yaml import Loader, SafeLoader

log = logging.getLogger(__name__)


def construct_yaml_str(self, node):
    """
    Override the default string handling function to always return unicode
    objects.

    Code from:
    http://stackoverflow.com/questions/2890146/how-to-force-pyyaml-to-load-strings-as-unicode-objects
    """
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


class ConfigurationError(Exception):
    """
    Raised if user provided configuration is invalid (missing or invalid
    required options).
    """


class ConfigEntry(object):
    def __init__(self, required=False):
        self.required = required

    def validate(self, value):
        """
        Validate entry value, raise exception if invalid.
        """
        pass

    def clean(self, value):
        """
        Cleanup entry value if needed, returned value will be new entry value.
        """
        return value


class StringEntry(ConfigEntry):
    pass


class IntegerEntry(ConfigEntry):
    pass


class ListEntry(ConfigEntry):
    def __init__(self, value_type, **kwargs):
        self.value_type = value_type
        super(ListEntry, self).__init__(**kwargs)


class FSPathEntry(ConfigEntry):
    def __init__(self, must_exist=False, **kwargs):
        self.must_exist = must_exist
        super(FSPathEntry, self).__init__(**kwargs)

    def validate(self, value):
        if self.must_exist and not os.path.exists(value):
            log.error(u"Required path '%s' does not exits" % value)
            raise ConfigurationError


class ScriptEntry(ConfigEntry):
    """
    Used for scripts that can be defined either as a list of strings or one big
    multi-line string. In case of list it will be converted into single string.
    """

    def clean(self, value):
        if isinstance(value, list):
            return u"\n".join(value)


class Config(object):
    """
    Configuration object, it will parse all entries and check if they are valid
    using predefined schema.

    Schema is a dictionary where values are ConfigEntry instances describing
    possible options and its syntax:
    {
        "required_string": config.StringEntry(required=True),
        "folder1": {
            "subfolder1": {
                "required_int": config.IntegerEntry(required=True)
            },
            "optional_int": config.IntegerEntry(),
        }
    }
    """

    schema = {}

    @classmethod
    def from_file(cls, path):

        try:
            with open(path) as config_file:
                content = yaml.safe_load(config_file)
        except IOError:
            log.error(u"Can't open configuration file '%s'" % path)
            raise ConfigurationError

        return cls(content)

    def __init__(self, content, _schema=None):
        if _schema:
            self.schema = _schema

        if self.schema and (not content or not isinstance(content, dict)):
            log.error(u"Invalid configuration")
            raise ConfigurationError

        self.entries = {}
        self.children = set()

        for key, value in self.schema.items():
            if isinstance(value, dict):
                setattr(self, key, Config(content.get(key), _schema=value))
                self.children.add(key)
            elif isinstance(value, ConfigEntry):
                self.parse_entry(key, value, (content or {}).get(key))
            else:
                log.warning(u"Invalid entry in configuration content: %s" % key)

    def __getattr__(self, item):
        if item in self.entries:
            return self.entries[item]
        raise AttributeError

    def get(self, item, default=None):
        try:
            return self.__getattr__(item)
        except AttributeError:
            return default

    def dump(self):
        """
        Dump all entries as dictionary.
        """
        ret = {}
        ret.update(self.entries)
        for key in self.children:
            ret[key] = getattr(self, key).dump()
        return ret

    def parse_entry(self, name,  entry_schema, value):
        """
        Parse and validate single configuration entry using schema.
        """
        log.debug(u"Parsing configuration entry '%s'" % name)
        if entry_schema.required and not value:
            log.error(u"Missing required configuration entry '%s'" % name)
            raise ConfigurationError
        log.debug(u"Cleaning configuration entry '%s'" % name)
        value = entry_schema.clean(value)
        log.debug(u"Validating configuration entry '%s'" % name)
        entry_schema.validate(value)
        if value:
            self.entries[name] = value
            log.debug(u"Configuration entry '%s' with value '%s'" % (name,
                                                                     value))
