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

from twisted.internet import protocol, defer
from twisted.python import log

try:
    from cStringIO import StringIO
except ImportError, e:
    from StringIO import StringIO

import struct
import bson

import xmlrpclib

# -32768 - 32000 is reserved for RPC errors
# @see: http://xmlrpc-epi.sourceforge.net/specs/rfc.fault_codes.php
# Ranges of errors
PARSE_ERROR = xmlrpclib.PARSE_ERROR
SERVER_ERROR = xmlrpclib.SERVER_ERROR
APPLICATION_ERROR = xmlrpclib.APPLICATION_ERROR
#SYSTEM_ERROR                = -32400
#TRANSPORT_ERROR             = -32300

# Specific errors
NOT_WELLFORMED_ERROR = xmlrpclib.NOT_WELLFORMED_ERROR
UNSUPPORTED_ENCODING = xmlrpclib.UNSUPPORTED_ENCODING
INVALID_ENCODING_CHAR = xmlrpclib.INVALID_ENCODING_CHAR
INVALID_XMLRPC = xmlrpclib.INVALID_XMLRPC
METHOD_NOT_FOUND = xmlrpclib.METHOD_NOT_FOUND
#INVALID_METHOD_PARAMS       = -32602
#INTERNAL_ERROR              = -32603

STATUS_OK = 0

Fault = xmlrpclib.Fault

class Protocol(protocol.Protocol):

    bytesNeeded = None
    bytesCount = None
    socketBuf = None

    debug = False

    def dataReceived(self, data):
        if self.socketBuf == None:
            self.socketBuf = StringIO()
            self.bytesCount = 0

            try:
                self.bytesNeeded = struct.unpack("!I", data[:4])[0]
            except struct.error:
                self.socketBuf = None
                self.bsonReceived(Fault(NOT_WELLFORMED_ERROR, 'Haven\'t got a length.'))
                return False

            data = self._writeBuf(data, 4)

        else:
            data = self._writeBuf(data)


        if self.bytesCount == self.bytesNeeded:
            obj = self.socketBuf.getvalue()
            obj = self.decode(obj)
            self.socketBuf = None

            self.bsonReceived(obj)

        if data:
            self.dataReceived(data)


    def bsonReceived(self, obj):
        raise NotImplementedError


    def _writeBuf(self, data, startFrom=0):
        """ 
        Writes bytes from data into C{self.socketBuf<StringIO.StringIO} until
        self.bytesNeeded has been reached.
        
        Starts to read from startFrom if it has been given
        """
        bytes = len(data) - startFrom
        if bytes + self.bytesCount > self.bytesNeeded:
            bytesToRead = self.bytesNeeded - self.bytesCount
            self.socketBuf.write(data[startFrom:bytesToRead + startFrom])
            data = data[bytesToRead + startFrom:]

            self.bytesCount += bytesToRead
        else:
            self.socketBuf.write(data[startFrom:])
            self.bytesCount += bytes
            data = None

        return data


    def encode(self, data):
        """
        Encodes data returns a BSON object or
        a Fault
        """
        try:
            return bson.BSON.encode(data)
        except bson.errors.InvalidBSON:
            return Fault(NOT_WELLFORMED_ERROR, 'Invalid BSON Data')
        except bson.errors.InvalidStringData:
            return Fault(UNSUPPORTED_ENCODING, 'Non UTF-8 BSON Data')



    def decode(self, data):
        """
        A proxy method for BSON.decode
        TODO: This will block if a lot data has been received!
        """
        try:
            return bson.BSON(data).decode()
        except bson.errors.InvalidBSON:
            return Fault(NOT_WELLFORMED_ERROR, 'Invalid BSON Data')
        except bson.errors.InvalidStringData:
            return Fault(UNSUPPORTED_ENCODING, 'Non UTF-8 BSON Data')


class Server(Protocol):

    def bsonReceived(self, data):
        """ Handles an incoming command 
            and forwards its to the do_X handler.
        """
        if isinstance(data, Fault):
            return defer.fail(data)

        if not 'method' in data \
          or not 'params' in data \
          or not 'id' in data:
            self.sendResponse(NOT_WELLFORMED_ERROR)


        cmd = 'do_%s' % data['method']

        if self.debug:
            log.msg('%s: Executing' % cmd)

        try:
            func = getattr(self, cmd)
        except AttributeError, e:
            log.msg('Got an unknown command "%s"' % cmd)
            self.sendResponse(METHOD_NOT_FOUND)
            return False

        d = defer.maybeDeferred(func, data['params'])
        d.addCallback(self._bsonCb, data['id'])
        d.addErrback(self._bsonEb, data['id'])

        return d


    def _bsonEb(self, failure, id):
        obj = failure.value
        if isinstance(obj, Fault):
            self.sendResponse(obj.faultCode, obj.faultString, id)
        elif isinstance(obj, Exception):
            self.sendResponse(APPLICATION_ERROR, "%s: %s" % (obj.__class__.__name__, repr(obj)), id)
        else:
            self.sendResponse(APPLICATION_ERROR, repr(obj), id)


    def _bsonCb(self, result, id):
        if isinstance(result, Fault):
            self.sendResponse(result.faultCode, result.faultString, id)
        else:
            self.sendResponse(STATUS_OK, result, id)


    def sendResponse(self, code=STATUS_OK, result='', id=None):
        data = {'status': code, 'result': result, 'id': id}

        data = self.encode(data)
        self.transport.write(struct.pack('!I', len(data)) + data)


class Client(Protocol):
    def bsonReceived(self, obj):
        if isinstance(obj, Fault):
            self.faultReceived(obj)
            return False

        if obj['status'] >= STATUS_OK:
            self.calls[obj['id']].callback(obj['result'])
        else:
            self.calls[obj['id']].errback(Fault(obj['status'], obj['result']))


    def faultReceived(self, fault):
        raise fault


    def callRemote(self, method, params=''):
        self.id += 1
        data = self.encode({'method': method,
                            'params': params,
                            'id': self.id})

        data = struct.pack('!I', len(data)) + data
        self.transport.write(data)

        finished = defer.Deferred()
        self.calls[self.id] = finished

        return finished
