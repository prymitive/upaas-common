# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import tempfile
import shutil
import logging

from upaas import distro

from upaas import commands
from upaas import tar
from upaas.checksum import calculate_file_sha256
from upaas.config.base import ConfigurationError
from upaas.builder import exceptions
from upaas.chroot import Chroot
from upaas.storage.exceptions import StorageError


log = logging.getLogger(__name__)


class BuildResult:

    def __init__(self):
        self.progress = 0

        self.storage = None
        self.package_path = None
        self.checksum = None

        self.distro_name = distro.distro_name()
        self.distro_version = distro.distro_version()


class Builder(object):

    builder_action_names = ["system"]
    app_action_names = ["before", "main", "after"]

    def __init__(self, builder_config, metadata):
        """
        :param builder_config: Builder configuration.
        :param metadata: Application metadata.
        """
        self.metadata = metadata
        self.config = builder_config

        self.actions = self.parse_actions(metadata)
        self.envs = self.parse_envs(metadata)
        self.os_packages = self.parse_packages(metadata)
        self.storage = self.find_storage_handler()

    def parse_actions(self, meta):
        """
        Parse and merge all config files (builder and app meta), then return
        final list of all actions to perform.
        """
        def _run_action(entry, name, ret):
            try:
                value = entry["actions"]["setup"][name]
                if value:
                    ret[name] = value
            except KeyError:
                pass
            else:
                log.debug(u"Got '%s' action" % name)

        ret = {}

        # builder actions are special, they cannot be declared by app, only
        # by builder config
        for name in self.builder_action_names:
            ret[name] = []
            _run_action(self.config.interpreters, name, ret)

        for name in self.app_action_names:
            ret[name] = []

            # global actions
            _run_action(self.config.interpreters, name, ret)

            # interpreter actions
            for version in ["any"] + meta.interpreter.versions:
                _run_action(
                    self.config.interpreters[meta.interpreter.type][version],
                    name, ret)

            # app metadata actions
            try:
                value = meta.actions.setup.get(name)
                if value:
                    ret[name] = value
            except AttributeError:
                pass
            else:
                log.debug(u"Got '%s' action from app meta" % name)

        for name in self.builder_action_names + self.app_action_names:
            actions = ret.get(name, [])
            log.info(u"Commands for '%s' action:" % name)
            for action in actions:
                log.info(u"- %s" % action)
            log.info(u"- ")

        return ret

    def parse_envs(self, meta):
        """
        Parse and merge all config files (builder and app meta), then return
        final all env variables used in actions.
        """
        ret = {}
        try:
            value = self.config.interpreters["env"]
            if value:
                ret.update(value)
                log.debug(u"Got env variables for all interpreters: %s" % (
                    u", ".join([u"%s=%s" % (k, v) for k, v in value.items()])))
        except KeyError:
            pass
        for version in ["any"] + meta.interpreter.versions:
            try:
                value = self.config.interpreters[meta.interpreter.type][
                    version]["env"]
                if value:
                    ret.update(value)
            except KeyError:
                pass
            else:
                log.debug(u"Got env variables from %s/%s: %s" % (
                    meta.interpreter.type, version,
                    u", ".join([u"%s=%s" % (k, v) for k, v in value.items()])))
            if meta.get(u"env"):
                ret.update(meta.env)
                log.debug(u"Got env variables from app meta: %s" % u", ".join(
                    [u"%s=%s" % (k, v) for k, v in value.items()]))
        return ret

    def parse_packages(self, meta):
        """
        Parse and merge all config files (builder and app meta), then return
        final list of all packages to install.
        """
        ret = set()
        try:
            for pkg in self.config.interpreters["packages"]:
                ret.add(pkg)
                log.debug(u"Will install package '%s' from builder config "
                          u"for all interpreters" % pkg)
        except KeyError:
            pass
        for version in ["any"] + meta.interpreter.versions:
            try:
                for pkg in self.config.interpreters[meta.interpreter.type][
                        version]["packages"]:
                    ret.add(pkg)
                    log.debug(u"Will install package '%s' from builder config "
                              u"for interpreter version '%s'" % (pkg, version))
            except KeyError:
                pass
            try:
                for pkg in meta.os[distro.distro_name()]["packages"]:
                    ret.add(pkg)
                    log.debug(u"Will install package '%s' from metadata for "
                              u"distribution %s" % (pkg, distro.distro_name()))
            except KeyError:
                pass
        return ret

    def find_storage_handler(self):
        """
        Will try to find storage handler class user has set in configuration,
        create instance of it and return that instance.
        """
        storage_handler = None
        name = self.config.storage.handler
        storage_module = ".".join(name.split(".")[0:len(name.split(".")) - 1])
        storage_class = name.split(".")[len(name.split(".")) - 1]
        try:
            exec("from %s import %s as storage_handler" % (
                storage_module, storage_class))
        except ImportError:
            log.error(u"Storage handler '%s' could not be "
                      u"loaded" % self.config.storage.handler)
            raise exceptions.InvalidConfiguration
        else:
            log.info(u"Loaded storage handler: "
                     u"%s" % self.config.storage.handler)
            try:
                return storage_handler(self.config.storage.settings)
            except ConfigurationError:
                log.error(u"Storage handler failed to initialize with given "
                          u"configuration")
                raise exceptions.InvalidConfiguration

    def build_package(self, force_fresh=False):
        """
        Build a package

        :param meta: Package metadata passed as Config instance.
        :param force_fresh: Force fresh package built using empty system image.
        """
        def _cleanup(directory):
            log.info(u"Removing directory '%s'" % directory)
            shutil.rmtree(directory)

        log.info(u"Starting package build (force fresh package: "
                 u"%s)" % force_fresh)

        result = BuildResult()

        if not self.has_valid_os_image():
            try:
                self.bootstrap_os()
            except exceptions.OSBootstrapError:
                log.error(u"Error during os bootstrap, aborting")
                raise exceptions.PackageSystemError
            except StorageError:
                log.error(u"Error during uploading os image, aborting")
                raise exceptions.PackageSystemError

        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_package_")
        workdir = os.path.join(directory, "workdir")
        chroot_homedir = "/home/app"
        os.mkdir(workdir, 0755)
        log.info(u"Working directory created at '%s'" % workdir)

        if not self.unpack_os(directory, workdir, force_fresh=force_fresh):
            _cleanup(directory)
            raise exceptions.PackageSystemError
        log.info(u"Os image unpacked")
        result.progress = 10
        yield result

        if not self.run_actions(self.builder_action_names, workdir, '/'):
            _cleanup(directory)
            raise exceptions.PackageUserError
        log.info(u"All application actions executed")
        result.progress = 20
        yield result

        if not self.install_packages(workdir):
            _cleanup(directory)
            raise exceptions.PackageUserError
        log.info(u"All packages installed")
        result.progress = 35
        yield result

        if not self.clone(workdir, chroot_homedir):
            _cleanup(directory)
            raise exceptions.PackageUserError
        log.info(u"Application cloned")
        result.progress = 40
        yield result

        if not self.run_actions(self.app_action_names, workdir,
                                chroot_homedir):
            _cleanup(directory)
            raise exceptions.PackageUserError
        log.info(u"All application actions executed")
        result.progress = 85
        yield result

        package_path = os.path.join(directory, "package")
        if not tar.pack_tar(workdir, package_path):
            _cleanup(directory)
            raise exceptions.PackageSystemError
        log.info(u"Application package created")
        result.progress = 92
        yield result

        checksum = calculate_file_sha256(package_path)
        log.info(u"Package checksum: %s" % checksum)
        result.progress = 96
        yield result

        try:
            self.storage.put(package_path, checksum)
        except StorageError:
            log.error(u"Error while uploading package")
            _cleanup(directory)
            raise exceptions.PackageSystemError

        _cleanup(directory)

        result.progress = 100
        result.storage = self.storage.__class__.__name__
        result.package_path = checksum
        result.checksum = checksum
        yield result

    def unpack_os(self, directory, workdir, force_fresh=False):
        #TODO right now we always build fresh package
        os_image_path = os.path.join(directory, distro.distro_image_filename())
        log.info(u"Fetching os image")
        try:
            self.storage.get(distro.distro_image_filename(), os_image_path)
        except StorageError:
            log.error(u"Storage error while fetching os image")
            return False
        else:
            log.info(u"Unpacking os image")
            if not tar.unpack_tar(os_image_path, workdir):
                log.error(u"Error while unpacking os image to '%s'" % workdir)
                return False
        return True

    def install_packages(self, workdir):
        with Chroot(workdir):
            for name in self.os_packages:
                cmd = self.config.commands.install.cmd.replace("%package%",
                                                               name)
                try:
                    commands.execute(cmd,
                                     timeout=self.config.commands.timelimit,
                                     env=self.config.commands.install.env,
                                     output_loglevel=logging.INFO)
                except commands.CommandTimeout:
                    log.error(u"Installing package '%s' is taking to long, "
                              u"aborting" % name)
                    return False
                except commands.CommandFailed:
                    log.error(u"Installing package '%s' failed" % name)
                    return False
        return True

    def clone(self, workdir, homedir):
        with Chroot(workdir):
            for cmd in self.metadata.repository.clone:
                cmd = cmd.replace("%destination%", homedir)
                try:
                    commands.execute(cmd,
                                     timeout=self.config.commands.timelimit,
                                     env=self.metadata.repository.env,
                                     output_loglevel=logging.INFO)
                except commands.CommandTimeout:
                    log.error(u"Cloning repository is taking too long, "
                              u"aborting")
                    return False
                except commands.CommandFailed:
                    log.error(u"Cloning failed")
                    return False
        return True

    def run_actions(self, actions, workdir, homedir):
        for name in actions:
            log.info(u"Executing '%s' setup actions" % name)
            for cmd in self.actions[name]:
                with Chroot(workdir, workdir=homedir):
                    try:
                        commands.execute(
                            cmd, timeout=self.config.commands.timelimit,
                            env=self.envs, output_loglevel=logging.INFO)
                    except commands.CommandTimeout:
                        log.error(u"Command is taking to long to execute, "
                                  u"aborting")
                        return False
                    except commands.CommandFailed:
                        log.error(u"Command failed")
                        return False
        return True

    def has_valid_os_image(self):
        """
        Check if os image exists and is fresh enough.
        """
        if not self.storage.exists(distro.distro_image_filename()):
            return False

        #TODO check os image mtime
        return True

    def bootstrap_os(self):
        """
        Bootstrap base os image.
        """
        def _cleanup(directory):
            log.info(u"Removing directory '%s'" % directory)
            shutil.rmtree(directory)

        log.info(u"Bootstrapping os image using")

        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_bootstrap_")
        log.debug(u"Created temporary directory for bootstrap at "
                  u"'%s'" % directory)

        for cmd in self.config.bootstrap.commands:
            cmd = cmd.replace("%workdir%", directory)
            try:
                commands.execute(cmd, timeout=self.config.bootstrap.timelimit,
                                 cwd=directory, env=self.config.bootstrap.env)
            except commands.CommandTimeout:
                log.error(u"Bootstrap was taking too long and it was killed")
                _cleanup(directory)
                raise exceptions.OSBootstrapError
            except commands.CommandFailed:
                log.error(u"Bootstrap command failed")
                _cleanup(directory)
                raise exceptions.OSBootstrapError
        log.info(u"Bootstrap done, packing image")

        archive_path = os.path.join(directory, "image.tar.gz")
        if not tar.pack_tar(directory, archive_path,
                            timeout=self.config.bootstrap.timelimit):
            _cleanup(directory)
            raise exceptions.OSBootstrapError
        else:
            log.info(u"Image packed, uploading")
            self.storage.put(archive_path, distro.distro_image_filename())

        log.info(u"Image uploaded")
        _cleanup(directory)
        log.info(u"All done")
