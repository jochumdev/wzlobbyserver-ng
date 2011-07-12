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

# This is the V4 Variant of the Protocol - BSON.

__all__ = ['Protocol4']

from twisted.internet import defer
from twisted.python import log
from socketrpc.twisted_srpc import SocketRPCProtocol, set_serializer, Fault

from wzlobby import settings

set_serializer('jsonlib')

NO_GAME = -402
NOT_ACCEPTABLE = -403
WRONG_LOGIN = -404
LOGIN_REQUIRED = -405
SESSION_INVALID = -406

class Protocol4(SocketRPCProtocol):
    game = None

    lobbyVersion = 4

    def connectionMade(self):
        SocketRPCProtocol.connectionMade(self)

        self.debug = settings.debug
        self.gameDB = self.factory.gameDB
        self.db = self.factory.db

        self.authenticated = False


    def dispatch_call(self, method, id, args, kwargs):
        if not self.authenticated \
          and settings.login_required \
          and method != 'login':
            log.msg('Not executing %s - login required' % method)
            return defer.fail(
                    Fault(LOGIN_REQUIRED, "Please login first!")
            )

        log.msg('executing docall_%s' % method)

        return SocketRPCProtocol.dispatch_call(self, method, id, args, kwargs)


    def docall_login(self, username, password=None, token=None):
        def check_pass_cb(result):
            # Login ok
            self.authenticated = True
            return result

        def check_pass_eb(failure):
            self.authenticated = False
            return defer.fail(Fault(WRONG_LOGIN, "Password login failed, unknown user or wrong password!"))

        def check_token_cb(result):
            # Token login ok
            self.authenticated = True
            return result

        def check_token_eb(failure):
            self.authenticated = False
            return defer.fail(Fault(WRONG_LOGIN, "Token login failed, unknown user or wrong password!"))

        if token is None:
            d = self.db.check_user_password(username, password, self.transport.getPeer().host)
            d.addCallbacks(check_pass_cb, check_pass_eb)
        else:
            d = self.db.check_user_token(username, token, self.transport.getPeer().host)
            d.addCallbacks(check_token_cb, check_token_eb)

        return d


    def docall_logout(self):
        self.authenticated = False

        return defer.succeed("")


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

            return {"gameId": game['gameId'],
                    "result": result}


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


    def docall_addPlayer(self, gameId, slot, name, username, session):
        def check_cb(result):
            if result:
                game['currentPlayers'] += 1
                return defer.succeed('')
            else:
                return defer.fail(Fault(SESSION_INVALID, 'Users session is invalid!'))

        game = self.gameDB.get(gameId, False)
        if not game:
            return defer.fail(
                    Fault(NO_GAME, 'Game %d does not exists' % gameId)
            )

        d = self.db.check_user_session(username, session)
        d.addCallback(check_cb)

        return d


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
            # Skip empty games.
            if not game['description']:
                continue

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
