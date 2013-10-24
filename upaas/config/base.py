# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import types
import os
import logging

import yaml
from yaml import Loader, SafeLoader, YAMLError


log = logging.getLogger(__name__)


# paths for searching config files
UPAAS_CONFIG_DIRS = ['.', '/etc/upaas']


def construct_yaml_str(self, node):
    """
    Override the default string handling function to always return unicode
    objects.

    Code from:
    http://stackoverflow.com/questions/2890146/how-to-force-pyyaml-to-load
    -strings-as-unicode-objects
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

    default = None

    def __init__(self, required=False, default=None):
        self.required = required
        if not default is None:
            self.default = default

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


class WildcardEntry(ConfigEntry):
    pass


class StringEntry(ConfigEntry):
    pass


class IntegerEntry(ConfigEntry):

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        if min_value and max_value and min_value > max_value:
            log.error(u"Minimal value (%d) must be lower then maximum value "
                      u"(%d)!" % (min_value, max_value))
            raise ValueError
        self.min_value = min_value
        self.max_value = max_value
        super(IntegerEntry, self).__init__(*args, **kwargs)

    def validate(self, value):
        if value is not None and not isinstance(value, int):
            log.error(u"Value must be integer, %s "
                      u"given" % value.__class__.__name__)
            raise ConfigurationError
        if value is not None and self.min_value and value < self.min_value:
            log.error(u"Value %d is too low, minimal value is '%d'" % (
                value, self.min_value))
            raise ConfigurationError
        if value is not None and self.max_value and value > self.max_value:
            log.error(u"Value %d is too high, maximal value is '%d'" % (
                value, self.max_value))
            raise ConfigurationError


class BooleanEntry(ConfigEntry):

    def validate(self, value):
        if value is not None and not isinstance(value, bool):
            log.error(u"Value must be a bool, %s "
                      u"given" % value.__class__.__name__)
            raise ConfigurationError


class ListEntry(ConfigEntry):

    default = []

    def __init__(self, value_type=None, **kwargs):
        self.value_type = value_type
        super(ListEntry, self).__init__(**kwargs)

    def validate(self, value):
        if value is None:
            return
        if not isinstance(value, list):
            log.error(u"Value must be list, %s "
                      u"given" % value.__class__.__name__)
            raise ConfigurationError
        if not self.value_type:
            return
        for elem in value:
            if not isinstance(elem, self.value_type):
                log.error(u"List element '%r' must be instance of '%s', '%s' "
                          u"given" % (elem, self.value_type.__name__,
                                      elem.__class__.__name__))
                raise ConfigurationError


class DictEntry(ConfigEntry):

    default = {}

    def __init__(self, value_type=None, **kwargs):
        self.value_type = value_type
        super(DictEntry, self).__init__(**kwargs)

    def validate(self, value):
        if value is None:
            return
        if not isinstance(value, dict):
            log.error(u"Value must be dict, %s "
                      u"given" % value.__class__.__name__)
            raise ConfigurationError
        if not self.value_type:
            return
        for name, elem in value.items():
            if not isinstance(elem, self.value_type):
                log.error(u"Dict key '%r' value must be instance of '%s', '%s'"
                          u" given" % (name, self.value_type.__name__,
                                       elem.__class__.__name__))
                raise ConfigurationError


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
    multi-line string. In case of string it will be converted into list.
    """

    def clean(self, value):
        if isinstance(value, unicode):
            return [value]
        return value


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
        except YAMLError:
            log.error(u"Can't parse yaml file '%s'" % path)
            raise ConfigurationError

        return cls(content)

    @classmethod
    def from_string(cls, string):
        return cls(yaml.safe_load(string))

    def __init__(self, content, _schema=None):
        if _schema:
            self.schema = _schema

        log.debug(u"Parsing settings %s with schema %s" % (content,
                                                           self.schema))

        if not isinstance(content, (types.DictionaryType, types.NoneType)):
            log.error(u"Invalid configuration, expected dict but got "
                      u"%s" % content.__class__.__name__)
            raise ConfigurationError

        self.content = content
        self.entries = {}
        self.children = set()

        for key, value in self.schema.items():
            if content is None and isinstance(value, ConfigEntry) \
                    and value.required:
                log.error(u"Empty configuration")
                raise ConfigurationError
            if isinstance(value, dict):
                setattr(self, key, Config(content.get(key, {}), _schema=value))
                self.children.add(key)
            elif isinstance(value, WildcardEntry):
                self.entries[key] = (content or {}).get(key)
            elif isinstance(value, ConfigEntry):
                self.parse_entry(key, value, (content or {}).get(key))
            else:
                log.warning(u"Invalid configuration entry: %s" % key)

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

    def dump_string(self):
        """
        Dump all entries as string.
        """
        return yaml.safe_dump(self.content)

    def parse_entry(self, name, entry_schema, value):
        """
        Parse and validate single configuration entry using schema.
        """
        log.debug(u"Parsing configuration entry '%s'" % name)
        if entry_schema.required and value is None:
            log.error(u"Missing required configuration entry '%s'" % name)
            raise ConfigurationError
        log.debug(u"Cleaning configuration entry '%s'" % name)
        value = entry_schema.clean(value)
        log.debug(u"Validating configuration entry '%s'" % name)
        try:
            entry_schema.validate(value)
        except ConfigurationError:
            log.error(u"Configuration entry '%s' is invalid" % name)
            raise ConfigurationError
        else:
            if value is not None:
                self.entries[name] = value
                log.debug(u"Configuration entry '%s' with value "
                          u"'%s'" % (name, value))
            elif entry_schema.default is not None:
                log.debug(u"Configuration entry '%s' is missing, using default"
                          u" value: %s" % (name, entry_schema.default))
                self.entries[name] = entry_schema.default


def load_config(cls, filename, directories=UPAAS_CONFIG_DIRS):
    """
    Try to load config, return None in case of errors.

    :param cls: Class to use for config validation and parsing.
    :filename: Filename to look for.
    """

    upaas_config = None

    paths = [os.path.join(p, filename) for p in directories]
    if os.environ.get('UPAAS_CONFIG_DIR'):
        log.info(u"Adding directory '%s' from UPAAS_CONFIG_DIR env "
                 u"variable" % os.environ.get('UPAAS_CONFIG_DIR'))
        paths = [os.path.join(os.environ.get('UPAAS_CONFIG_DIR'),
                              filename)] + paths

    for path in paths:
        log.debug(u"Trying to load %s config file from %s" % (cls.__name__,
                                                              path))
        if os.path.isfile(path):
            log.info(u"Loading %s config file from %s" % (cls.__name__,
                                                          path))
            try:
                upaas_config = cls.from_file(path)
            except ConfigurationError:
                log.error(u"Invalid %s config file at %s" % (cls.__name__,
                                                             path))
                return None
            else:
                break

    if not upaas_config:
        log.error(u"No config file found for %s" % filename)

    return upaas_config
