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
from twisted.application import service

from wzlobby.game import Game
from wzlobby.tools import testConnect

class GameDB(service.Service):
    
    def __init__(self):
        self.gidIndex = {}
        
        self.numgen = iterCount(1)

    
    def createGame(self, lobbyVer):
        gameId = self.numgen.next()
        
        game = Game(lobbyVer, gameId)
        self.gidIndex[gameId] = game
        
        return game
    
    
    def getGaidGame(self, gameId):
        return self.gidIndex.get(gameId, None)

    
    def getGames(self):
        return self.gidIndex
    
    
    def updateGame(self, gameId, data):
        if not gameId in self.gidIndex:
            return False
        
        self.gidIndex[gameId].update(data)
        
        return True
    
    
    def removeGame(self, game):
        gameId = game['gameId']
        
        try:
            game = self.gidIndex[gameId]
            if game.lCall and game.lCall.running:
                game.lCall.stop()
            
            del(game, self.gidIndex[gameId])
            
        except KeyError:
            return False
                
        return True
    
    
    def checkGame(self, game):
        """ Check the game for its connectivity and removes it on failures.
        
        returns a C{twisted.internet.defer.Deferred} 
        """
        if not game or not game['gameHost']:
            return defer.succeed('NO GAME or hostip')
        
        d = testConnect(game['gameHost'], game['gamePort'])            
        d.addErrback(lambda x: self.removeGame(game))
        
        return d
    
    
    def loopCheck(self, game):
        """ Starts a loop which checks the given game every 10 seconds
            FIXME: make that interval configurable!
        """
        
        gameId = game['gameId']
        
        if gameId in self.gidIndex:            
            if game.lCall and game.lCall.running:
                log.msg('Stopping old loopingcall for %s:%d' % (game['gameHost'], game['gamePort']))
                game.lCall.stop()
                
            game.lCall = LoopingCall(self.checkGame, game)
            game.lCall.start(10, now=False)


    def __remove(self, g):
        # ignore keyerrors, this never removes indexes
        try:
            self.list.gidIndex(g)
        except KeyError:
            pass