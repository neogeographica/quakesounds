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

import expak
import subprocess
import sys
import os
import errno

verbose = False


def verbose_print(format_str, args=None):
    if verbose:
        if args:
            print(format_str % args)
        else:
            print(format_str)

def set_verbosity(settings):
    global verbose
    if settings.is_defined('verbose'):
        verbose_value = settings.eval('verbose')
        if verbose_value.lower() == "true":
            verbose = True
        else:
            verbose = False

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

def printable_command_stage(command_stage):
    return " ".join([a.strip() for a in command_stage.split(",")])

def make_converter(settings):
    command = settings.eval_prep_cfg('converter', ['base_name'])
    command_stages = [s.strip() for s in command.split("|")]
    num_stages = len(command_stages)
    for stage in range(num_stages):
        verbose_print("converter stage %d of %d:" % (stage + 1, num_stages))
        verbose_print("    %s" % printable_command_stage(command_stages[stage]))
    def converter(orig_data, base_name):
        verbose_print("   creating %s", base_name)
        out_dir = os.path.dirname(base_name)
        if out_dir:
            ensure_dir(out_dir)
        p_chain = []
        for stage in range(num_stages):
            stage_args = settings.eval_list_finalize(command_stages[stage],
                                                     {'base_name': base_name})
            stage_stdin = p_chain[-1].stdout if p_chain else subprocess.PIPE
            stage_stdout = subprocess.PIPE if (stage + 1 < num_stages) else None
            p = subprocess.Popen(stage_args, stdin=stage_stdin, stdout=stage_stdout)
            p_chain.append(p)
        # We don't need the file objects that were created to wrap the stdout
        # file descriptors of the non-terminal stages of the chain, so go ahead
        # and close them now.
        for p in p_chain[:-1]:
            p.stdout.close()
        # Pump the sound data into the first stage of the chain and flush it.
        p_chain[0].stdin.write(orig_data)
        p_chain[0].stdin.close()
        # Wait for the last stage in the chain to finish before we leave and
        # garbage-collect objects.
        p_chain[-1].wait()
        return True
    return converter

def go(settings, file_table):
    set_verbosity(settings)
    verbose_print("")
    pak_paths = settings.eval_list('pak_paths')
    abs_pak_paths = [os.path.abspath(p) for p in pak_paths]
    set_working_dir(settings)
    converter = make_converter(settings)
    for path in abs_pak_paths:
        verbose_print("")
        verbose_print("processing pak file %s...", path)
        expak.process_resources(path, converter, file_table)
    verbose_print("")
    return True

