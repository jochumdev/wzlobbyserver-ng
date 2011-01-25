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

from twisted.internet import reactor, defer, protocol

__all__ = ['testConnect']

class CallbackAndDisconnectProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.deferred.callback('Connected!')
        self.transport.loseConnection()
        

class ConnectionTestFactory(protocol.ClientFactory):
    protocol = CallbackAndDisconnectProtocol
    
    # Disable log messages
    noisy = False
    
    def __init__(self):
        self.deferred = defer.Deferred()
        
    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)
        

def testConnect(host, port):
    """ Returns a deferred which tries to connect 
    to the given host and port.
    """
    testFactory = ConnectionTestFactory()
    reactor.connectTCP(host, port, testFactory)
    
    return testFactory.deferred