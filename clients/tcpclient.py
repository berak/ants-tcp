#!/usr/bin/env python

import time
import sys
import threading
import re
import string
import random
import subprocess
from socket import socket, AF_INET, SOCK_STREAM

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

USAGE="""

    tcpclient.py   host_or_ip  port  botpath  player_nick  password  [num_rounds]

    if running on windows or if the botpath contains spaces,
    you have to wrap it with "", eg.: "java /x/y/MyBot", "e:\\ai\\bots\\mybot.exe"

    player_nick and password may only contain ascii_letters, '_', and numbers

"""


def readline(sock):
    s = BytesIO()
    while sock:
        c = sock.recv(1)
        if not c:
            break
        elif c==b'\r':
            continue
        elif c==b'\n':
            break
        else:
            s.write(c)
    return s.getvalue()


time_out = 1.0
def tcp(host, port, bot_command, user, password, options):
    global time_out
    # spread out if in batch mode, to allow more random ordering on the server
    time.sleep(time_out + 5.0 * random.random())

    # Start up the network connection
    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(240)
    sock.connect((host, port))
    if sock:
        sys.stderr.write('\n\nconnected to %s:%d as %s\n' % (host,port,user))
    else:
        sys.stderr.write('\n\nfailed to connect to %s:%d as %s\n' % (host,port,user))
        return

    # send greetz
    sock.sendall(('USER %s %s\n' % (user, password)).encode('utf-8'))

    # start bot
    bot = subprocess.Popen(
        bot_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )

    bot_input = BytesIO()
    bot_output = BytesIO()

    while sock:
        end_reached = False
        finish = False
        # get input, send it to bot
        while sock:
            try:
                line = readline(sock)
            except:
                finish = True
                break

            if not line:
                bot_input.write(b'end\ngo\n')
                if end_reached:
                    finish = True
                    break
                continue # bad connection, keep on trying

            print(line.decode('ascii', 'replace'))
            if line.startswith(b'INFO:'): # not meant for the bot
                if (line.find(b'already running')>0) or (line.find(b'already queued')>0):
                    ## penalty for getting eliminated, but still trying to be first in the upcoming game.
                    time_out += 10.0 + 10.0*random.random()
                continue

            bot_input.write(line)
            bot_input.write(b'\n')

            if line.startswith(b'end'):
                end_reached = True
            elif line.startswith(b'ready'):
                time_out = 1.0
                break
            elif line.startswith(b'go'):
                if end_reached:
                    finish = True
                break

        bot.stdin.write(bot_input.getvalue())
        bot.stdin.flush()

        bot_input.seek(0)
        bot_input.truncate()

        if finish or not sock:
            break

        # get bot output, send to serv
        while 1:
            answer = bot.stdout.readline()
            if not answer.strip():
                break
                
            # weed out stuff meant for the extended visualizer
            if answer.startswith(b'v'): continue
            if answer.startswith(b'i'): continue
                
            bot_output.write(answer)
            if answer.startswith(b'go'):
                break

        output = bot_output.getvalue()
        bot_output.seek(0)
        bot_output.truncate()

        # if there's no orders, send at least an empty line
        if not output:
            output = b'\r\n'
        print(output.decode('ascii', 'replace'))
        sock.sendall(output)

    try:
        sock.close()
        sock = None
    except:
        pass

    try:
        bot.kill()
        time.sleep(0.5)
        bot.wait()
    except:
        pass


def check_string( pname, use ):
    """ check for invalid chars since json won't like them. """
    for l in pname:
        if l in string.ascii_letters: continue
        if l in string.digits : continue
        if l =='_' : continue
        print( "your "+use+" (" + pname + ") contains invalid characters, please choose another one!" )
        return False
    if len(use) > 32:
        print( "username and password must not be longer than 32 chars." )
        return False
    return True


def main():
    if len(sys.argv) < 6:
        print(USAGE)
        return

    host = sys.argv[1]
    port = int(sys.argv[2])
    botpath = sys.argv[3]
    pname = sys.argv[4]
    password = sys.argv[5]

    if not check_string(pname, "botname"):
        return
    if not check_string(password, "password"):
        return

    try:
        rounds = int(sys.argv[6])
    except:
        rounds = 1

    for i in range(rounds):
        tcp(host, port, botpath, pname, password, {})


if __name__ == "__main__":
    main()
