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

"""Manage internal resources bundled with the application.

Instead of treating zipped and unzipped application formats differently,
always make a temp dir and copy the resources there. This means that the
qs_internal directory will always behave like a space that gets deleted after
the run, which is a nice consistency. Also in practice of course we should
almost always be running in the zipped state.

That's one reason to not just use :func:`pkg_resources.resource_filename`, but
another reason is that resource_filename doesn't work for zipped archives that
are not named *.egg. Rather than try to circumvent that -- probably there's a
good reason -- I'll roll my own temp resource file staging.

"""

import os
import shutil
import tempfile
import sys
import stat
from contextlib import contextmanager, closing

# Use the system-installed :mod:`pkg_resources` module if it is available. If
# not, try to load a bundled-in copy from this application package. Save an
# indicator of which pkg_resources was used.
saved_sys_path = sys.path
sys.path = sys.path[1:]
try:
    from pkg_resources import resource_listdir, resource_isdir, resource_stream
    sys.path = saved_sys_path
    pkg_resources_source = "system"
except ImportError:
    sys.path = saved_sys_path
    from pkg_resources import resource_listdir, resource_isdir, resource_stream
    pkg_resources_source = "bundled"


@contextmanager
def temp_copies(res_path, temp_dir=None):
    """Context manager to extract and clean up internally bundled resources.

    Make a temporary directory to hold the resources. Extract them there and
    set each resource file's mode to be readable, writable, & executable. On
    scope exit delete that temp directory and all its contents.

    :param res_path: resource path within this application bundle
    :type res_path:  str
    :param temp_dir: directory where the new temporary directory should be
                     created, or None to use some system-standard location
    :type temp_dir:  str or None

    :returns: path to the created temporary directory
    :rtype:   str

    """
    temp_dir = tempfile.mkdtemp(dir=temp_dir)
    try:
        for resource in resource_listdir(__name__, res_path):
            if not resource: # sometimes can have emptystring in this list?
                continue
            resource_path = "/".join([res_path, resource])
            # Easier to just deal with a flat file layout, no further subdirs.
            if resource_isdir(__name__, resource_path):
                sys.stderr.write("skipping internal resource %s "
                                 "(resource subdirectories not supported)\n" %
                                 resource_path)
                continue
            # The resource stream won't be a file object (in zipped app case),
            # so we have to wrap it in the "closing" context mgr to close it
            # on scope exit.
            with closing(resource_stream(__name__, resource_path)) as instream:
                # Assuming this is small enough (megabytes, not GB) that we
                # don't need to bother chunking it.
                content = instream.read()
            outname = os.path.join(temp_dir, resource)
            with open(outname, 'wb') as outstream:
                outstream.write(content)
                # Make sure the file is readable/writable. Also mark
                # executable; helps some resources, doesn't hurt others.
                owner_perms = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                st = os.stat(outname)
                os.chmod(outname, st.st_mode | owner_perms)
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)
