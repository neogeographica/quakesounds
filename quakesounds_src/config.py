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

MAX_SUBSTITUTION_DEPTH = 16


def read_properties(prop_lines, prop_table, default_func):
    for line in [l.strip() for l in prop_lines]:
        if not line or line[0] == "#":
            continue
        property = line.partition(":")
        property_key = property[0].rstrip()
        if not property_key:
            continue
        property_value = property[2].lstrip()
        if not property_value:
            property_value = default_func(property_key)
        if property_value is None:
            continue
        prop_table[property_key] = property_value

def read_properties_file(file_path, prop_table, default_func):
    try:
        with open(file_path, 'r') as prop_lines:
            read_properties(prop_lines, prop_table, default_func)
    except IOError:
        pass

def read_cfg(cfg_path, default_func=lambda x: None):
    cfg_table = {}
    read_properties_file(cfg_path, cfg_table, default_func)
    return cfg_table

def update_cfg(args, cfg_table, default_func=lambda x: None):
    read_properties(args, cfg_table, default_func)

class TooManySubstitutions(Exception):
    def __init__(self, key):
        self.key = key
    def __str__(self):
        return ("evaluation of setting %s "
                "has gone through %d token substitution passes "
                "without completely resolving" %
                (self.key, MAX_SUBSTITUTION_DEPTH))

class BadSetting(Exception):
    def __init__(self, key):
        self.key = key
    def __str__(self):
        return ("setting %s is undefined or used in an illegal context" %
                self.key)

class Settings:
    def __init__(self, cfg_table, path_table):
        self.special_table = {'base_name': None, 'percent': "%", 'comma': ","}
        self.path_table = path_table.copy()
        self.protect_tokens(self.path_table, self.special_table)
        self.cfg_table = cfg_table.copy()
        self.protect_tokens(self.cfg_table, self.path_table)
        self.token_re = re.compile("%([^%]+)%")
        special_token_name = "|".join(t for t in self.special_table)
        self.special_token_re = re.compile("%(" + special_token_name + ")%")
    @staticmethod
    def protect_tokens(table, token_names):
        for name in token_names:
            table[name] = "%" + name + "%"
    @staticmethod
    def sub_table_tokens(table, token_re, value):
        try:
            new_value = token_re.sub(lambda m: table[m.group(1)], value)
        except KeyError as badkey:
            raise BadSetting(badkey)
        return new_value
    def sub_cfg_tokens(self, key, value, iter=0):
        new_value = self.sub_table_tokens(self.cfg_table, self.token_re, value)
        if new_value == value:
            return new_value
        if iter >= MAX_SUBSTITUTION_DEPTH:
            raise TooManySubstitutions(key)
        return self.sub_cfg_tokens(key, new_value, iter + 1)
    def eval_prep_cfg(self, key):
        try:
            value = self.cfg_table[key]
        except KeyError as badkey:
            raise BadSetting(badkey)
        return self.sub_cfg_tokens(key, value)
    def eval_prep_paths(self, value):
        return self.sub_table_tokens(self.path_table, self.token_re, value)
    def eval_finalize(self, value, base_name=None):
        if base_name is None:
            self.special_table.pop('base_name', None)
        else:
            self.special_table['base_name'] = base_name
        return self.sub_table_tokens(self.special_table, self.special_token_re,
                                     value)
    def eval_list_finalize(self, value, base_name=None):
        new_value = value.split(",")
        return [self.eval_finalize(e, base_name).strip() for e in new_value]
    def eval(self, key, base_name=None):
        value = self.eval_prep_paths(self.eval_prep_cfg(key))
        return self.eval_finalize(value, base_name)
    def eval_list(self, key, base_name=None):
        value = self.eval_prep_paths(self.eval_prep_cfg(key))
        return self.eval_list_finalize(value, base_name)
    def is_defined(self, key):
        return key in self.cfg_table

