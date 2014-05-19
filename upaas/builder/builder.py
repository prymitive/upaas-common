# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import tempfile
import datetime
import logging

from timestring import Date

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

        # package filename
        self.filename = None
        # package checksum
        self.checksum = None
        # package size
        self.bytes = 0

        self.distro_name = distro.distro_name()
        self.distro_version = distro.distro_version()
        self.distro_arch = distro.distro_arch()

        # information about last commit in VCS (if available)
        self.vcs_revision = {}


class Builder(object):

    # TODO stage decorators
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
        self.envs = {}
        self.actions = {}
        self.os_packages = []

        self.interpreter_version = utils.select_best_version(self.config,
                                                             metadata)

        self.current_revision = None

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
                log.debug("Got '%s' action" % name)

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
                log.debug("Got '%s' action from app meta" % name)

        for name in self.builder_action_names + \
                self.interpreter_action_names + self.app_action_names + \
                self.finalize_action_names:
            actions = ret.get(name, [])
            log.info("Commands for '%s' action:" % name)
            for action in actions:
                for line in action.splitlines():
                    log.info("- %s" % line)

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
                log.info("Got env variables for all interpreters: %s" % (
                    ", ".join(["%s=%s" % (k, v) for k, v in list(
                        value.items())])))
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
                log.info("Got env variables from %s/%s: %s" % (
                    meta.interpreter.type, version,
                    ", ".join(["%s=%s" % (k, v) for k, v in list(
                        value.items())])))
                if meta.get("env"):
                    ret.update(meta.env)
                    log.info("Got env variables from app meta: " +
                             ", ".join(["%s=%s" % (k, v)
                                       for k, v in list(value.items())]))

        if ret:
            log.info("Final env variables:")
            for key, value in list(ret.items()):
                log.info("%s = %s" % (key, value))
        else:
            log.info("No env variables set")

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
                log.debug("Will install package '%s' from builder config "
                          "for all interpreters" % pkg)
        except KeyError:
            pass
        for version in ["any"] + [self.interpreter_version]:
            try:
                for pkg in self.config.interpreters[meta.interpreter.type][
                        version]["packages"]:
                    ret.add(pkg)
                    log.debug("Will install package '%s' from builder config "
                              "for interpreter version '%s'" % (pkg, version))
            except KeyError:
                pass
            try:
                for pkg in meta.os[distro.distro_name()]["packages"]:
                    ret.add(pkg)
                    log.debug("Will install package '%s' from metadata for "
                              "distribution %s" % (pkg, distro.distro_name()))
            except (KeyError, TypeError):
                pass
            try:
                for pkg in meta.os[distro.distro_name()][
                        distro.distro_version()]["packages"]:
                    ret.add(pkg)
                    log.debug("Will install package '%s' from metadata for "
                              "distribution %s, version "
                              "%s" % (pkg, distro.distro_name(),
                                      distro.distro_version()))
            except (KeyError, TypeError):
                pass
        return ret

    def build_package(self, system_filename=None, interpreter_version=None,
                      current_revision=None):
        """
        Build a package

        :param system_filename: Use given file as base system, if None empty
                                system image will be used.
        :param interpreter_version: Use specific interpreter version, only used
                                    for fresh packages.
        :param current_revision: VCS revision id from current package.
        """
        if interpreter_version:
            self.interpreter_version = interpreter_version
            log.info("Using forced interpreter version: "
                     "%s" % interpreter_version)

        self.storage = find_storage_handler(self.config.storage.handler,
                                            self.config.storage.settings)
        if system_filename and self.storage.exists(system_filename):
            log.info("Starting package build using package "
                     "%s" % system_filename)
            if current_revision:
                log.info("VCS revision from current package: "
                         "%s" % current_revision)
                self.current_revision = current_revision
        else:
            if system_filename:
                log.warning("Requested base package file not found, using "
                            "empty system image")
            self.envs['UPAAS_FRESH_PACKAGE'] = 'true'
            system_filename = None
            log.info("Starting package build using empty system image")
            if not self.has_valid_os_image():
                try:
                    self.bootstrap_os()
                except exceptions.OSBootstrapError as e:
                    self.system_error("Error during os bootstrap: %s" % e)
                except StorageError as e:
                    self.system_error("Error during uploading OS image: "
                                      "%s" % e)

        if not self.interpreter_version:
            self.user_error("Unsupported interpreter version")

        self.actions.update(self.parse_actions(self.metadata))
        self.envs.update(self.parse_envs(self.metadata))
        self.os_packages += self.parse_packages(self.metadata)

        result = BuildResult()
        result.parent = system_filename
        result.interpreter_version = self.interpreter_version

        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_package_")
        workdir = os.path.join(directory, "workdir")
        chroot_homedir = self.config.apps.home
        os.mkdir(workdir, 0o755)
        log.info("Working directory created at '%s'" % workdir)
        self.envs['HOME'] = chroot_homedir

        if not self.unpack_os(directory, workdir,
                              system_filename=system_filename):
            kill_and_remove_dir(directory)
            self.system_error("Unpacking OS image failed")
        log.info("OS image unpacked")
        result.progress = 10
        yield result

        log.info("Using interpreter %s, version %s" % (
            self.metadata.interpreter.type, self.interpreter_version))

        if not self.run_actions(self.builder_action_names, workdir):
            kill_and_remove_dir(directory)
            self.system_error("System actions failed")
        log.info("All builder actions executed")
        result.progress = 20
        yield result

        if not self.install_packages(workdir, self.os_packages):
            kill_and_remove_dir(directory)
            self.user_error("Failed to install OS packages")
        log.info("All packages installed")
        result.progress = 35
        yield result

        if not self.run_actions(self.interpreter_action_names, workdir, '/'):
            kill_and_remove_dir(directory)
            self.system_error("Interpreter actions failed")
        log.info("All interpreter actions executed")
        result.progress = 40
        yield result

        # TODO if building fails up to this point, then we can try retry it
        # on another builder (for a limited number of times)

        if system_filename:
            if not self.update(workdir, chroot_homedir):
                kill_and_remove_dir(directory)
                self.user_error("Updating repository failed")
        else:
            if not self.clone(workdir, chroot_homedir):
                kill_and_remove_dir(directory)
                self.user_error("Cloning repository failed")
        log.info("Application repository ready")
        result.progress = 45
        yield result

        result.vcs_revision = self.vcs_info(workdir, chroot_homedir)
        result.progress = 46
        yield result

        if not self.write_files(workdir, chroot_homedir):
            kill_and_remove_dir(directory)
            self.user_error("Creating files from metadata failed")
        log.info("Created all files from metadata")
        result.progress = 49
        yield result

        if not self.run_actions(self.app_action_names, workdir,
                                chroot_homedir):
            self.user_error("Application actions failed")
            kill_and_remove_dir(directory)
        log.info("All application actions executed")
        result.progress = 85
        yield result

        if not self.run_actions(self.finalize_action_names, workdir, '/'):
            kill_and_remove_dir(directory)
            self.system_error("Finalize actions failed")
        log.info("All final actions executed")
        result.progress = 88
        yield result

        if not self.chown_app_dir(workdir, chroot_homedir):
            kill_and_remove_dir(directory)
            self.system_error("Setting file ownership failed")
        log.info("Owner of application directory updated")
        result.progress = 89
        yield result

        if not self.umount_filesystems(workdir):
            kill_and_remove_dir(directory)
            self.system_error("Failed to unmount filesystems")
        result.progress = 90
        yield result

        package_path = os.path.join(directory, "package")
        if not tar.pack_tar(workdir, package_path):
            kill_and_remove_dir(directory)
            self.system_error("Creating package file failed")
        result.bytes = os.path.getsize(package_path)
        log.info("Application package created, "
                 "%s" % utils.bytes_to_human(result.bytes))
        result.progress = 93
        yield result

        checksum = calculate_file_sha256(package_path)
        log.info("Package checksum: %s" % checksum)
        result.progress = 96
        yield result

        try:
            self.storage.put(package_path, checksum)
        except StorageError as e:
            kill_and_remove_dir(directory)
            self.system_error("Package upload failed: %s" % e)

        kill_and_remove_dir(directory)

        result.progress = 100
        result.filename = checksum
        result.checksum = checksum
        yield result

    def unpack_os(self, directory, workdir, system_filename=None):
        empty_os_image = False
        if not system_filename:
            system_filename = distro.distro_image_filename()
            empty_os_image = True

        os_image_path = os.path.join(directory, "os.image")
        log.info("Fetching OS image '%s'" % system_filename)
        try:
            self.storage.get(system_filename, os_image_path)
        except StorageError:
            log.error("Storage error while fetching OS image")
            return False
        else:
            log.info("Unpacking OS image")
            if not tar.unpack_tar(os_image_path, workdir):
                log.error("Error while unpacking OS image to '%s'" % workdir)
                return False
        # verify if os is working
        log.info("Checking if OS image is working (will execute /bin/true)")
        try:
            with Chroot(workdir):
                commands.execute('/bin/true',
                                 timeout=self.config.commands.timelimit,
                                 output_loglevel=logging.INFO)
        except Exception as e:
            log.error("Broken OS image! /bin/true failed: %s" % e)
            if empty_os_image:
                try:
                    self.storage.delete(system_filename)
                except StorageError as e:
                    log.error("Storage error while deleting OS image: %s" % e)
                else:
                    log.info("Deleted broken OS image from storage")
                    self.bootstrap_os()
                    return self.unpack_os(directory, workdir,
                                          system_filename=system_filename)
            return False
        else:
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
                    log.error("Installing package '%s' is taking to long, "
                              "aborting" % name)
                    return False
                except commands.CommandFailed:
                    log.error("Installing package '%s' failed" % name)
                    return False
        return True

    def clone(self, workdir, homedir):
        log.info("Updating repository to '%s'" % homedir)
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
                    log.error("Command is taking too long, aborting")
                    return False
                except commands.CommandFailed:
                    log.error("Command failed")
                    return False
        return True

    def vcs_info(self, workdir, homedir):
        ret = {}
        log.info("Extracting information about last commit")
        with Chroot(workdir, workdir=homedir):
            def vcs_cmd(name, cmd, replace=None):
                name = 'repository.revision.%s' % name
                if hasattr(cmd, '__call__'):
                    cmd = cmd()
                if replace:
                    for (rold, rnew) in replace:
                        cmd = cmd.replace(rold, rnew)
                env = self.metadata.repository.env.copy()
                env['LANG'] = 'C.UTF-8'
                env['LC_ALL'] = 'C.UTF-8'
                try:
                    _, output = commands.execute(
                        cmd, timeout=self.config.commands.timelimit, env=env,
                        output_loglevel=logging.INFO, strip_envs=True)
                except commands.CommandTimeout:
                    log.error("%s command is taking too long, aborting" % name)
                except commands.CommandFailed:
                    log.error("%s command failed" % name)
                else:
                    return ''.encode('utf-8').join(output).rstrip(
                        '\n'.encode('utf-8'))

            ret = {
                'id': vcs_cmd('id', self.metadata.repository.revision.id),
                'author': vcs_cmd('author',
                                  self.metadata.repository.revision.author),
                'date': vcs_cmd('date',
                                self.metadata.repository.revision.date),
                'description': vcs_cmd(
                    'description',
                    self.metadata.repository.revision.description),
            }

            if self.current_revision and self.current_revision != ret['id']:
                ret['changelog'] = vcs_cmd(
                    'changelog',
                    self.metadata.repository.revision.changelog,
                    replace=[
                        ('%old%', self.current_revision.rstrip('\n')),
                        ('%new%', ret['id'].rstrip('\n')),
                    ])

        if 'date' in ret:
            try:
                ret['date'] = Date(ret['date']).date
            except ValueError:
                log.warning("Can't convert '%s' to date" % ret['date'])
                del ret['date']

        return ret

    def update(self, workdir, homedir):
        log.info("Updating repository in '%s'" % homedir)
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
                    log.error("Command is taking too long, aborting")
                    return False
                except commands.CommandFailed:
                    log.error("Command failed")
                    return False
        return True

    def run_actions(self, actions, workdir, homedir='/'):
        for name in actions:
            log.info("Executing '%s' setup actions" % name)
            for cmd in self.actions[name]:
                with Chroot(workdir, workdir=homedir):
                    try:
                        commands.execute(
                            cmd, timeout=self.config.commands.timelimit,
                            env=self.envs, output_loglevel=logging.INFO,
                            strip_envs=True)
                    except commands.CommandTimeout:
                        log.error("Command is taking too long to execute, "
                                  "aborting")
                        return False
                    except commands.CommandFailed as e:
                        log.error("Execution failed: %s" % e)
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
                log.error("chown is taking too long to execute, aborting")
                return False
            except commands.CommandFailed:
                log.error("chown failed")
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
            log.info("OS image is too old (%d days)" % delta.days)
            self.storage.delete(distro.distro_image_filename())
            return False

        return True

    def bootstrap_os(self):
        """
        Bootstrap base OS image.
        """
        log.info("Bootstrapping new OS image")

        # directory is encoded into string to prevent unicode errors
        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_bootstrap_")
        log.debug("Created temporary directory for bootstrap at "
                  "'%s'" % directory)

        for cmd in self.config.bootstrap.commands:
            cmd = cmd.replace("%workdir%", directory)
            try:
                commands.execute(cmd, timeout=self.config.bootstrap.timelimit,
                                 cwd=directory, env=self.config.bootstrap.env,
                                 strip_envs=True)
            except commands.CommandTimeout as e:
                log.error("Bootstrap was taking too long and it was killed")
                kill_and_remove_dir(directory)
                raise exceptions.OSBootstrapError(e)
            except commands.CommandFailed as e:
                log.error("Bootstrap command failed")
                kill_and_remove_dir(directory)
                raise exceptions.OSBootstrapError(e)
        log.info("All commands completed, installing packages")

        self.install_packages(directory, self.config.bootstrap.packages)
        log.info("Bootstrap done, packing image")

        archive_path = os.path.join(directory, "image.tar.gz")
        if not tar.pack_tar(directory, archive_path,
                            timeout=self.config.bootstrap.timelimit):
            kill_and_remove_dir(directory)
            raise exceptions.OSBootstrapError("Tar error")
        else:
            log.info("Image packed, uploading")

        try:
            self.storage.put(archive_path, distro.distro_image_filename())
        except Exception as e:
            log.error("Upload failed: %s" % e)
            raise

        log.info("Image uploaded")
        kill_and_remove_dir(directory)
        log.info("All done")

    def write_files(self, workdir, chroot_homedir):
        """
        Create all files specified in metadata 'files' section.
        """
        with Chroot(workdir, workdir=chroot_homedir):
            for path, content in list(self.metadata.files.items()):
                basedir = os.path.dirname(path)
                if basedir and not os.path.exists(basedir):
                    try:
                        os.makedirs(basedir)
                    except Exception as e:
                        log.error("Can't create base directory (%s): %s" % (
                            basedir, e))
                        return False
                log.info("Creating metadata file: %s" % path)
                try:
                    with open(path, 'w') as out:
                        out.write(content)
                except Exception as e:
                    log.error("Can't write to '%s': %s" % (path, e))
                    return False
        return True

    def umount_filesystems(self, workdir):
        try:
            utils.umount_filesystems(workdir,
                                     timeout=self.config.bootstrap.timelimit)
        except commands.CommandTimeout as e:
            log.error("Can't umount filesystem, timeout reached")
            return False
        except commands.CommandFailed as e:
            log.error("Failed to umount filesystem: %s" % e)
            return False
        return True


class OSBuilder(Builder):

    def __init__(self, builder_config):
        """
        :param builder_config: Builder configuration.
        """
        self.config = builder_config
        self.storage = find_storage_handler(self.config.storage.handler,
                                            self.config.storage.settings)
