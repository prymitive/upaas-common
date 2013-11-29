# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import tempfile
import shutil
import datetime
import logging

from upaas import distro

from upaas import commands
from upaas import tar
from upaas import utils
from upaas.checksum import calculate_file_sha256
from upaas.builder import exceptions
from upaas.chroot import Chroot
from upaas.storage.utils import find_storage_handler
from upaas.storage.exceptions import StorageError
from upaas.processes import kill_and_remove_dir


log = logging.getLogger(__name__)


class BuildResult:

    def __init__(self):
        # % progress
        self.progress = 0

        # filename of the package used to build this package
        self.parent = None

        # selected interpreter version
        self.interpreter_version = None

        # class of the storage this package was uploaded to
        self.storage = None
        # package filename
        self.filename = None
        # package checksum
        self.checksum = None
        # package size
        self.bytes = 0

        self.distro_name = distro.distro_name()
        self.distro_version = distro.distro_version()
        self.distro_arch = distro.distro_arch()


class Builder(object):

    #TODO stage decorators
    # @stage('action_system', 95%)
    # time()

    builder_action_names = ["system"]
    interpreter_action_names = ["interpreter"]
    app_action_names = ["before", "main", "after"]
    finalize_action_names = ["finalize"]

    def __init__(self, builder_config, metadata):
        """
        :param builder_config: Builder configuration.
        :param metadata: Application metadata.
        """
        self.metadata = metadata
        self.config = builder_config

        self.interpreter_version = utils.select_best_version(self.config,
                                                             metadata)
        if not self.interpreter_version:
            self.user_error(u"Unsupported interpreter version")

        self.actions = self.parse_actions(metadata)
        self.envs = self.parse_envs(metadata)
        self.os_packages = self.parse_packages(metadata)
        self.storage = find_storage_handler(self.config)

    def user_error(self, msg):
        log.error(msg)
        raise exceptions.PackageUserError(msg)

    def system_error(self, msg):
        log.error(msg)
        raise exceptions.PackageSystemError(msg)

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

        # builder and finalize actions are special, they cannot be declared
        # by app, only by builder config
        for name in self.builder_action_names + self.finalize_action_names:
            ret[name] = []
            _run_action(self.config.interpreters, name, ret)

        # interpreter action can also be declared only by builder config,
        # but it is taken from interpreter settings key
        for name in self.interpreter_action_names:
            ret[name] = []
            try:
                ret[name] = self.config.interpreters[meta.interpreter.type][
                    "any"]["actions"]["setup"][name]
            except KeyError:
                pass
            try:
                ret[name] = self.config.interpreters[meta.interpreter.type][
                    self.interpreter_version]["actions"]["setup"][name]
            except KeyError:
                pass

        for name in self.app_action_names:
            ret[name] = []

            # global actions
            _run_action(self.config.interpreters, name, ret)

            # interpreter actions
            for version in ["any"] + [self.interpreter_version]:
                try:
                    cfg = self.config.interpreters[meta.interpreter.type][
                        version]
                except KeyError:
                    pass
                else:
                    _run_action(cfg, name, ret)

            # app metadata actions
            try:
                value = meta.actions.setup.get(name)
                if value:
                    ret[name] = value
            except AttributeError:
                pass
            else:
                log.debug(u"Got '%s' action from app meta" % name)

        for name in self.builder_action_names + \
                self.interpreter_action_names + self.app_action_names + \
                self.finalize_action_names:
            actions = ret.get(name, [])
            log.info(u"Commands for '%s' action:" % name)
            for action in actions:
                for line in action.splitlines():
                    log.info(u"- %s" % line)

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
                log.info(u"Got env variables for all interpreters: %s" % (
                    u", ".join([u"%s=%s" % (k, v) for k, v in value.items()])))
        except KeyError:
            pass
        for version in ["any"] + [self.interpreter_version]:
            try:
                value = self.config.interpreters[meta.interpreter.type][
                    version]["env"]
                if value:
                    ret.update(value)
            except KeyError:
                pass
            else:
                log.info(u"Got env variables from %s/%s: %s" % (
                    meta.interpreter.type, version,
                    u", ".join([u"%s=%s" % (k, v) for k, v in value.items()])))
                if meta.get(u"env"):
                    ret.update(meta.env)
                    log.info(u"Got env variables from app meta: " +
                             u", ".join([u"%s=%s" % (k, v)
                                         for k, v in value.items()]))

        if ret:
            log.info(u"Final env variables:")
            for key, value in ret.items():
                log.info(u"%s = %s" % (key, value))
        else:
            log.info(u"No env variables set")

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
        for version in ["any"] + [self.interpreter_version]:
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
            try:
                for pkg in meta.os[distro.distro_name()][
                        distro.distro_version()]["packages"]:
                    ret.add(pkg)
                    log.debug(u"Will install package '%s' from metadata for "
                              u"distribution %s, version "
                              u"%s" % (pkg, distro.distro_name(),
                                       distro.distro_version()))
            except KeyError:
                pass
        return ret

    def build_package(self, system_filename=None):
        """
        Build a package

        :param system_filename: Use given file as base system, if None empty
                                system image will be used.
        """
        if system_filename and self.storage.exists(system_filename):
            log.info(u"Starting package build using package "
                     u"%s" % system_filename)
        else:
            self.envs['UPAAS_FRESH_PACKAGE'] = 'true'
            system_filename = None
            log.info(u"Starting package build using empty system image")
            if not self.has_valid_os_image():
                try:
                    self.bootstrap_os()
                except exceptions.OSBootstrapError, e:
                    self.system_error(u"Error during os bootstrap: %s" % e)
                except StorageError, e:
                    self.system_error(u"Error during uploading OS image: "
                                      u"%s" % e)

        result = BuildResult()
        result.parent = system_filename
        result.interpreter_version = self.interpreter_version

        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_package_").encode("utf-8")
        workdir = os.path.join(directory, "workdir")
        chroot_homedir = self.config.apps.home
        os.mkdir(workdir, 0755)
        log.info(u"Working directory created at '%s'" % workdir)
        self.envs['HOME'] = chroot_homedir

        if not self.unpack_os(directory, workdir,
                              system_filename=system_filename):
            kill_and_remove_dir(directory)
            self.system_error(u"Unpacking OS image failed")
        log.info(u"OS image unpacked")
        result.progress = 10
        yield result

        log.info(u"Using interpreter %s, version %s" % (
            self.metadata.interpreter.type, self.interpreter_version))

        if not self.run_actions(self.builder_action_names, workdir):
            kill_and_remove_dir(directory)
            self.system_error(u"System actions failed")
        log.info(u"All builder actions executed")
        result.progress = 20
        yield result

        if not self.install_packages(workdir, self.os_packages):
            kill_and_remove_dir(directory)
            self.user_error(u"Failed to install OS packages")
        log.info(u"All packages installed")
        result.progress = 35
        yield result

        if not self.run_actions(self.interpreter_action_names, workdir, '/'):
            kill_and_remove_dir(directory)
            self.system_error(u"Interpreter actions failed")
        log.info(u"All interpreter actions executed")
        result.progress = 40
        yield result

        #TODO if building fails up to this point, then we can try retry it
        # on another builder (for a limited number of times)

        if system_filename:
            if not self.update(workdir, chroot_homedir):
                kill_and_remove_dir(directory)
                self.user_error(u"Updating repository failed")
        else:
            if not self.clone(workdir, chroot_homedir):
                kill_and_remove_dir(directory)
                self.user_error(u"Cloning repository failed")
        log.info(u"Application repository ready")
        result.progress = 45
        yield result

        if not self.write_files(workdir, chroot_homedir):
            kill_and_remove_dir(directory)
            self.user_error(u"Creating files from metadata failed")
        log.info(u"Created all files from metadata")
        result.progress = 48
        yield result

        if not self.run_actions(self.app_action_names, workdir,
                                chroot_homedir):
            self.user_error(u"Application actions failed")
            kill_and_remove_dir(directory)
        log.info(u"All application actions executed")
        result.progress = 85
        yield result

        if not self.run_actions(self.finalize_action_names, workdir, '/'):
            kill_and_remove_dir(directory)
            self.system_error(u"Finalize actions failed")
        log.info(u"All final actions executed")
        result.progress = 88
        yield result

        if not self.chown_app_dir(workdir, chroot_homedir):
            kill_and_remove_dir(directory)
            self.system_error(u"Setting file ownership failed")
        log.info(u"Owner of application directory updated")
        result.progress = 89
        yield result

        if not self.umount_filesystems(workdir):
            kill_and_remove_dir(directory)
            self.system_error(u"Failed to unmount filesystems")
        result.progress = 90
        yield result

        package_path = os.path.join(directory, "package")
        if not tar.pack_tar(workdir, package_path):
            kill_and_remove_dir(directory)
            self.system_error(u"Creating package file failed")
        result.bytes = os.path.getsize(package_path)
        log.info(u"Application package created, "
                 u"%s" % utils.bytes_to_human(result.bytes))
        result.progress = 93
        yield result

        checksum = calculate_file_sha256(package_path)
        log.info(u"Package checksum: %s" % checksum)
        result.progress = 96
        yield result

        try:
            self.storage.put(package_path, checksum)
        except StorageError, e:
            kill_and_remove_dir(directory)
            self.system_error(u"Package upload failed: %s" % e)

        kill_and_remove_dir(directory)

        result.progress = 100
        result.storage = self.storage.__class__.__name__
        result.filename = checksum
        result.checksum = checksum
        yield result

    def unpack_os(self, directory, workdir, system_filename=None):
        if not system_filename:
            system_filename = distro.distro_image_filename()

        os_image_path = os.path.join(directory, "os.image")
        log.info(u"Fetching OS image '%s'" % system_filename)
        try:
            self.storage.get(system_filename, os_image_path)
        except StorageError:
            log.error(u"Storage error while fetching OS image")
            return False
        else:
            log.info(u"Unpacking OS image")
            if not tar.unpack_tar(os_image_path, workdir):
                log.error(u"Error while unpacking OS image to '%s'" % workdir)
                return False
        return True

    def install_packages(self, workdir, packages):
        with Chroot(workdir):
            for name in packages:
                cmd = self.config.commands.install.cmd.replace("%package%",
                                                               name)
                try:
                    commands.execute(cmd,
                                     timeout=self.config.commands.timelimit,
                                     env=self.config.commands.install.env,
                                     output_loglevel=logging.INFO,
                                     strip_envs=True)
                except commands.CommandTimeout:
                    log.error(u"Installing package '%s' is taking to long, "
                              u"aborting" % name)
                    return False
                except commands.CommandFailed:
                    log.error(u"Installing package '%s' failed" % name)
                    return False
        return True

    def clone(self, workdir, homedir):
        log.info(u"Updating repository to '%s'" % homedir)
        with Chroot(workdir):
            for cmd in self.metadata.repository.clone:
                cmd = cmd.replace("%destination%", homedir)
                try:
                    commands.execute(cmd,
                                     timeout=self.config.commands.timelimit,
                                     env=self.metadata.repository.env,
                                     output_loglevel=logging.INFO,
                                     strip_envs=True)
                except commands.CommandTimeout:
                    log.error(u"Command is taking too long, aborting")
                    return False
                except commands.CommandFailed:
                    log.error(u"Command failed")
                    return False
        return True

    def update(self, workdir, homedir):
        log.info(u"Updating repository in '%s'" % homedir)
        with Chroot(workdir, workdir=homedir):
            for cmd in self.metadata.repository.update:
                cmd = cmd.replace("%destination%", homedir)
                try:
                    commands.execute(cmd,
                                     timeout=self.config.commands.timelimit,
                                     env=self.metadata.repository.env,
                                     output_loglevel=logging.INFO,
                                     strip_envs=True)
                except commands.CommandTimeout:
                    log.error(u"Command is taking too long, aborting")
                    return False
                except commands.CommandFailed:
                    log.error(u"Command failed")
                    return False
        return True

    def run_actions(self, actions, workdir, homedir='/'):
        for name in actions:
            log.info(u"Executing '%s' setup actions" % name)
            for cmd in self.actions[name]:
                with Chroot(workdir, workdir=homedir):
                    try:
                        commands.execute(
                            cmd, timeout=self.config.commands.timelimit,
                            env=self.envs, output_loglevel=logging.INFO,
                            strip_envs=True)
                    except commands.CommandTimeout:
                        log.error(u"Command is taking too long to execute, "
                                  u"aborting")
                        return False
                    except commands.CommandFailed, e:
                        log.error(u"Execution failed: %s" % e)
                        return False
        return True

    def chown_app_dir(self, workdir, homedir):
        cmd = "chown -R %s:%s %s" % (self.config.apps.uid,
                                     self.config.apps.gid, homedir)
        with Chroot(workdir):
            try:
                commands.execute(cmd, timeout=self.config.commands.timelimit,
                                 output_loglevel=logging.INFO, strip_envs=True)
            except commands.CommandTimeout:
                log.error(u"chown is taking too long to execute, aborting")
                return False
            except commands.CommandFailed:
                log.error(u"chown failed")
                return False
        return True

    def has_valid_os_image(self):
        """
        Check if OS image exists and is fresh enough.
        """
        if not self.storage.exists(distro.distro_image_filename()):
            return False

        os_mtime = self.storage.mtime(distro.distro_image_filename())
        delta = datetime.datetime.now() - os_mtime
        if delta > datetime.timedelta(days=self.config.bootstrap.maxage):
            log.info(u"OS image is too old (%d days)" % delta.days)
            self.storage.delete(distro.distro_image_filename())
            return False

        return True

    def bootstrap_os(self):
        """
        Bootstrap base OS image.
        """
        def _cleanup(directory):
            log.info(u"Removing directory '%s'" % directory)
            shutil.rmtree(directory)

        log.info(u"Bootstrapping new OS image")

        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_bootstrap_").encode("utf-8")
        log.debug(u"Created temporary directory for bootstrap at "
                  u"'%s'" % directory)

        for cmd in self.config.bootstrap.commands:
            cmd = cmd.replace("%workdir%", directory)
            try:
                commands.execute(cmd, timeout=self.config.bootstrap.timelimit,
                                 cwd=directory, env=self.config.bootstrap.env,
                                 strip_envs=True)
            except commands.CommandTimeout, e:
                log.error(u"Bootstrap was taking too long and it was killed")
                _cleanup(directory)
                raise exceptions.OSBootstrapError(e)
            except commands.CommandFailed, e:
                log.error(u"Bootstrap command failed")
                _cleanup(directory)
                raise exceptions.OSBootstrapError(e)
        log.info(u"All commands completed, installing packages")

        self.install_packages(directory, self.config.bootstrap.packages)
        log.info(u"Bootstrap done, packing image")

        archive_path = os.path.join(directory, "image.tar.gz")
        if not tar.pack_tar(directory, archive_path,
                            timeout=self.config.bootstrap.timelimit):
            _cleanup(directory)
            raise exceptions.OSBootstrapError(u"Tar error")
        else:
            log.info(u"Image packed, uploading")

        try:
            self.storage.put(archive_path, distro.distro_image_filename())
        except Exception, e:
            log.error(u"Upload failed: %s" % e)
            raise

        log.info(u"Image uploaded")
        _cleanup(directory)
        log.info(u"All done")

    def write_files(self, workdir, chroot_homedir):
        """
        Create all files specified in metadata 'files' section.
        """
        with Chroot(workdir, workdir=chroot_homedir):
            for path, content in self.metadata.files.items():
                basedir = os.path.dirname(path)
                if basedir and not os.path.exists(basedir):
                    try:
                        os.makedirs(basedir)
                    except Exception, e:
                        log.error(u"Can't create base directory (%s): %s" % (
                            basedir, e))
                        return False
                log.info(u"Creating metadata file: %s" % path)
                try:
                    with open(path, 'w') as out:
                        out.write(content)
                except Exception, e:
                    log.error(u"Can't write to '%s': %s" % (path, e))
                    return False
        return True

    def umount_filesystems(self, workdir):
        try:
            utils.umount_filesystems(workdir,
                                     timeout=self.config.bootstrap.timelimit)
        except commands.CommandTimeout, e:
            log.error(u"Can't umount filesystem, timeout reached")
            return False
        except commands.CommandFailed, e:
            log.error(u"Failed to umount filesystem: %s" % e)
            return False
        return True


class OSBuilder(Builder):

    def __init__(self, builder_config):
        """
        :param builder_config: Builder configuration.
        """
        self.config = builder_config
        self.storage = find_storage_handler(self.config)
