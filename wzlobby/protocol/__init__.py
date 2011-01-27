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
from twisted.internet import protocol

import struct

from wzlobby.protocol.protocol3 import Protocol3
from wzlobby.protocol.protocol4 import Protocol4

class ProtocolSwitcher(protocol.Protocol):
    """ I try to detect a version command and switch
    the protocol.
    TODO: i'm a proxy but i wanna replace the protocol!
    """
    
    protocol = None
    
    debug = False
    
    def connectionMade(self):
        """" I reject ip bans. """
        
        self.debug = self.factory.noisy
        
        if self.transport.getPeer().host in self.factory.settings.ipbans:
            self.transport.loseConnection()
            
            
    def connectionLost(self, reason):
        if self.protocol:
            self.protocol.connectionLost(reason)     
    
    
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
            
            self.protocol.debug = self.debug
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