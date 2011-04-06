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

__all__ = ['GameDB']

from itertools import count as iterCount

from twisted.internet import defer
from twisted.python import log
from twisted.internet.task import LoopingCall

import UserDict

from wzlobby.game import Game
from wzlobby.tools import testConnect

class GameDB(UserDict.IterableUserDict):

    def __init__(self, settings):
        self.settings = settings
        self.data = {}

        self.numgen = iterCount(1)


    def createGame(self, lobbyVer):
        gameId = self.numgen.next()

        game = Game(lobbyVer, gameId)
        log.msg('Created game: %d' % gameId)

        return game


    def registerGame(self, game):
        self.data[game['gameId']] = game


    def updateGame(self, gameId, data):
        if not gameId in self.data:
            return False

        self.data[gameId].update(data)

        return True


    def removeGame(self, game):
        log.msg('Removing game: %d' % game['gameId'])
        try:
            del(self.data[game['gameId']])
        except KeyError:
            return False

        return True


    def check(self, game):
        """ Starts a loop which checks the given game every 10 seconds
            FIXME: make that interval configurable!
        """
        if not game['host']:
            return defer.succeed('Ignoring empty games in case of the 2.3 multiconnect bug.')

        hostname = game['description'].lower().split(' ')
        if not self.settings.badwords.isdisjoint(hostname):
            log.msg('Game name not acceptable.')
            return defer.fail(Exception('Game name not acceptable. The game is NOT hosted, change the name of your game.'))

        if game.lCall and game.lCall.running:
            game.lCall.stop()

        d = self._check(game)
        d.addCallback(lambda x: self.settings.getMotd(game['multiVer']))

        # Start the loopingcall
        game.lCall = LoopingCall(self._check, game)
        d2 = game.lCall.start(10, now=False)
        # Ignore future errors on the LoopingCall
        d2.addErrback(lambda x: '')

        return d


    def _check(self, game):
        """ Check the game for its connectivity and removes it on failures.
        
        returns a C{twisted.internet.defer.Deferred} 
        """
        def removeGame(failure):
            self.removeGame(game)

            return defer.fail(Exception('Game unreachable, failed to open a connection to port %d.' % game['port']))

        d = testConnect(game['host'], game['port'])
        d.addErrback(removeGame)

        return d
