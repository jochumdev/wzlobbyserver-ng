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

from twisted.internet import protocol, reactor, ssl
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

def makeService():
    s = service.MultiService()
    f = protocol.ServerFactory()
    f.protocol = ProtocolSwitcher
    f.clients = []
    f.gameDB = GameDB()
    f.db = Database()
    h = internet.TCPServer(settings.port, f).setServiceParent(s)
    h = internet.SSLServer(
       settings.ssl_port,
       f,
       ssl.DefaultOpenSSLContextFactory(
                settings.ssl_key,
                settings.ssl_cert)
    ).setServiceParent(s)

    # Debug add some games
#    for i in xrange(30):
#        game = f.gameDB.create(4, True)
#        f.gameDB.updateGame(game['gameId'], {
#            "host"           : "localhost",
#            "port"           : 2100,
#            "description"    : "Test %d" % i,
#            "currentPlayers" : 1,
#            "maxPlayers"     : 3,
#            "multiVer"       : "None existend test",
#            "wzVerMajor"     : 4,
#            "wzVerMinor"     : 11012,
#            "isPrivate"      : True,
#            "modlist"        : "",
#            "mapname"        : "Sk-Rush-T1",
#            "hostplayer"     : "Test %d" % i,
#        })

    return s

if hasattr(signal, "SIGHUP"):
    signal.signal(signal.SIGHUP, _handleSIGHUP)

application = service.Application('wzlobbyserver')
makeService().setServiceParent(application)
