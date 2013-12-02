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

"""Process resources from pak files, according to the provided settings."""

import subprocess
import sys
import os
import errno
import threading
from util import verbose_print

# Use the system-installed :mod:`expak` module if it is available. If not, try
# to load a bundled-in copy from this application package. Save indicators of
# which expak was used and what its version string is.
saved_sys_path = sys.path
sys.path = sys.path[1:]
try:
    import expak
    sys.path = saved_sys_path
    expak_source = "system"
except ImportError:
    sys.path = saved_sys_path
    import expak
    expak_source = "bundled"
expak_version = expak.__version__


def ensure_dir(dir):
    """Atomically create a directory if it doesn't exist.

    :param dir: directory path to create if necessary
    :type dir:  str

    :returns: True if the directory was created, False if it already exists
    :rtype:   bool

    :raises OSError: if the directory creation fails for reasons other than
                     "directory already exists"

    """
    try:
        os.makedirs(dir)
        return True
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        return False

def set_working_dir(settings):
    """Apply the out_working_dir setting.

    Create the directory indicated by the out_working_dir setting if it
    doesn't exist, then change the working directory to that directory.

    :param settings: settings
    :type settings:  :class:`config.Settings`

    :raises config.BadSetting: if a token name discovered during setting
                               evaluation references an undefined setting

    :raises config.TooManySubstitutions: if token substitution goes on for too
                                         many iterations

    """
    if settings.is_defined('out_working_dir'):
        out_working_dir = settings.eval('out_working_dir')
        if out_working_dir:
            verbose_print("converter working directory is " + out_working_dir)
            if ensure_dir(out_working_dir):
                verbose_print("created directory: " + out_working_dir)
            os.chdir(out_working_dir)

def valid_command_stage(settings, stage_args, is_last_stage):
    """Test command-stage elements for possible problems.

    Run through the few validation checks that are possible without using any
    knowledge of the specific sound utility behaviors. This includes doing a
    test of the final token substitution that will be done when the converter
    function runs. If an issue is found, print about it to stderr, and if that
    issue qualifies as a fatal error then return False. Finally, return True.

    :param settings:      settings
    :type settings:       :class:`config.Settings`
    :param stage_args:    list of command-stage elements
    :type stage_args:     list(str)
    :param is_last_stage: whether this is the final stage of the command
    :type is_last_stage:  bool

    :returns: whether an error was discovered
    :rtype:   bool

    :raises config.BadSetting: if a token name discovered during evaluation of
                               the converter setting references an undefined
                               setting

    :raises config.TooManySubstitutions: if token substitution goes on for too
                                         many iterations

    """
    test_var_table = {'sound_name': "%sound_name%", 'write_to': "%write_to%"}
    test_stage_args = [settings.eval_finalize('converter', a, test_var_table)
                       for a in stage_args]
    if not test_stage_args:
        sys.stderr.write("    Error: converter command stage is empty\n")
        return False
    if not test_stage_args[0]:
        sys.stderr.write("    Error: "
                         "first element of converter command stage is empty\n")
        return False
    if test_stage_args[0] == "%write_to%":
        if len(test_stage_args) != 2:
            sys.stderr.write("    Error: "
                             "%write_to% command takes one argument\n")
            return False
        if not is_last_stage:
            # This is just a warning, so we'll still return True.
            sys.stderr.write("    Warning: "
                             "the rest of this stage after the %write_to% "
                             "command will be ignored\n")
    return True

def writer_func(instream, outpath):
    """Function used to implement %write_to% when it needs its own thread.

    Open the indicated output path for binary write, and write to it whatever
    is read from the input stream.

    :param instream: binary file object to read from
    :type instream:  file
    :param outpath:  output path to write to
    :type outpath:   str

    """
    with open(outpath, 'wb') as outstream:
        outstream.write(instream.read())

def make_converter(settings):
    """Create the converter command used to process every selected sound.

    Look up the converter command value in the settings. Perform the initial
    token substitution for user-defined settings, and split the command into
    stages. Validate the stages. Return a definition of a function that can be
    used as an :mod:`expak` converter function, which will handle doing final
    token substitutions on the stage definitions, spawning the stages,
    connecting their pipes, and sending the sound data into the first stage.

    :param settings: settings
    :type settings:  :class:`config.Settings`

    :returns: converter function, or None if the converter command is invalid
    :rtype:   function(str,str) or None

    :raises config.BadSetting: if a token name discovered during evaluation of
                               the converter setting references an undefined
                               setting

    :raises config.TooManySubstitutions: if token substitution goes on for too
                                         many iterations

    """
    # Get the raw value of the converter setting and see if it has token
    # markers. If it does, or if the dumb_converter_eval setting is enabled,
    # then we will evaluate it normally. Otherwise treat it as the name of
    # another setting to evaluate. In either case make sure that %sound_name%
    # and %write_to% tokens are skipped in this first evaluation.
    raw_converter_val = settings.raw_cfg('converter')
    raw_has_tokens = (raw_converter_val.find("%") != -1)
    reserved_names = ['sound_name', 'write_to']
    if raw_has_tokens or settings.optional_bool('dumb_converter_eval'):
        command = settings.eval_prep('converter', reserved_names)
    else:
        command = settings.eval_prep(raw_converter_val, reserved_names)
    # Split the command into stages at each pipe symbol; split the stages into
    # stage elements (executable+args) at each comma.
    command_stages = [[a.strip() for a in s.split(",")]
                      for s in command.split("|")]
    # Validate.
    num_stages = len(command_stages)
    for stage in range(num_stages):
        verbose_print("converter stage %d of %d:" % (stage + 1, num_stages))
        stage_args = command_stages[stage]
        verbose_print("    " + " ".join(stage_args))
        if not valid_command_stage(settings, stage_args,
                                   stage == num_stages - 1):
            return None
    # Stages look good, so let's define a converter function to use them!
    skip_makedir = settings.optional_bool('skip_preconverter_makedir')
    def converter(orig_data, sound_name):
        """Converter function for processing sound data with a command chain.

        Make necessary subdirectories for the desired output file.

        Do final token substitution on the command stages, and spawn them
        as processes (in the case of external utilities) or a thread (in the
        case of a "%write_to%" command). Hook the command stages together,
        piping stdout from one into stdin of the next. Write the sound data
        to the stdin of the first stage.

        Note that any exceptions raised while executing a converter function
        will only abort that converter invocation, not the entire program.
        However although this function can in theory raise BadSetting or
        TooManySubstitutions, in practice the command stage validation should
        have already caught such errors.

        :param orig_data:  sound data from the pak file
        :type orig_data:   str
        :param sound_name: mapped name for the sound resource; usually the
                           basename of the file to create
        :type sound_name:  str

        :returns: True
        :rtype:   bool

        :raises config.BadSetting: if a token name discovered during final
                                   evaluation of the converter setting
                                   references an undefined setting

        :raises config.TooManySubstitutions: if token substitution goes on for
                                             too many iterations

        """
        verbose_print("    processing " + sound_name)
        # Unless the settings tell us not to, let's interpret the name as a
        # path and make sure that the necessary directories exist.
        if not skip_makedir:
            out_dir = os.path.dirname(sound_name)
            if out_dir:
                if ensure_dir(out_dir):
                    verbose_print("    in working directory, "
                                  "created directory: " + out_dir)
        # Now we're going to spawn the stages. Need to do final token
        # substitution and then build a list of spawned processes.
        var_table = {'sound_name': sound_name, 'write_to': "%write_to%"}
        passthru_filename = None
        p_chain = []
        for stage in range(num_stages):
            stage_args = [settings.eval_finalize('converter', a, var_table)
                          for a in command_stages[stage]]
            # Use of the %write_to% command makes this the last stage, and
            # means that we won't handle it like other stages.
            if stage_args[0] == "%write_to%":
                passthru_filename = stage_args[1]
                break
            # For "normal" command stages we'll just spawn processes and hook
            # their pipes together. The first stage is special because its
            # stdin will receive the sound data from us, and the last stage
            # is special because no one cares about its stdout.
            stage_stdin = p_chain[-1].stdout if p_chain else subprocess.PIPE
            stage_stdout = subprocess.PIPE if (stage + 1 < num_stages) else None
            p = subprocess.Popen(stage_args, stdin=stage_stdin, stdout=stage_stdout)
            p_chain.append(p)
        # OK we built our chain of processes. Unless the very first stage
        # used "%write_to%", the process chain will have something in it.
        if p_chain:
            # Launch the thread to handle a final "%write_to%"" stage if there
            # is one.
            writer_thread = None
            if passthru_filename:
                writer_thread = threading.Thread(target=writer_func,
                                                 args=(p_chain[-1].stdout,
                                                       passthru_filename))
                writer_thread.start()
            # We don't need the file objects that were created to wrap the
            # stdout file descriptors of the non-terminal stages of the chain,
            # so go ahead and close them now. We don't close the last one
            # because it is either None, or used by the write-to thread.
            for p in p_chain[:-1]:
                p.stdout.close()
            # Pump the sound data into the first stage of the chain and flush.
            p_chain[0].stdin.write(orig_data)
            p_chain[0].stdin.close()
            # Wait for the last stage in the chain to finish before we leave
            # and garbage-collect objects.
            if writer_thread:
                writer_thread.join()
            else:
                p_chain[-1].wait()
        else:
            # As the code currently stands, an empty process chain means
            # that the one and only stage is "%write_to%". But just to be
            # robust against future weirdness, we'll check to make sure that
            # there indeed was a "%write_to%" command.
            if passthru_filename:
                # We can handle this in-thread without spawning anything.
                with open(passthru_filename, 'wb') as outstream:
                    outstream.write(orig_data)
        # This converter always returns True if it doesn't encounter an
        # exception.
        return True
    return converter

def go(settings, targets_table):
    """Process according to the given settings and sound selections.

    Get the pak file paths from the settings. Get and apply the working
    directory from the settings. Get the converter definition from the
    settings and define a converter function. Process each pak file using
    :func:`expak.process_resources`.

    :param settings:      settings
    :type settings:       :class:`config.Settings`
    :param targets_table: table mapping sound selections to output names
    :type targets_table:  dict(str,str)

    :returns: False if the converter definition is invalid, True otherwise
    :rtype:   bool

    :raises config.BadSetting: if a token name discovered setting evaluation
                               references an undefined setting

    :raises config.TooManySubstitutions: if token substitution goes on for
                                         too many iterations

    """
    # Get the paths of pak files to process.
    pak_paths_prep = settings.eval_prep('pak_paths').split(",")
    pak_paths = [settings.eval_finalize('pak_paths', p.strip())
                 for p in pak_paths_prep]
    if settings.is_defined('pak_home'):
        pak_home = os.path.abspath(settings.eval('pak_home'))
        abs_pak_paths = [os.path.join(pak_home, p) for p in pak_paths if p]
    else:
        abs_pak_paths = [os.path.abspath(p) for p in pak_paths if p]
    # Change to the defined working directory.
    set_working_dir(settings)
    # Make the converter function.
    converter = make_converter(settings)
    if not converter:
        return False
    # Process each pak file.
    for path in abs_pak_paths:
        verbose_print("")
        verbose_print("reading pak file %s..." % path)
        expak.process_resources(path, converter, targets_table)
    verbose_print("")
    return True

