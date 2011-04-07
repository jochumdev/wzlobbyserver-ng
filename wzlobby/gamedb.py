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

from UserDict import IterableUserDict

from wzlobby.game import Game
from wzlobby.tools import testConnect
from wzlobby import settings

class GameDB(IterableUserDict):

    def __init__(self):
        self.data = {}
        self.numgen = iterCount(1)


    def create(self, lobby_ver, register=False):
        game_id = self.numgen.next()

        game = Game(lobby_ver, game_id)
        if settings.debug:
            log.msg('Created game: %d' % game_id)

        if register:
            self.register(game)

        return game


    def register(self, game):
        self.data[game['gameId']] = game


    def updateGame(self, game_id, infos):
        if not game_id in self.data:
            log.err('Unknown game %s' % game_id)
            return False

        self.data[game_id].update(infos)

        return True


    def remove(self, game):
        try:
            del(self.data[game['gameId']])
            log.msg('Removed game: %d' % game['gameId'])
        except KeyError:
            return False

        return True


    def check(self, game):
        """ Starts a loop which checks the given game every settings.check_interval seconds
        """
        if not game['host']:
            return defer.fail(Exception('Ignoring empty games.'))

        hostname = game['description'].lower().split(' ')
        if not settings.badwords.isdisjoint(hostname):
            log.msg('Game name not acceptable.')
            return defer.fail(Exception('Game name not acceptable. The game is NOT hosted, change the name of your game.'))

        if game.lCall and game.lCall.running:
            game.lCall.stop()

        d = self._check(game)
        d.addCallback(lambda x: settings.getMotd(game['multiVer']))

        # Start the loopingcall
        if not game.lCall:
            game.lCall = LoopingCall(self._check, game)
            d2 = game.lCall.start(settings.check_interval, now=False)
            # Ignore future errors on the LoopingCall
            d2.addErrback(lambda x: '')

        return d


    def _check(self, game):
        """ Check the game for its connectivity and removes it on failures.
        
        returns a C{twisted.internet.defer.Deferred} 
        """
        def remove(failure):
            self.remove(game)
            return defer.fail(Exception('Game unreachable, failed to open a connection to port %d.' % game['port']))

        d = testConnect(game['host'], game['port'])
        d.addErrback(remove)

        return d
