#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et sts=4 sw=4 encoding=utf-8:
#
# This file is part of Warzone 2100.
# Copyright (C) 2011  Warzone 2100 Project
#
# Warzone 2100 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Warzone 2100 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Warzone 2100; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
###############################################################################
from __future__ import division

### START Library location
# Set import Library to ../wzlobbyserver if exists (not installed)
import sys
import os.path

if os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), os.pardir, 'wzlobby')):
    sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), os.pardir))
### END library location

if __name__ == '__main__':
    from twisted.scripts.twistd import run
    import pkgutil
    package = pkgutil.get_loader('wzlobby.scripts.wzlobbyserver')

    argv = sys.argv[1:]
    sys.argv = [__file__, '-y', package.filename]
    sys.argv.extend(argv)
    run()
