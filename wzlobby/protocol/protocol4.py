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

from wzlobby import bsonlib

NO_GAME = -402
NOT_ACCEPTABLE = -403
GAME_IS_FULL = -404

class Protocol4(bsonlib.Server):

    game = None

    lobbyVersion = 4

    def connectionMade(self):
        self.gameDB = self.factory.gameDB
        self.settings = self.factory.settings


    def connectionLost(self, reason):
        """ This will be called when the client
        closed its connection.
        """
        if self.game:
            self.gameDB.removeGame(self.game)


    def do_addGame(self, args):
        def checkFailed(reason):
            return defer.fail(
                    bsonlib.Fault(
                            NOT_ACCEPTABLE,
                            reason.getErrorMessage()
                   )
            )


        def checkDone(result):
            self.gameDB.registerGame(game)
            self.game = game

            return {'gameId': self.game['gameId'],
                    'motd': result,
                   }


        game = self.gameDB.createGame(self.lobbyVersion)

        # Update the game with the received data        
        for k, v in args.iteritems():
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


    def do_addPlayer(self, args):
        if not self.game:
            return defer.fail(
                    bsonlib.Fault(NO_GAME, 'Create a game first!')
            )

        if self.game['currentPlayers'] == self.game['maxPlayers']:
            return defer.fail(
                    bsonlib.Fault(GAME_IS_FULL, 'Game is Full.')
            )
        else:
            self.game['currentPlayers'] += 1
            return defer.succeed('Player added.')


    def do_removePlayer(self, args):
        if not self.game:
            return defer.fail(
                    bsonlib.Fault(NO_GAME, 'Create a game first!')
            )

        self.game['currentPlayers'] -= 1
        return defer.succeed('Player removed.')


    def do_removeGame(self, args=None):
        if not self.game:
            return defer.fail(
                    bsonlib.Fault(NO_GAME, 'Create a game first!')
            )

        self.gameDB.removeGame(self.game)
        self.game = None

        return defer.succeed('Game removed')


    def do_list(self, args):
        result = {'count': len(self.gameDB), 'list': []}

        for game in self.gameDB.itervalues():
            result['list'].append(dict(game))

        return defer.succeed(result)
