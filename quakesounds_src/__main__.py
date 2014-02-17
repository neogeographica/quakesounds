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

"""Audio processing pipeline for Quake sound samples.

quakesounds is a utility for easily ripping sound effects out of Quake pak
files and pushing them through a sequence of audio processing effects.

quakesounds will look for its configuration in :file:`quakesounds.cfg` in the
current working directory. Settings can also be specified on the command line
to add to or change the settings taken from the config file.

If there is no :file:`quakesounds.cfg` in the working directory, and no
settings on the command line, then quakesounds will create a default version
of the config file and exit.

If quakesounds did get a configuration, then it will reference those settings
to determine which pak files to read, what sounds to extract, and how to
process those sounds.

:func:`expak.process_resources` will be invoked to process each selected
sound. The converter function will spawn processes for commands, or for
a chain of commands, that can accept sound data on stdin and finally write
the processed result to a file.

"""

import re
import os
import sys
import glob
import resources
import config
import processing
from util import verbose_print, set_verbosity
from contextlib import contextmanager

__version__ = "1.0"

RES_PATH = "res"
DEFAULT_CFG = "default.cfg"
CFG_FILE = "quakesounds.cfg"
UTILITY_PATH_RE = re.compile("%UTILITY_PATH%(\S+)")

pause_on_exit = False


def app_home():
    """Find the home directory of the application, for use in config settings.

    Get the absolute path of this file and of the executed command (argv[0]).
    Compare those to figure out exactly how this application was invoked, and
    use that info to transform the command path into the directory that
    contains the application directory/archive. Return the result.

    :returns: absolute path to directory containing the application
    :rtype:   str

    """
    mainfile_abspath = os.path.abspath(__file__)
    cmd_abspath = os.path.abspath(sys.argv[0])
    cmd_dir = os.path.dirname(cmd_abspath)
    if cmd_abspath == mainfile_abspath:
        return os.path.dirname(cmd_dir)
    else:
        return cmd_dir

def add_sep(dir_path):
    """Modify a directory path to make it ready to be prepended to a filename.

    Uses of standard directory tokens in setting values in the default config
    need to be platform-agnostic. This means we want to remove worries about
    platform-specific directory separators between the token and the filename;
    the directory path represented by the token should be in a form that can
    be directly prepended to a filename.

    This function takes a directory path, appends a test file name to the
    path in a platform-appropriate way, deletes that test file name from the
    result, and returns that. In practice this is just a moderately-paranoid
    way to append a platform-specific directory separator to the given path.

    :param dir_path: directory path to make a modified version of
    :type dir_path:  str

    :returns: directory path ready to be prepended to filename
    :rtype:   str

    """
    return os.path.join(dir_path, "a")[:-1]

def set_pause_on_exit(cfg_table, path_table):
    global pause_on_exit
    """Set the pause-on-exit flag if requested.

    If the pause_on_exit key is not in the given config table, return.
    Otherwise make a temporary :class:`config.Settings` object from the given
    properties, and set the global pause-on-exit flag according to the value
    of that key evaluated as an optional bool.

    :param cfg_table:  table of user config properties
    :type cfg_table:   dict(str,str)
    :param path_table: table of system path properties
    :type path_table:  dict(str,str)

    """
    if 'pause_on_exit' in cfg_table:
        temp_settings = config.Settings(cfg_table, path_table)
        pause_on_exit = temp_settings.optional_bool('pause_on_exit')

def optional_pause_on_exit():
    """If the global pause-on-exit flag is set, wait for Enter keypress.

    """
    if pause_on_exit:
        prompt = "Press Enter to finish: "
        try:
            raw_input(prompt)
        except NameError:
            input(prompt)

def user_temp_dir(cfg_table, path_table):
    """Return the user-specified temp directory, if any.

    If the temp_dir key is not in the given config table, return None.
    Otherwise make a temporary :class:`config.Settings` object from the given
    properties, and return the value it gives for the temp_dir setting.

    :param cfg_table:  table of user config properties
    :type cfg_table:   dict(str,str)
    :param path_table: table of system path properties
    :type path_table:  dict(str,str)

    :returns: user-specified temp directory if any, None otherwise
    :rtype:   str or None

    """
    if 'temp_dir' in cfg_table:
        temp_settings = config.Settings(cfg_table, path_table)
        return temp_settings.eval('temp_dir')
    else:
        return None

@contextmanager
def out_fd_if_not_exist(path):
    """Context manager to create/open/close an FD to write a new file.

    In order to make sure that we don't overwrite an existing file, we need
    to use os.open rather than the built-in open. This context manager handles
    doing that create+open, returning the FD, and then closing the FD on
    scope exit.

    :param path: path to file to create and open for writing
    :type path:  str

    :returns: file descriptor of file opened for writing
    :rtype:   int

    :raises OSError: if file can't be opened, which includes the case with
                     errno set to errno.EEXIST if file already exists at path

    """
    out_fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        yield out_fd
    finally:
        os.close(out_fd)

def create_config_file(cfg_path, resource_dir):
    """Create an instance of the default config file in the working directory.

    Read the default config template :const:`DEFAULT_CFG` from the internal
    resources directory. Modify it to contain appropriate paths for utilities,
    and write the result to the given path.

    :param cfg_path:     path where the config file will be created
    :type cfg_path:      str
    :param resource_dir: directory containing internal resources
    :type resource_dir:  str

    :returns: True if config file was successfully created, False otherwise
    :rtype:   bool

    :raises OSError: if the config instance can't be created for reasons other
                     than "file already exists"

    """
    def utility_path(match):
        """Process matches for "utility path" in config template.

        Get the utility name from the match object. Look for a file named
        <utility_name>_exename.txt in the resource directory; if it exists,
        get the platform-appropriate executable name from its contents,
        otherwise the executable name is the same as the utility name.

        If the executable name exists in the internal resource directory,
        prepend "%qs_internal%" to it before returning it. (Otherwise the
        default path will just be the utility name itself; ideally that
        utility will be installed in the user's executables path.)

        :param match: match object for discovered utility path
        :type match:  :class:`SRE_Match`

        :returns: utility path to use in the instantiated config file
        :rtype:   str

        """
        utility_name = match.group(1)
        exe_name = os.path.join(resource_dir, utility_name + "_exename.txt")
        if os.path.exists(exe_name):
            with open(exe_name) as instream:
                utility_name = instream.read().strip()
        internal_path = os.path.join(resource_dir, utility_name)
        if os.path.exists(internal_path):
            return "%qs_internal%" + utility_name
        else:
            return utility_name
    try:
        with open(os.path.join(resource_dir, DEFAULT_CFG), 'r') as instream:
            default_cfg = instream.read()
            cfg = UTILITY_PATH_RE.sub(utility_path, default_cfg)
            with out_fd_if_not_exist(cfg_path) as out_fd:
                os.write(out_fd, cfg.encode('utf-8'))
    except OSError as e:
        sys.stderr.write("Unable to create default config file at {0}\n".format(
            cfg_path))
        if e.errno != errno.EEXIST:
            raise
        sys.stderr.write("File already exists at that path.\n")
        return False
    print("Default config file created at {0}".format(cfg_path))
    return True

def print_qs_info(resource_dir):
    """Print info about this program and the bundled utilities.

    Print the quakesounds version. Also look for info files created by the
    make process (when bundling utilities), and print their contents if they
    exist.

    :param resource_dir: directory containing internal resources
    :type resource_dir:  str

    """
    print("\n* quakesounds version {0} *\n".format(__version__))
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
    """Verbose-print info about the additional Python modules used.

    Get info from the processing and resources modules, to see whether they
    are using bundled or external versions of :mod:`expak` and
    :mod:`pkg_resources`; print that info if verbose.

    """
    verbose_print("Modules used:")
    if processing.expak_source == "system":
        verbose_print("    expak: from system library (version {0})".format(
            processing.expak_version))
    else:
        verbose_print("    expak: not found in system library; "
                      "using bundled (version {0})".format(
            processing.expak_version))
    if resources.pkg_resources_source == "system":
        verbose_print("    pkg_resources: from system library")
    else:
        verbose_print("    pkg_resources: not found in system library; "
                      "using bundled")

def default_sound_name(resource_name):
    """Function for generating sound_name when not specified in file table.

    Strip the file extension, split the resource name on slashes, and rejoin
    it using platform-specific directory separators.

    :param resource_name: resource name from the pak file
    :type resource_name:  str

    :returns: default sound_name value for the resource
    :rtype:   str

    """
    dot_pos = resource_name.rfind(".")
    if dot_pos != -1:
        base_name = resource_name[0:dot_pos]
    else:
        base_name = resource_name
    return os.path.join(*base_name.split("/"))

def main(argv):
    """Control flow for reading the config settings and processing sounds.

    Get the configuration from the file :const:`CFG_FILE` (if it exists) and
    update the configuration from command-line args (if any).

    Extract internal resources for the duration of the remaining work; will be
    automatically cleaned up afterward.

    If no config, instantiate a default config and exit.

    Construct a :class:`config.Settings` object, and read the file table.

    Process the selected sounds, and then print any that were not found.

    :param argv: command-line arguments
    :type argv:  iterable(str)

    :returns: 1 if an error prevents an attempt at processing or instantiation
              of the default config file; 0 otherwise
    :rtype:   int

    :raises config.BadSetting: if a necessary setting is undefined

    :raises config.TooManySubstitutions: if a setting-evaluation loop goes on
                                         for too many iterations

    """

    # Grab a couple of useful paths.
    qs_home = app_home()
    qs_working_dir = os.getcwd()

    # Read the config file (if it exists).
    cfg_path = os.path.join(qs_working_dir, CFG_FILE)
    cfg_table = config.read_cfg(cfg_path)

    # Apply any command-line args.
    config.update_cfg(argv, cfg_table)

    # Set pause_on_exit appropriately, and extract packaged resources for the
    # duration of the remaining work.
    path_table = {'qs_home' : add_sep(qs_home),
                  'qs_working_dir' : add_sep(qs_working_dir)}
    set_pause_on_exit(cfg_table, path_table)
    temp_dir = user_temp_dir(cfg_table, path_table)
    with resources.temp_copies(RES_PATH, temp_dir) as resource_dir:

        # Print info about this program and internal utilities.
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

        # Get the sound selections and name mappings.
        targets_path = settings.eval('targets_path')
        targets_table = config.read_cfg(targets_path, default_sound_name)
        if not targets_table:
            if os.path.exists(targets_path):
                print("Nothing to process in the targets table at path: {0}".format(
                    targets_path))
                return 0
            else:
                print("No targets table found at path: {0}".format(targets_path))
                return 1

        # Do that voodoo that we do.
        if not processing.go(settings, targets_table):
            return 1

        # Inform of leftovers.
        if targets_table:
            print("Not processed:")
            for t in targets_table:
                print("    {0}".format(t))
        else:
            print("All selections processed.")
        print("")

    # Done!
    return 0


try:
    sys.exit(main(sys.argv[1:]))
except (config.BadSetting, config.TooManySubstitutions) as e:
    sys.stderr.write("\nError: " + str(e) + "\n")
    sys.exit(1)
finally:
    optional_pause_on_exit()
