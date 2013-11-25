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

from contextlib import contextmanager
from contextlib import closing
import os
import shutil
from pkg_resources import resource_listdir
from pkg_resources import resource_isdir
from pkg_resources import resource_stream
import tempfile
import sys
import stat


# Instead of treating zipped and unzipped application formats differently,
# let's always make a temp dir and copy the resources. This means that the
# qs_internal directory will always behave like a space that gets deleted after
# the run, which is a nice consistency. Also in practice of course we should
# almost always be running in the zipped state.

# pkg_resources.resource_filename doesn't work for zipped apps that are not
# named *.egg. Rather than try to circumvent that -- probably there's a good
# reason -- I'll roll my own temp resource file staging.

@contextmanager
def temp_copies(res_path, temp_dir=None):
    temp_dir = tempfile.mkdtemp(dir=temp_dir)
    try:
        for resource in resource_listdir(__name__, res_path):
            if not resource:
                continue
            resource_path = "/".join([res_path, resource])
            if resource_isdir(__name__, resource_path):
                sys.stderr.write("skipping internal resource %s "
                                 "(resource subdirectories not supported)\n" %
                                 resource_path)
                continue
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

