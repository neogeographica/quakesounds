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

"""Initialize, update, and evaluate settings values."""

import re

TOKEN_RE = re.compile("%([^%]+)%")
MAX_SUBSTITUTION_DEPTH = 16


def read_properties(prop_lines, prop_table, default_func):
    """Update a properties table from a list of property key:value lines.

    Skip any line that is blank or that has a "#" character as its first non-
    whitespace character. For other lines, split them into key and value at
    the first ":" character (dropping any whitespace around the split point).
    If value is empty, pass the key to default_func to get the default value.

    If the property value is not None, set it in the ``prop_table``. Otherwise
    remove that property from the ``prop_table`` if it is currently in there.

    :param prop_lines:   list of strings that are each either blank, comment,
                         or specifying a property key:value
    :type prop_lines:    iterable(str)
    :param prop_table:   property key/value table to update
    :type prop_table:    dict(str,str)
    :param default_func: function to produce a property value for a key, when
                         no value is specified
    :type default_func:  function(str)

    """
    for line in [l.strip() for l in prop_lines]:
        if not line or line[0] == "#":
            continue
        prop = line.partition(":")
        prop_key = prop[0].rstrip()
        if not prop_key:
            continue
        prop_value = prop[2].lstrip()
        if not prop_value:
            prop_value = default_func(prop_key)
        if prop_value is None:
            prop_table.pop(prop_key, None)
        else:
            prop_table[prop_key] = prop_value

def read_properties_file(file_path, prop_table, default_func):
    """Update a properties table from a file.

    If the file exists and is readable, open it and use its contents to
    invoke :func:`read_properties`. Otherwise leave the property table
    unmodified.

    :param file_path:    path to properties file to read
    :type file_path:     str
    :param prop_table:   property key/value table to update
    :type prop_table:    dict(str,str)
    :param default_func: function to produce a property value for a key, when
                         no value is specified
    :type default_func:  function(str)

    """
    try:
        with open(file_path, 'r') as prop_lines:
            read_properties(prop_lines, prop_table, default_func)
    except IOError:
        pass

def read_cfg(cfg_path, default_func=lambda x: None):
    """Initialize a properties table from a file.

    Just a convenience wrapper for :func:`read_properties_file` that
    creates and returns a new property table, and provides a default for
    the default_func.

    :param cfg_path:     path to properties file to read
    :type cfg_path:      str
    :param default_func: function to produce a property value for a key, when
                         no value is specified
    :type default_func:  function(str)

    :returns: property key/value table initialized from the file contents
    :rtype:   dict(str,str)

    """
    cfg_table = {}
    read_properties_file(cfg_path, cfg_table, default_func)
    return cfg_table

def update_cfg(args, cfg_table, default_func=lambda x: None):
    """Update a properties table from a list of property key:value lines.

    Just a wrapper for :func:`read_properties`; the only difference is a
    default for the default_func. And name consistency with read_cfg, I guess.
    Leaving it here for now in case "config" semantics on top of the
    "property table" semantics show up again in the future.

    :param args:         list of strings that are each either blank, comment,
                         or specifying a property key:value
    :type args:          iterable(str)
    :param cfg_table:    property key/value table to update
    :type cfg_table:     dict(str,str)
    :param default_func: function to produce a property value for a key, when
                         no value is specified
    :type default_func:  function(str)

    """
    read_properties(args, cfg_table, default_func)

class TooManySubstitutions(Exception):
    """Exception for signaling that value substitution is taking too long.

    This exception is raised when a value has been iteratively processed for
    token substitution more than some acceptable limit of times, with tokens
    still remaining in the value.

    """

    def __init__(self, context_key, value, max_depth):
        """Initializer.

        :param context_key: The key for the value that is being processed.
        :type context_key:  str
        :param value:       The value when the iteration limit was hit.
        :type value:        str
        :param max_depth:   The iteration limit that was hit.
        :type max_depth:    int

        """
        self.context_key = context_key
        self.value = value
        self.max_depth = max_depth

    def __str__(self):
        """String representation.

        :returns: exception description
        :rtype:   str

        """
        return ("evaluation of setting '{0}' "
                "has gone through {1} token substitution passes "
                "without completely resolving; current value: {2}".format(
            self.context_key, self.max_depth, self.value))

class BadSetting(Exception):
    """Exception for signaling that a key lookup has failed.

    """

    def __init__(self, key, context_key=None, context_value=None):
        """Initializer.

        :param key:           key for the failed lookup
        :type key:            str
        :param context_key:   key for the value that contained a token
                              reference to the failed key, or None if the
                              failed key was the initial lookup
        :type context_key:    str or None
        :param context_value: value that contained a token reference to the
                              failed key, or None if the failed key was the
                              initial lookup
        :type context_value:  str or None

        """
        self.key = key
        self.context_key = context_key
        self.context_value = context_value

    def __str__(self):
        """String representation.

        :returns: exception description
        :rtype:   str

        """
        if not self.context_key:
            return ("required setting '{0}' is undefined".format(self.key))
        else:
            return ("setting '{0}' is undefined or used in an illegal context "
                    "when evaluating content of setting '{1}': {2}".format(
                self.key, self.context_key, self.context_value))

class Settings:
    """Encapsulate config properties and methods for evaluating them.

    An instance of this class contains a table of user-defined properties that
    can have their values recursively evaluated for token substitution, and a
    table of system-defined properties. The methods fetch property values with
    the appropriate substitutions handled.

    The user-defined and system-defined properties defined at initialization
    time will be properties that have constant values for the life of this
    object. The value-fetching methods do provide some support for specifying
    additional system-defined properties that may have values that change over
    time.

    """

    def __init__(self, cfg_table, finalize_table):
        """Initializer.

        Save copies of the given tables of user-defined properties and
        system properties. In the copy of system properties, instantiate
        additional properties representing the special characters. In the copy
        of user properties, instantiate properties representing tokens for all
        of the system properties, so that system-property tokens won't be
        disturbed during the passes that handle user-property substitution.

        :param cfg_table:      user-defined properties
        :type cfg_table:       dict(str,str)
        :param finalize_table: system-defined properties
        :type finalize_table:  dict(str,str)

        """
        self.cfg_table = cfg_table.copy()
        self.finalize_table = {'percent': "%", 'comma': ",",
                               'space': " ", 'empty': ""}
        self.finalize_table.update(finalize_table)
        for token_name in self.finalize_table:
            self.cfg_table[token_name] = "%" + token_name + "%"

    def raw_cfg(self, key):
        """Fetch a user-defined property value without doing substitutions.

        :param key: property key
        :type key:  str

        :returns: key's value direct from the user-defined property table
        :rtype:   str

        :raises BadSetting: if the key is not in the table

        """
        try:
            value = self.cfg_table[key]
        except KeyError as badkey:
            raise BadSetting(badkey.message)
        return value

    @staticmethod
    def sub_table_tokens(context_key, table, value, skip_names):
        """Internal method to do one pass of token substitution on a value.

        Use the token regular expression to do a left-to-right substitution
        pass. Tokens are ignored if their names are in ``skip_names``;
        otherwise they will be replaced by the value from looking up the
        token name in ``table``.

        :param context_key: key for which this value processing is being done
                            (used in error messages)
        :type context_key:  str
        :param table:       table to look up values for token names
        :type table:        dict(str,str)
        :param value:       value to process
        :type value:        str
        :param skip_names:  token names to ignore
        :type skip_names:   container(str) or None

        :returns: modified value after one pass of token substitution
        :rtype:   str

        :raises BadSetting: if a discovered token's name is in neither
                            ``skip_names`` nor ``table``

        """
        def token_lookup(match):
            """Process token matches.

            Get the token name from the match object. If the token name is in
            ``skip_names``, return the entire token unchanged. Otherwise
            return the value from looking up the token name in ``table``.

            :param match: match object for discovered token
            :type match:  :class:`SRE_Match`

            :returns: string to substitute for token
            :rtype:   str

            :raises BadSetting: if the token name is in neither ``skip_names``
                                nor ``table``

            """
            token_name = match.group(1)
            if skip_names and token_name in skip_names:
                return "%" + token_name + "%"
            if token_name in table:
                return table[token_name]
            raise BadSetting(token_name, context_key, value)
        return TOKEN_RE.sub(token_lookup, value)

    def sub_cfg_tokens(self, context_key, value, skip_names, iter=0):
        """Internal method to iteratively do token substitution on a value.

        Using tail recursion, repeatedly invoke :func:`sub_table_tokens` on
        the given value, using the properties of the user-defined config. If
        the value reaches a stable form, return that. If on the other hand the
        process goes through :const:`MAX_SUBSTITUTION_DEPTH` iterations and
        the value is still changing, raise an exception.

        :param context_key: key for which this value processing is being done
                            (used in error messages)
        :type context_key:  str
        :param value:       value to process
        :type value:        str
        :param skip_names:  token names to ignore
        :type skip_names:   container(str) or None
        :param iter:        current iteration number
        :type iter:         int

        :returns: modified value after token substitution
        :rtype:   str

        :raises BadSetting: if a discovered token's name is in neither
                            ``skip_names`` nor ``table``

        :raises TooManySubstitutions: if ``iter`` is greater than or equal to
                                      :const:`MAX_SUBSTITUTION_DEPTH` after
                                      a substitution that changes ``value``

        """
        new_value = self.sub_table_tokens(context_key, self.cfg_table, value,
                                          skip_names)
        if new_value == value:
            return new_value
        if iter >= MAX_SUBSTITUTION_DEPTH:
            raise TooManySubstitutions(context_key, value,
                                       MAX_SUBSTITUTION_DEPTH)
        return self.sub_cfg_tokens(context_key, new_value, skip_names,
                                   iter + 1)

    def eval_prep(self, key, skip_names=None):
        """Get a key's value with token substitution handled for user config.

        Get the initial value for the key, then use :func:`sub_cfg_tokens` to
        do token substitution on that value. Return the final value.

        :param key:        key of the user-defined property value to process
        :type key:         str
        :param skip_names: token names to ignore during substitution
        :type skip_names:  container(str) or None

        :returns: value after token substitution using the user config
        :rtype:   str

        :raises BadSetting: if a necessary token lookup fails

        :raises TooManySubstitutions: if token substitution goes on for too
                                      too many iterations

        """
        return self.sub_cfg_tokens(key, self.raw_cfg(key), skip_names)

    def eval_finalize(self, context_key, value, var_table=None):
        """Apply token substitution to a value with system-defined properties.

        Use :func:`sub_table_tokens` to do a single pass of token
        substitution. The properties table for that substitution will be the
        ``finalize_table`` provided in the initializer, augmented with any
        properties defined in ``var_table``.

        :param context_key: key for which this value processing is being done
                            (used in error messages)
        :type context_key:  str
        :param value:       value to process
        :type value:        str
        :param var_table:   additional properties to reference
        :type var_table:    dict(str,str) or None

        :returns: modified value after one pass of token substitution
        :rtype:   str

        :raises BadSetting: if a discovered token's name is not found in the
                            table constructed for the substitution

        """
        if var_table:
            total_table = self.finalize_table.copy()
            total_table.update(var_table)
        else:
            total_table = self.finalize_table
        return self.sub_table_tokens(context_key, total_table, value, None)

    def eval(self, key, var_table=None):
        """Look up a key's value and apply all token substitutions.

        Convenience wrapper for :func:`eval_prep` and :func:`eval_finalize`.

        :param key:       key of the user-defined property value to process
        :type key:        str
        :param var_table: additional properties to reference
        :type var_table:  dict(str,str) or None

        :returns: value after token substitution is handled
        :rtype:   str

        :raises BadSetting: if a discovered token's name is not found in the
                            appropriate table

        :raises TooManySubstitutions: if the setting-evaluation loop goes on
                                      for too many iterations

        """
        prep_value = self.eval_prep(key, var_table)
        return self.eval_finalize(key, prep_value, var_table)

    def is_defined(self, key):
        """Check to see if a key is present in the user-defined config.

        :param key: key of the user-defined property to check
        :type key:  str

        :returns: whether the key is in the user-defined config
        :rtype:   bool

        """
        return key in self.cfg_table

    def optional_bool(self, key):
        """Evaluate a property as an optional boolean value.

        Return True if the property is defined with a value that evaluates to
        "True" (case-insensitive). Return False otherwise.

        :param key: key of the property to evaluate
        :type key:  str

        :returns: whether the key's value evaluates to "True" (case-insensitive)
        :rtype:   bool

        """
        if not self.is_defined(key):
            return False
        value = self.eval(key)
        return value.lower() == "true"
