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

__all__ = ['Protocol3']

from twisted.python import log
from twisted.internet import defer, protocol
from twisted.python.failure import Failure

import struct
from itertools import izip

from wzlobby import settings

SUCCESS_OK = 200
CLIENT_ERROR_NOT_ACCEPTABLE = 406

def encodeCString(string, buf_len):
    # If we haven't got a string return an empty one
    if not string:
        return str('\0' * buf_len)

    return str(string[:buf_len - 1].ljust(buf_len, "\0").encode('utf8'))


class Protocol3(protocol.Protocol):
    """Warzone 2100 Lobby Protocol for (may 2.2) and  2.3 Clients"""

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


    def connectionLost(self, reason):
        """ This will be called when the client
        closed its connection.
        """
        if self.game:
            self.gameDB.remove(self.game)


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
                try:
                    cmd = 'do_%s' % data[:4].lower()
                    data = data[5:]
                except AttributeError:
                    pass

        else:
            cmd = self.waitData
            self.waitData = None

        # Try to execute that command
        try:
            log.msg('executing %s' % cmd)

            func = getattr(self, cmd)
            if not func(data):
                log.msg('%s: Failed' % cmd)
                self.transport.loseConnection()
        except AttributeError:
            pass
        except Exception, e:
            self._logException(e)


    def do_list(self, data=None):
        """ Sends the list of games.
        
        Format:    (unsigned int)<number of games>
                   <number of games> * GAMESTRUCT
                   
        May closes the connection on errors.
        """
        games = []
        for game in self.gameDB.itervalues():
            if not game['description']:
                continue
            games.append(self._encodeGame(game))

        self.transport.write(struct.pack('!I', len(games)))
        for game in games:
            self.transport.write(game)

        return True


    def do_gaid(self, data=None):
        """ 
        I'm the helper for the "gaid" command, i
        run "wzlobby.game.Game.createGame" and return the result
        to the client.
        """

        self.game = self.gameDB.create(self.lobbyVersion, True)
        self.transport.write(struct.pack('!I', int(self.game.get('gameId'))))

        return True


    def do_addg(self, data=None):
        """ I check the games connectivity and send a status message.
        """
        if data:
            self.do_updateGame(data)

            log.msg('new game %d: "%s" from "%s".' % (self.game['gameId'],
                                                      self.game['description'].encode('utf8'),
                                                      self.game['hostplayer'].encode('utf8')))

        d = self.gameDB.check(self.game)
        d.addCallback(self._sendStatusMessage, SUCCESS_OK)
        d.addErrback(self._sendStatusMessage, CLIENT_ERROR_NOT_ACCEPTABLE)

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
            data['host'] = self.transport.getPeer().host
            data['port'] = self.gamePort

        except struct.error:
            log.err('Can\'t unpack the incoming GAMESTRUCT')
            return False

        # Now update the game
        self.gameDB.updateGame(data['gameId'], data)

        if not self.game:
            self.game = self.gameDB.get(data['gameId'])

        return True


    def _sendStatusMessage(self, message, code):
        """ I send a status message to the game host
            Format    (unsigned int)<message length>
                      (unsigned int)<response code>
                      char[<message length>]<message>)
                      
            I close the connection when struct.pack fails.
        """

        if isinstance(message, Failure):
            message = message.getErrorMessage()

        if settings.debug:
            log.msg('Sending %d:%s' % (code, message))
        try:
            d = defer.succeed(struct.pack('!II%ds' % len(message), code, len(message), str(message)))
            d.addCallback(lambda m: self.transport.write(m))
        except AttributeError:
            log.msg('Failed to send status %d to the client' % code)
            self.transport.loseConection()


    def _encodeGame(self, game):
        """ I return the Network byte string for a game.
        
        @see: Protocol3.gameStructVars
        """
        vars = [game['gStructVer'],
                encodeCString(game['description'], self.gameStructCharSizes['description']),
                1, # dwSize
                0,
                encodeCString(game['host'], self.gameStructCharSizes['host1']), # host1
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
