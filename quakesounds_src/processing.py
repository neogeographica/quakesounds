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

import subprocess
import sys
import os
import errno
import threading
from util import verbose_print

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
    try:
        os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def set_working_dir(settings):
    if settings.is_defined('out_working_dir'):
        out_working_dir = settings.eval('out_working_dir')
        if out_working_dir:
            ensure_dir(out_working_dir)
            os.chdir(out_working_dir)
            verbose_print("converter working dir is %s", out_working_dir)

def valid_command_stage(stage_args, is_last_stage):
    if not stage_args:
        sys.stderr.write("    Error: converter command stage is empty\n")
        return False
    if not stage_args[0]:
        sys.stderr.write("    Error: first element of converter command stage is empty\n")
        return False
    if stage_args[0] == "%write_to%":
        if len(stage_args) != 2:
            sys.stderr.write("    Error: %write_to% command takes one argument\n")
            return False
        if not is_last_stage:
            sys.stderr.write("    Warning: the rest of this stage after the %write_to% command will be ignored\n")
    return True

def writer_func(instream, outpath):
    with open(outpath, 'wb') as outstream:
        outstream.write(instream.read())

def make_converter(settings):
    command = settings.eval_prep('converter', ['sound_name', 'write_to'])
    command_stages = [[a.strip() for a in s.split(",")]
                      for s in command.split("|")]
    num_stages = len(command_stages)
    for stage in range(num_stages):
        verbose_print("converter stage %d of %d:" % (stage + 1, num_stages))
        stage_args = command_stages[stage]
        verbose_print("    %s" % " ".join(stage_args))
        if not valid_command_stage(stage_args, stage == num_stages - 1):
            sys.exit(1)
    def converter(orig_data, sound_name):
        verbose_print("   creating %s", sound_name)
        out_dir = os.path.dirname(sound_name)
        if out_dir:
            ensure_dir(out_dir)
        var_table = {'sound_name': sound_name, 'write_to': "%write_to%"}
        passthru_filename = None
        p_chain = []
        for stage in range(num_stages):
            stage_args = [settings.eval_finalize(a, var_table)
                          for a in command_stages[stage]]
            if stage_args[0] == "%write_to%":
                passthru_filename = stage_args[1]
                break
            stage_stdin = p_chain[-1].stdout if p_chain else subprocess.PIPE
            stage_stdout = subprocess.PIPE if (stage + 1 < num_stages) else None
            p = subprocess.Popen(stage_args, stdin=stage_stdin, stdout=stage_stdout)
            p_chain.append(p)
        if p_chain:
            # Launch the writer thread if needed.
            writer_thread = None
            if passthru_filename:
                writer_thread = threading.Thread(target=writer_func,
                                                 args=(p_chain[-1].stdout,
                                                       passthru_filename))
                writer_thread.start()
            # We don't need the file objects that were created to wrap the
            # stdout file descriptors of the non-terminal stages of the chain,
            # so go ahead and close them now. We don't close the last one
            # because it is either None, or used by the writer thread.
            for p in p_chain[:-1]:
                p.stdout.close()
            # Pump the sound data into the first stage of the chain and flush.
            p_chain[0].stdin.write(orig_data)
            p_chain[0].stdin.close()
            # Wait for the last stage in the chain to finish before we leave and
            # garbage-collect objects.
            if writer_thread:
                writer_thread.join()
            else:
                p_chain[-1].wait()
        else:
            # As things stand passthru_filename should always be set here, but
            # we might as well be robust against future weirdness.
            if passthru_filename:
                with open(passthru_filename, 'wb') as outstream:
                    outstream.write(orig_data)
        return True
    return converter

def go(settings, file_table):
    pak_paths_prep = settings.eval_prep('pak_paths').split(",")
    pak_paths = [settings.eval_finalize(p.strip()) for p in pak_paths_prep]
    abs_pak_paths = [os.path.abspath(p) for p in pak_paths if p]
    set_working_dir(settings)
    converter = make_converter(settings)
    for path in abs_pak_paths:
        verbose_print("")
        verbose_print("processing pak file %s...", path)
        expak.process_resources(path, converter, file_table)
    verbose_print("")
    return True

