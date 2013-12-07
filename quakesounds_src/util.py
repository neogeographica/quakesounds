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

"""Utility functions used by multiple modules. Not much here now!"""

verbose = False


def set_verbosity(settings):
    """Enable/disable verbose printing according to config settings.

    Set verbose=True if the verbose setting is set True (case-insensitive);
    verbose=False if the setting is unset or some other value.

    :param settings: config settings
    :type settings:  :class:`config.Settings`

    """
    global verbose
    verbose = settings.optional_bool('verbose')

def verbose_print(message):
    """Print the message string if verbose is currently True.

    :param message: message string, ready-to-print
    :type message:  str

    """
    if verbose:
        print(message)
