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
    - This needs to be implemented

Requirements
-----------
* Twisted >=10.1

Installation
-----------
* clone this repository
* edit wzlobby/settings.py for your needs

Basic usage:
-----------
start
----

    cd <your clone>
    ./bin/wzlobbyserver.py

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
