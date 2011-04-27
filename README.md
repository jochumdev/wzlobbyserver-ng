Warzone 2100 Lobbyserver - next generation
============

This is my implementation of the new Warzone Masterserver.
Read more about its protocol at http://developer.wz2100.net/wiki/NewLobbyProtocol

TODO
-----------
* Application organisation
    - setuptools installer
    - config file per commandline
    - init.d script
    - pid file and log file location
    
* wzlobby.protocol.ProtocolSwitcher
    - It should rebase the protocol not proxy it
    
* Protocol v4
    - Needs more tests

Requirements
-----------
* Twisted >=10.1
* socketrpc >=0.0.2
* pymongo (for bson)
* txpostgres - https://github.com/wulczer/txpostgres
* phpass - https://github.com/exavolt/python-phpass

Installation
-----------
* clone this repository
* Import the lobby db: $sudo postgres psql warzone_lobby < ./data/lobby.sql
* copy wzlobby/settings.py.dist to wzlobby/settings.py
* edit wzlobby/settings.py for your needs

Basic usage:
-----------
start
----

    cd <your clone>
    ./bin/wzlobbyserver.py
    
or in console:

	./bin/wzlobbyserver.py -n

stop
----

    cd <your clone>
    kill $(cat twistd.pid)

reload
----

    cd <your clone>
    kill -HUP $(cat twistd.pid)

view the log
----

    cd <your clone>
    tail -f twistd.log
