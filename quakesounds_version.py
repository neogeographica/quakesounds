#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import re

path = os.path.join("quakesounds_src", "__main__.py")
with open(path, 'r') as instream:
    content = instream.read()

version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                          content, re.M)
print(version_match.group(1), end='')
