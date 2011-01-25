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

__all__ = ['ProtocolSwitcher']

from twisted.python import log
from twisted.internet import defer, protocol

import struct
from itertools import izip

def encodeCString(string, buf_len):
    # If we haven't got a string return an empty one
    if not string:
        return str('\0' * buf_len)
    
    return str(string[:buf_len - 1].ljust(buf_len, "\0"))


class ProtocolSwitcher(protocol.Protocol):
    """ I try to detect a version command and switch
    the protocol.
    TODO: i'm a proxy but i wanna replace the protocol!
    """
    
    protocol = None
    
    def connectionMade(self):
        """" I reject ip bans. """
        if self.transport.getPeer().host in self.factory.settings.ipbans:
            self.transport.loseConnection()        
    
    
    def dataReceived(self, data):
        if self.protocol:
            self.protocol.dataReceived(data)
            
        else:
            isV3 = False
            
            # Try to detect the protocol
            version = self._detectProtocolVersion(data)
            if version != False:
                # Creates a new Protocol based on the version id
                try:
                    self.protocol = globals()['Protocol%d' % version]()
                except AttributeError:
                    log.msg('Can\'t find protocol version %d (Protocol%d)' % (version, version))
                    self.transport.loseConnection()
                    return False
            else:
                # Detection failed assume v3
                self.protocol = Protocol3()
                isV3 = True
                
    
            self.transport.logstr = "%s,%s,%s" % (self.protocol.__class__.__name__,
                                        self.transport.sessionno,
                                        self.transport.hostname)            
            
            
            self.protocol.factory = self.factory
            self.protocol.makeConnection(self.transport)
            if isV3:
                self.protocol.dataReceived(data)
            elif len(data) > 12:
                self.protocol.dataReceived(data[12:])
                
            # Now switch the protocol
            # self.transport.protocol = self.protocol
        
            
    def _detectProtocolVersion(self, data):
        """ I detect a "version\0<version#>" Packet
        """
        try:
            data = struct.unpack('!8sI', data[0:12])
            if data[0] == "version\0":
                return data[1]
            else:
                return False
            
        except struct.error:
            return False


class Protocol3(protocol.Protocol):
    """Warzone 2100 Lobby Protocol for (may 2.2) and  2.3 Clients"""

    # Status codes for self._sendStatusMessage
    SUCCESS_OK = 200
    CLIENT_ERROR_HOSTNAME_NOT_ACCEPTABLE = 403    
    CLIENT_ERROR_NOT_ACCEPTABLE = 406


    # Needed all over
    lobbyVersion = 3
    
    # To check the gamehosts connectivity
    gamePort = 2100

    # Holder for the game of the current connection
    game = None
    
    # List of Vars for the GAMESTRUCT
    # @see: http://developer.wz2100.net/wiki/NewLobbyProtocol
    gameStructVars = ('gStructVer',
                      'description',
                      'dwSize',
                      'dwFlags',
                      'host1',
                      'maxPlayers',                      
                      'currentPlayers',                      
                      'dwUFlag0',
                      'dwUFlag1',
                      'dwUFlag2',
                      'dwUFlag3',
                      'host2',
                      'host3',
                      'extra',
                      'mapname',
                      'hostplayer',
                      'multiVer',
                      'modlist',                      
                      'wzVerMajor',
                      'wzVerMinor',
                      'isPrivate',
                      'isPure',
                      'mods',
                      'gameId',
                      'future2',
                      'future3',
                      'future4',
                    ) 
        

    
    # String sizes for the according values
    gameStructCharSizes = {'description'    :      64,
                           'host1'          :      40,
                           'host2'          :      40,
                           'host3'          :      40,
                           'multiVer'       :      64,
                           'modlist'        :     255,
                           'extra'          :     159,
                           'mapname'        :      40,
                           'hostplayer'     :      40,         
                           }
    
    # Prebuild the struct
    gameStruct = struct.Struct('!I%dsii%ds6i%ds%ds%ds%ds%ds%ds%ds9I' % 
                                    (gameStructCharSizes['description'],
                                     gameStructCharSizes['host1'],
                                     gameStructCharSizes['host2'],
                                     gameStructCharSizes['host3'],
                                     gameStructCharSizes['extra'],
                                     gameStructCharSizes['mapname'],
                                     gameStructCharSizes['hostplayer'],
                                     gameStructCharSizes['multiVer'],
                                     gameStructCharSizes['modlist'],
                                    )
    )
    
    # And prefetch its size
    gameStructSize = gameStruct.size        
                               
    # If not "None" wait for more data to execute the "cmd"
    waitData = None
    
    
    def connectionMade(self):
        self.gameDB = self.factory.gameDB
        self.settings = self.factory.settings
    
    
    def dataReceived(self, data):
        """ Handles an incoming command 
            and forwards its to the do_X handler.
        """
        if not self.waitData:
            if len(data) == 5:
                cmd = 'do_%s' % data[:4].lower()
                
                if cmd == 'do_addg':
                    self.waitData = 'do_addg'
                    return True
                                
                data = u''
                
            elif len(data) == self.gameStructSize:
                cmd = 'do_updateGame'
            else:
                cmd = 'do_%s' % data[:4].lower()
                data = data[5:]                
        
        else:
            cmd = self.waitData
            self.waitData = None
            
        # Try to execute that command
        try:
            log.msg('%s: Executing' % cmd)
            func = getattr(self, cmd)            
            if not func(data):
                log.msg('%s: Failed' % cmd)
                self.transport.loseConnection()
                
        except Exception, e:
            self._logException(e)
            
    
    def connectionLost(self, reason):
        """ This will be called when the client
        closed its connection.
        """
        if self.game:
            if self.gameDB.removeGame(self.game):
                log.msg('Removed aborted/closed game')
            else:
                log.msg('Failed to remove the game!')
            
    
    def do_list(self, data = None):
        """ Sends the list of games.
        
        Format:    (unsigned int)<number of games>
                   <number of games> * GAMESTRUCT
                   
        May closes the connection on errors.
        """
        games = self.gameDB.getGames()
        self.transport.write(struct.pack('!I', len(games)))
        
        # Loop optimization        
        encodeGame = self._encodeGame
        write = self.transport.write
        
        # Generate a chained deferred
        d = defer.Deferred()
        for game in games.itervalues():
            d.addCallback(lambda ign: encodeGame(game)).addCallback(lambda x: write(x))
            
        # add an error handler
        d.addErrback(self._logException)
        
        # and run the generated defered
        d.callback('')
        
        return True
            
            
    def do_gaid(self, data = None):
        """ 
        I'm the helper for the "gaid" command, i
        run "wzlobby.game.Game.createGame" and return the result
        to the client.
        """
        
        self.game = self.gameDB.createGame(self.lobbyVersion)
        
        log.msg('Created game ID: %d' % self.game.get('gameId'))
        self.transport.write(struct.pack('!I', int(self.game.get('gameId'))))
        
        return True            
                    
    
    def do_addg(self, data = None):
        """ I check the games connectivity and send a status message.
        """
        
        self.do_updateGame(data)
        
        d = self.gameDB.checkGame(self.game)
        d.addCallback(lambda x: 
                self._sendStatusMessage(
                    self.SUCCESS_OK, 
                    self.settings.getMotd(self.game['multiVer'])
                )
        )
        d.addErrback(lambda x: 
                self._sendStatusMessage(
                    self.CLIENT_ERROR_NOT_ACCEPTABLE, 
                    'Game unreachable, failed to open a connection to port %d' % self.gamePort
                )
        )
        
        # Start the loopingcall for this game
        self.gameDB.loopCheck(self.game)            
        
        return True
    
    
    def do_updateGame(self, data):
        """ I will be called whenever i receive a Gamestruct
        from the gamehost.
        """
        
        try:
            # Extract the data from the gamestruct
            data = self.gameStruct.unpack(data)
            # Create a dict from it while using self.gameStructVars as keys 
            data = dict(izip(self.gameStructVars, data))
            
            # Remove unused keys
            del(data['host1'], data['host2'], data['host3'], 
                data['dwSize'], data['dwFlags'], data['dwUFlag0'], 
                data['dwUFlag1'], data['dwUFlag2'], data['dwUFlag3'],
                data['future2'], data['future3'], data['future4'],
                data['extra'])
            
            # Add the games ip and the gamesport
            data['gameHost'] = self.transport.getPeer().host
            data['gamePort'] = self.gamePort
                        
        except struct.error:
            return False
        
        # Now update the game
        self.gameDB.updateGame(data['gameId'], data)
        
        # Fix for bogus clients (<=2.3.7) which connect twice
        if not self.game:
            self.game = self.gameDB.getGaidGame(data['gameId'])
                
        return True
    
    
    def _sendStatusMessage(self, code, message):
        """ I send a status message to the game host
            Format    (unsigned int)<message length>
                      (unsigned int)<response code>
                      char[<message length>]<message>)
                      
            I close the connection when struct.pack fails.
        """
        
        log.msg('Sending %d:%s' % (code, message))
        try:
            d = defer.succeed(struct.pack('!II%ds' % len(message), code, len(message), str(message)))
            d.addCallback(lambda m: self.transport.write(m))
        except AttributeError:
            log.msg('Failed to send status %d to the client' % code)
            self.transport.loseConection() 
            
    
    def _encodeGame(self, game):
        """ I return the Network byte string for a game.
        
        @see: WZLobbyProtocol3.gameStructVars
        """
        vars = [game['gStructVer'],
                encodeCString(game['description'], self.gameStructCharSizes['description']),
                1, # dwSize
                0,
                encodeCString(game['gameHost'], self.gameStructCharSizes['host1']), # host1
                game['maxPlayers'],
                game['currentPlayers'],
                0, # dwUFlag0
                0, # dwUFlag1
                0, # dwUFlag2
                0, # dwUFlag3
                encodeCString(u'', self.gameStructCharSizes['host2']), # host2
                encodeCString(u'', self.gameStructCharSizes['host3']), # host3
                encodeCString(u'Extra', self.gameStructCharSizes['extra']), # Extra
                encodeCString(game['mapname'], self.gameStructCharSizes['mapname']),
                encodeCString(game['hostplayer'], self.gameStructCharSizes['hostplayer']),
                encodeCString(game['multiVer'], self.gameStructCharSizes['multiVer']),
                encodeCString(game['modlist'], self.gameStructCharSizes['modlist']),
                game['wzVerMajor'],
                game['wzVerMinor'],
                game['isPrivate'],
                game['isPure'],
                game['mods'],
                game['gameId'],
                0xBAD02, # future2,
                0xBAD03, # future3,
                0xBAD04, # future4,
        ]
       
        try:
            return self.gameStruct.pack(*vars)
        except struct.error, e:
            log.msg('%s, count of arguments was %d' % (e, len(vars)))
            raise e
        
        
    def _logException(self, exception):
        """ Small helper to log an error and close
        the connection
        """
        log.err(exception)
        self.transport.loseConnection()