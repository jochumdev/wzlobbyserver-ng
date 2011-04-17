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

__all__ = ['Protocol4']

from twisted.internet import defer
from twisted.python import log
from socketrpc.twisted_srpc import SocketRPCProtocol, set_serializer, Fault

from wzlobby import settings

set_serializer('bson')

NO_GAME = -402
NOT_ACCEPTABLE = -403
WRONG_LOGIN = -404

class Protocol4(SocketRPCProtocol):
    game = None

    lobbyVersion = 4

    def connectionMade(self):
        SocketRPCProtocol.connectionMade(self)

        self.debug = settings.debug
        self.gameDB = self.factory.gameDB


    def docall_addGame(self, *args, **kwargs):
        def checkFailed(reason):
            return defer.fail(
                    Fault(
                          NOT_ACCEPTABLE,
                          reason.getErrorMessage()
                   )
            )


        def checkDone(result):
            self.gameDB.register(game)

            log.msg('new game %d: "%s" from "%s".' % (game['gameId'],
                                                      game['description'].encode('utf8'),
                                                      game['hostplayer'].encode('utf8')))

            return [game['gameId'], result]


        game = self.gameDB.create(self.lobbyVersion)

        # Update the game with the received data        
        for k, v in kwargs.iteritems():
            try:
                game[k] = v
            except KeyError:
                pass

        # Add hosts ip
        game['host'] = self.transport.getPeer().host

        d = self.gameDB.check(game)
        d.addCallback(checkDone)
        d.addErrback(checkFailed)

        return d


    def docall_delGame(self, gameId):
        game = self.gameDB.get(gameId, False)
        if not game:
            return defer.fail(
                    Fault(NO_GAME, 'Game %d does not exists' % gameId)
            )

        self.gameDB.remove(game)

        return defer.succeed('')


    def docall_addPlayer(self, gameId, slot, name, ipaddress):
        game = self.gameDB.get(gameId, False)
        if not game:
            return defer.fail(
                    Fault(NO_GAME, 'Game %d does not exists' % gameId)
            )

        game['currentPlayers'] += 1
        return defer.succeed('')


    def docall_delPlayer(self, gameId, slot):
        game = self.gameDB.get(gameId, False)
        if not game:
            return defer.fail(
                    Fault(NO_GAME, 'Game %d does not exists' % gameId)
            )

        game['currentPlayers'] -= 1
        return defer.succeed('')


    def docall_updatePlayer(self, gameId, slot, name):
        return defer.succeed('')


    def docall_list(self, maxgames=9999):
        maxgames = int(maxgames);

        games = []
        for game in self.gameDB.itervalues():
            games.append({
                "host"           : game["host"],
                "port"           : game["port"],
                "description"    : game["description"],
                "currentPlayers" : game["currentPlayers"],
                "maxPlayers"     : game["maxPlayers"],
                "multiVer"       : game["multiVer"],
                "wzVerMajor"     : game["wzVerMajor"],
                "wzVerMinor"     : game["wzVerMinor"],
                "isPrivate"      : game["isPrivate"],
                "modlist"        : game["modlist"],
                "mapname"        : game["mapname"],
                "hostplayer"     : game["hostplayer"],
            })

            maxgames -= 1
            if maxgames == 0:
                break;

        return defer.succeed(games)
