# -*- coding: utf-8 -*-
#
# Copyright 2013 Joel Baxter
#
# This file is part of quakesounds.
#
# quakesounds is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# quakesounds is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with quakesounds.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import sys
import glob
import resources
import config
import processing
from contextlib import contextmanager
from util import verbose_print, set_verbosity

VERSION = "1.0"

RES_PATH = "res"
DEFAULT_CFG = "default.cfg"
CFG_FILE = "quakesounds.cfg"

UTILITY_PATH_TOKEN = re.compile("%UTILITY_PATH%(\S+)")


# Find the app's home dir; be bulletproof against a few different ways of
# invoking the application, zipped or not.
def app_home():
    mainfile_abspath = os.path.abspath(__file__)
    cmd_abspath = os.path.abspath(sys.argv[0])
    cmd_dir = os.path.dirname(cmd_abspath)
    if cmd_abspath == mainfile_abspath:
        return os.path.dirname(cmd_dir)
    else:
        return cmd_dir

def add_sep(path):
    return os.path.join(path, "a")[:-1]

# Get the user-specific temp directory, if any.
def user_temp_dir(cfg_table, path_table):
    if 'temp_dir' in cfg_table:
        return config.Settings(cfg_table, path_table).eval('temp_dir')
    else:
        return None

@contextmanager
def out_fd_if_not_exist(path):
    out_fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        yield out_fd
    finally:
        os.close(out_fd)

def create_config_file(cfg_path, resource_dir):
    def utility_path(match):
        resource = match.group(1)
        exe_name = os.path.join(resource_dir, resource + "_exename.txt")
        if os.path.exists(exe_name):
            with open(exe_name) as instream:
                resource = instream.read().strip()
        internal_path = os.path.join(resource_dir, resource)
        if os.path.exists(internal_path):
            return "%qs_internal%" + resource
        else:
            return resource
    try:
        with open(os.path.join(resource_dir, DEFAULT_CFG), 'r') as instream:
            default_cfg = instream.read()
            cfg = UTILITY_PATH_TOKEN.sub(utility_path, default_cfg)
            with out_fd_if_not_exist(cfg_path) as out_fd:
                os.write(out_fd, cfg)
    except OSError as e:
        sys.stderr.write("Unable to create default config file at %s\n" %
                         cfg_path)
        if e.errno != errno.EEXIST:
            raise
        sys.stderr.write("File already exists at that path.\n")
        return False
    print("Default config file created at %s" % cfg_path)
    return True

def print_qs_info(resource_dir):
    print("\n* quakesounds version %s *\n" % VERSION)
    info_files = glob.glob(os.path.join(resource_dir, "*_info.txt"))
    info = ""
    for path in info_files:
        with open(path, 'r') as instream:
            info = info + "    " + instream.read()
    if not info:
        print("No internally bundled sound utilities.")
    else:
        print("Internally bundled sound utilities:")
        print(info.rstrip())

def print_modules_info():
    verbose_print("Modules used:")
    if processing.expak_source == "system":
        verbose_print("    expak: from system library, version " +
                      processing.expak_version)
    else:
        verbose_print("    expak: not found in system library; using bundled version " +
                      processing.expak_version)
    if resources.pkg_resources_source == "system":
        verbose_print("    pkg_resources: from system library")
    else:
        verbose_print("    pkg_resources: not found in system library; using bundled")

def main(argv):

    # Grab a couple of useful paths.
    qs_home = app_home()
    qs_working_dir = os.getcwd()

    # Read the config file (if it exists).
    cfg_path = os.path.join(qs_working_dir, CFG_FILE)
    cfg_table = config.read_cfg(cfg_path)

    # Apply any command-line args.
    config.update_cfg(argv, cfg_table)

    # Extract packaged resources for the duration of the remaining work.
    path_table = {'qs_home' : add_sep(qs_home),
                  'qs_working_dir' : add_sep(qs_working_dir)}
    temp_dir = user_temp_dir(cfg_table, path_table)
    with resources.temp_copies(RES_PATH, temp_dir) as resource_dir:

        print_qs_info(resource_dir)

        # Do we have any config? If not, create a default config file and exit.
        if not cfg_table:
            print("No settings in config file or on command line.")
            if not create_config_file(cfg_path, resource_dir):
                return 1
            print("Edit the config (if you like) then run quakesounds again.")
            return 0

        # Create the settings-evaluator.
        path_table['qs_internal'] = add_sep(resource_dir)
        settings = config.Settings(cfg_table, path_table)

        # Set verbosity for the remainder of the run, and print module info
        # if verbose.
        set_verbosity(settings)
        print_modules_info()
        print("")

        # Get the resources->files mapping.
        def default_base_name(orig_name):
            dot_pos = orig_name.rfind(".")
            if dot_pos != -1:
                base_name = orig_name[0:dot_pos]
            else:
                base_name = orig_name
            return os.path.join(*base_name.split("/"))
        files_path = settings.eval('files_path')
        file_table = config.read_cfg(files_path, default_base_name)
        if not file_table:
            if os.path.exists(files_path):
                print("Nothing to process in the file table at path: %s" % files_path)
                return 0
            else:
                print("No file table found at path: %s" % files_path)
                return 1

        # Do that voodoo that we do.
        processing.go(settings, file_table)

        # Inform of leftovers.
        if file_table:
            print("Not processed:")
            for f in file_table:
                print("    %s" % f)
	else:
            print("All selections processed.")
        print("")

        # Wait if requested.
        if settings.optional_bool('pause_on_exit'):
            raw_input("Press Enter to finish: ")

    # Done!
    return 0


try:
    sys.exit(main(sys.argv[1:]))
except (config.BadSetting, config.TooManySubstitutions) as e:
    sys.stderr.write("\nError: " + str(e) + "\n")
    sys.exit(1)

