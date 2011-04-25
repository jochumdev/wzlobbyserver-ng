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


    def check_user_password(self, username, password):
        def check_cb(result):
            if len(result) == 0:
                # User Not found.
                return False

            return self.pw_check(password, result[0][0])

        d = self._forums_conn.runQuery(
            "SELECT user_password FROM " + settings.phpbb_table + " WHERE username = %s AND user_inactive_reason = 0;",
            (username,)
        )
        d.addCallback(check_cb)

        return d


    def check_user_token(self, username, token):
        def check_cb(result):
            if len(result) == 0:
                # User Not found, invalid token or token expired.
                return False

            return result[0][0]

        d = self._lobby_conn.runQuery(
            "SELECT token FROM tokens WHERE username = %s AND token = %s AND updated_at >= %s;",
            (username,
             token,
             datetime.now() - timedelta(days=settings.token_expires),
            )
        )
        d.addCallback(check_cb)

        return d


    def get_user_token(self, username):
        def check_cb(result):
            if len(result) == 0:
                # No token Found or Token expired, create a new one.
                token = ''.join([choice(string.letters) for i in range(settings.token_length)])
                self._lobby_conn.runOperation(
                    "INSERT INTO tokens (username, token) VALUES (%s, %s)",
                    (username, token,)
                )

                return token

            # token found return it.
            return result[0][0]

        d = self._lobby_conn.runQuery(
            "SELECT token FROM tokens WHERE username = %s AND updated_at >= %s;",
            (username,
             datetime.now() - timedelta(days=settings.token_expires),
            )
        )
        d.addCallback(check_cb)

        return d
