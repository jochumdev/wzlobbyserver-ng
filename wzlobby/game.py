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

__all__ = ['Game']

from UserDict import IterableUserDict

class Game(IterableUserDict):
    # Translation table for incoming data
    dataTypes = {'host'        :   'string',
                 'port'        :   'int',
                 'description' :   'string',
                 'currentPlayers': 'int',
                 'maxPlayers'  :   'int',
                 'lobbyVer'    :   'int',
                 'multiVer'    :   'string',
                 'wzVerMajor'  :   'int',
                 'wzVerMinor'  :   'int',
                 'isPure'      :   'bool',
                 'isPrivate'   :   'bool',
                 'gameId'      :   'int',
                 'mods'        :   'int',
                 'modlist'     :   'string',

                 # Since 2.3.6
                 'mapname'     :   'string',
                 'hostplayer'  :   'string',

                 # For Lobby Ver 3
                 'gStructVer'  :   'int',
                }


    def __init__(self, lobbyVer, gameId):
        # Internal store for the LoopingCall C{check>wzlobby.gamedb.gameDB.check}
        self.lCall = None

        # These are the defaults for a new game
        # from 2.3 source
        self.data = {
            'host'              :   None, # Our clients IP Address 
            'port'              :   0, # Gamehost port for clients
            'description'       :   None,
            'currentPlayers'    :   0,
            'maxPlayers'        :   0,
            'multiVer'          :   '',
            'wzVerMajor'        :   0,
            'wzVerMinor'        :   0,
            'isPure'            :   True,
            'isPrivate'         :   False,
            'gameId'            :   0,
            'mods'              :   0,
            'modlist'           :   u'',

            # Since 2.3.6
            'mapname'           :   u'',
            'hostplayer'        :   u'',

            # For Lobby Ver 3
            'gStructVer'        :   3,

            # Constructor vars
            'lobbyVer'          :   lobbyVer,
            'gameId'            :   gameId,
        }

    def __setitem__(self, k, v):
        """ Setter for self.data[k] 
        may raises a KeyError if the key is not in self.dataTypes
        """
        type = self.dataTypes[k]
        if type == 'string':
            self.data[k] = unicode(v, 'utf8').strip("\0")
        elif type == 'int':
            self.data[k] = int(v)
        elif type == 'bool':
            self.data[k] = bool(v)


    def update(self, data):
        for k, v in data.iteritems():
            self.__setitem__(k, v)

    def __del__(self):
        if self.lCall and self.lCall.running:
            self.lCall.stop()
