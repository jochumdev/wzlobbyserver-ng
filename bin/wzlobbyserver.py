#!/usr/bin/twistd -y
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

# Get the right reactor (asuming that we have a 2.6 kernel on linux)
from platform import system as platformSystem
if platformSystem == 'Linux':
    from twisted.internet import epollreactor
    epollreactor.install()


from twisted.application import service

from wzlobby import server

server.main()

application = service.Application('wzlobbyserver')
server.makeService().setServiceParent(application)
