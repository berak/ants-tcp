#!/usr/bin/env python

import time
import sys
import threading
import re
import string
import random
import subprocess
from socket import socket, AF_INET, SOCK_STREAM


USAGE="""

    tcpclient.py   host_or_ip  port  botpath  player_nick  password  [num_rounds]
    
    if running on windows or if the botpath contains spaces,
    you have to wrap it with "", eg.: "java /x/y/MyBot", "e:\\ai\\bots\\mybot.exe"
    
    player_nick and password may only contain ascii_letters, '_', and numbers
    
"""



def readline(sock):
  s=""
  while(sock):
     c = sock.recv(1)
     if ( not c ):
        break
     elif ( c=='\r' ):
        continue
     elif ( c=='\n' ):
        break
     else:
        s += c
  return s


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
        sys.stderr.write("\n\nconnected to %s:%d as %s\n" % (host,port,user))
    else:
        sys.stderr.write("\n\nfailed to connect to %s:%d as %s\n" % (host,port,user))
        return
            
    # send greetz
    sock.sendall("USER %s %s\n" % (user, password) )
    
    # start bot
    try:
        bot = subprocess.Popen(bot_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=".")
    except:
        print( 'your bot ('+str(bot_command)+') failed to start!' )
        return;

    while sock:
        end_reached = False
        # get input, send it to bot
        bot_input = ""
        while sock:
            try:
                line = readline(sock)
            except: return
                
            if not line: 
                if end_reached:
                    sock.close()
                    sock = None
                    bot.kill()
                    return
                continue # bad connection, keep on trying
                
            print( line )            
            if line.startswith("INFO:"): # not meant for the bot
                if (line.find("already running")>0) or (line.find("already queued")>0): 
                    ## penalty for getting eliminated, but still trying to be first in the upcoming game.
                    time_out += 10.0 + 10.0*random.random()
                continue
                
            bot_input += line + "\n"
            if line.startswith("end"):
                end_reached = True                
            if line.startswith("ready"):
                time_out = 1.0
                break
            if line.startswith("go"):
                if end_reached:
                    sock.close()
                    sock = None
                    bot.kill()
                    return
                break
            
        if not sock:
            break
            
        bot.stdin.write(bot_input)
        bot.stdin.flush()
        
        # get bot output, send to serv
        client_mess=""
        while 1:
            answer = bot.stdout.readline()
            if not answer:	break
            client_mess += answer 
            if answer.startswith("go"):	break
        
        # if there's no orders, send at least an empty line
        if (client_mess==""):
            client_mess="\r\n" 
        print( client_mess )

        sock.sendall( client_mess )
                
    try:
        bot.kill()
    except:
        pass



def check_string( pname, use ):
    """ check for invalid chars since json won't like them. """
    for l in pname:
        if l in string.letters: continue
        if l in string.digits : continue
        if l =='_' : continue
        print( "your "+use+" (" + pname + ") contains invalid characters, please choose another one!" )
        return False
    return True


def main():
    if len(sys.argv) < 6:
        print USAGE
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
        
    # keep konsole window open (for debugging)
    sys.stdin.read()
    
if __name__ == "__main__":
    main()
