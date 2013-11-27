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
