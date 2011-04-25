# -*- coding: utf-8 -*-
# vim: set et sts=4 sw=4 encoding=utf-8:

from distutils.version import StrictVersion

#### START Settings ####

debug = False

check_interval = 10

motd_default = "Welcome to Warzone! Your game is now listed in the lobby server."
motd = (
        (
            StrictVersion('999.9.9'),
            motd_default,
        ),
        (
            StrictVersion('2.3.6'),
            "Your game is now listed in the lobby server. Please upgrade your Warzone to 2.3.7! See http://wz2100.net.",
        ),
        (
            StrictVersion('2.2'),
            "This server will not support your version of Warzone much longer!\n Please upgrade your game.  See www.wz2100.net.",
        ),
)

ipbans = set()

badwords = set()

login_required = False

token_length = 32
token_expires = 31

# Forum DB for Auth
phpbb_host = "localhost"
phpbb_db = "warzone_forums"
phpbb_user = ""
phpbb_pass = ""
phpbb_table = "phpbb3_users"

# DB for the lobby.
lobby_host = phpbb_host
lobby_db = "warzone_lobby"
lobby_user = phpbb_user
lobby_pass = phpbb_pass

#### END OF Settings ####

def getMotd(version):
    try:
        version = StrictVersion(version)
    except ValueError:
        return motd_default

    for k, v in motd:
        if version <= k:
            bestMatch = v

    return bestMatch

if __name__ == '__main__':
    print "%s: %s\n" % ('2.1', getMotd('2.1'))
    print "%s: %s\n" % ('2.2', getMotd('2.2'))
    print "%s: %s\n" % ('2.3.6', getMotd('2.3.6'))
    print "%s: %s\n" % ('2.3.7', getMotd('2.3.7'))
    print "%s: %s\n" % ('master, netcode 0.0000', getMotd('master, netcode 0.0000'))
