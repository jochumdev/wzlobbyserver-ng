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

from twisted.internet import defer, reactor
from twisted.python import log
from twisted.internet.task import LoopingCall

from txpostgres import txpostgres
from phpass import PasswordHash

from datetime import datetime, timedelta
from random import choice
import string

from wzlobby import settings

class Database(object):
    def __init__(self):
        self.pw_check = PasswordHash().check_password

        self._forums_conn = txpostgres.Connection()
        self._forums_conn.connect(host=settings.phpbb_host,
                                  database=settings.phpbb_db,
                                  user=settings.phpbb_user,
                                  password=settings.phpbb_pass)

        self._lobby_conn = txpostgres.Connection()
        self._lobby_conn.connect(host=settings.lobby_host,
                                  database=settings.lobby_db,
                                  user=settings.lobby_user,
                                  password=settings.lobby_pass)

        # Start the cleanup interval.
        self._cleanup_call = LoopingCall(self._cleanup)
        self._cleanup_call.start(settings.cleanup_interval, now=False)
        # and run it once in 2 seconds.
        reactor.callLater(2, self._cleanup)


    def check_user_password(self, username, password, ip):
        def check_cb(result):
            if len(result) == 0:
                # User Not found.
                return defer.fail(Exception())

            if (self.pw_check(password, result[0][0])):
                return self._create_user_token(username, ip)
            else:
                return defer.fail(Exception())

        if settings.debug:
            log.msg("Checking the password from \"%s\"" % username)

        d = self._forums_conn.runQuery(
            "SELECT user_password FROM " + settings.phpbb_table + " WHERE username = %s AND user_inactive_reason = 0;",
            (username,)
        )
        d.addCallback(check_cb)

        return d


    def check_user_token(self, username, token, ip):
        def check_cb(result):
            if len(result) == 0:
                # User token not found, invalid token or token expired.
                return defer.fail(Exception())

            # Update ip and extend token lifetime
            self._lobby_conn.runOperation(
                "UPDATE tokens set last_ip = %s WHERE username = %s AND token = %s;",
                (ip, username, token)
            )

            return {"token": result[0][0], "session":  self._create_session(username)}

        def check_user_cb(result):
            if len(result) == 0:
                # User not found.
                return defer.fail(Exception())

            # Now check the token
            d = self._lobby_conn.runQuery(
                        "SELECT token FROM tokens WHERE username = %s AND token = %s AND updated_at >= %s;",
                        (username,
                         token,
                         datetime.now() - timedelta(days=settings.token_lifetime),
                        )
            )
            return d

        if settings.debug:
            log.msg("Checking user \"%s\", token \"%s\"" % (username, token))

        # First check if the user is still valid.
        d = self._forums_conn.runQuery(
            "SELECT username FROM " + settings.phpbb_table + " WHERE username = %s AND user_inactive_reason = 0;",
            (username,)
        )
        d.addCallback(check_user_cb)
        d.addCallback(check_cb)

        return d


    def check_user_session(self, username, session):
        if settings.debug:
            log.msg("Checking user \"%s\", session \"%s\"" % (username, session))

        d = self._lobby_conn.runQuery(
            "SELECT username FROM sessions WHERE username = %s AND session = %s AND created_at >= %s;",
            (username,
             session,
             datetime.now() - timedelta(seconds=settings.session_lifetime),
            )
        )
        d.addCallback(lambda x: len(x) == 1)

        return d


    def _create_user_token(self, username, ip):
        token = ''.join([choice(string.letters) for i in range(settings.token_length)])
        self._lobby_conn.runOperation(
            "INSERT INTO tokens (username, token, last_ip) VALUES (%s, %s, %s)",
            (username, token, ip)
        )

        if settings.debug:
            log.msg("Created token \"%s\" for user \"%s\"" % (token, username))

        return {"token": token, "session": self._create_session(username)}

    def _create_session(self, username):
        session = ''.join([choice(string.letters) for i in range(settings.session_length)])
        self._lobby_conn.runOperation(
            "INSERT INTO sessions (username, session) VALUES (%s, %s)",
            (username, session)
        )

        if settings.debug:
            log.msg("Created session \"%s\" for user \"%s\"" % (session, username))

        return session

    def _cleanup(self):
        if settings.debug:
            log.msg("Running the cleanup")

        self._lobby_conn.runOperation(
            "DELETE FROM tokens WHERE updated_at < %s",
            (datetime.now() - timedelta(days=settings.token_lifetime),)
        )

        self._lobby_conn.runOperation(
            "DELETE FROM sessions WHERE created_at < %s",
            (datetime.now() - timedelta(seconds=settings.session_lifetime),)
        )
