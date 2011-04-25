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

from twisted.internet import protocol, reactor
from twisted.application import service, internet
from twisted.python import log

from wzlobby.protocol import ProtocolSwitcher
from wzlobby.gamedb import GameDB
from wzlobby.database import Database
from wzlobby import settings

import signal

def _handleSIGHUP(*args):
    log.msg('Reloading the config')
    reactor.callLater(0, reload, settings)

def main():
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _handleSIGHUP)

def makeService():
    s = service.MultiService()
    f = protocol.ServerFactory()
    f.protocol = ProtocolSwitcher
    f.clients = []
    f.gameDB = GameDB()
    f.db = Database()
    h = internet.TCPServer(9990, f).setServiceParent(s)

    return s
