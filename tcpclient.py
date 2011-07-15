#!/usr/bin/env python

import time
import sys
import threading
import re
import string
import random
import subprocess

from socket import socket, AF_INET, SOCK_STREAM

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


def tcp(host, port, bot_command, user, options):      
    # spread out if in batch mode, to allow more random ordering on the server
    time.sleep(5.0 * random.random())

       
    # Start up the network connection
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host, port))
    if sock:
        sys.stderr.write("connected\n")
    else:
        print( "failed to connect to " + host + " on port " + str(port) )
        return
            
    # start bot
    try:
        bot = subprocess.Popen(bot_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=".")
    except:
        print( 'your bot ('+str(bot_command)+') failed to start!' )
        return;

    # send greetz and start the loop
    sock.sendall("USER %s\n" % user)
    while sock:
        # get input, send it to bot
        bot_input = ""
        while sock:
            line = readline(sock)
            print( line )
            if not line: # bad connection, keep on trying
                continue
            if line.find("eliminated") > -1:
                sock.close()  #bail out and hope for the next game
                sock=None
                break
            if line.startswith("INFO:"): # not meant for the bot
                continue
            bot_input += line + "\n"
            if line.startswith("end"):
                sock.close()
                sock=None
                break
            if line.startswith("ready"):
                break
            if line.startswith("go"):
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
            if answer.startswith("go"):	break
            client_mess += answer 
        
        # if there's no orders, send at least an empty line
        if (client_mess==""):
            client_mess="\r\n" 
        print( client_mess )

        sock.sendall( client_mess )
                
    try:
        bot.kill()
    except:
        pass

                      

def main():
    usage="""
        tcpclient.py   host_or_ip  port  botpath  player_nick  [num_rounds]
        
        if running on windows or if the botpath contains spaces,
        you have to wrap the botpath with "", eg.: "java /x/y/MyBot", "e:\\ai\\bots\\mybot.exe"
        
        player_nick may only contain ascii_letters, '_', and numbers
        
    """
    if len(sys.argv) < 5:
        print usage
        return
        
    host=sys.argv[1]
    port=int(sys.argv[2])
    botpath=sys.argv[3]
    pname=sys.argv[4]
    
    try:
        rounds = int(sys.argv[5])
    except:
        rounds = 1

    # json can't handle special chars, so weed that out before playing 2000 turns, and crashing then..
    for l in pname:
        if l in string.letters: continue
        if l in string.digits : continue
        if l =='_' : continue
        print( "your botname (" + pname + ") contains invalid characters, please choose another one!" )
        return
    
    for i in range(rounds):
        tcp(host, port, botpath, pname, {})
        
    #~ # keep konsole window open (for debugging)
    #~ sys.stdin.read()
    
if __name__ == "__main__":
    main()
