#!/usr/bin/env python

#~ import select
#~ import signal
import socket
import sys
import os
import logging
import json
import random
import threading
import trueskill
import subprocess

from time import time,asctime

from ants import Ants

import game_db
from game_db import GameData, PlayerData, GameDB

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('tcp')
log.setLevel(logging.INFO)
# add ch to logger
log.addHandler(ch)

gamelog = logging.getLogger('game')
gamelog.setLevel(logging.DEBUG)
gamelog.addHandler(ch)

gamedatalog = logging.getLogger('gamedata')
gamedatalog.setLevel(logging.DEBUG)
gamedatalog.addHandler(ch)


BUFSIZ = 4096

from math import ceil, sqrt
from time import time
import json
import logging

log = logging.getLogger("game.Ants")

#
## sandbox impl
#
class TcpBox(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.inp_lines = []
        
        #dbg stuff
        self.name =""
        self.game_id=0
        
        # start thread
        #~ threading.Thread.start(self)
        self.start()
        
    def __del__(self):
        #~ print "__del__", self
        self._close()
        
    def _readline(self):
        s=""
        while(self.sock):
            try:
                c = self.sock.recv(1)
            except Exception, e:
                #~ print e
                break                
            if ( not c ):
                break
            elif ( c=='\r' ):
                continue
            elif ( c=='\n' ):
                break
            else:
                s += c
        return s
        
    def run( self ):
        while self.sock:
            line = self._readline() 
            ## an invalid line here can be the end of a message or the death of the other end. don't bailout, since we can't decide 
            if line:
                self.inp_lines.append(line)

    ## next 2 are commented out to avoid interference with the thread interface
    #~ @property
    #~ def is_alive(self):
        #~ return self.sock != None

    #~ def start(self, shell_command):
        #~ print "Thread start", self
        #~ pass
        
    def _close(self):
        try:
            self.sock.close()
        except: pass
        self.sock = None
        
    def kill(self):
        #~ print "Thread kill", self, self.sock
        try: 
            ## you died of dysentry
            self.write("end\nyou timed out.\n\n")
        except: pass
            
        self._close()
        

    def write(self, str):
        #~ print "Thread write", self,str
        if self.sock == None:
            log.warning("writing to invalid socket %s  game:%d" % (self.name,self.game_id) )
            return False
        self.sock.sendall(str)

    def write_line(self, line):
        #~ print "Thread write_line", self, line
        return self.write(line + "\n")

    def read_line(self, timeout=0):
        if (len(self.inp_lines) == 0) or (not self.sock):
            return None
        line = self.inp_lines[0]
        self.inp_lines = self.inp_lines[1:]
        return line


    ## dummies
    def release(self):
        #~ print "Thread release", self
        self._close()
        
    def pause(self):
        #~ print "Thread pause", self
        pass

    def resume(self):
        #~ print "Thread resume", self
        pass
        
    def read_error(self, timeout=0):
        return None
        
    ## never used
    #~ def retrieve(self):
        #~ print "Thread ertriev", self
        #~ pass


from engine import run_game

    
class TcpGame(threading.Thread):
    def __init__( self, db, opts, map_name, nplayers ):
        threading.Thread.__init__(self)
        self.db = db
        self.id = db.latest
        self.opts = opts
        self.players = []
        self.bot_status = []
        self.map_name = map_name
        self.nplayers = nplayers
        self.bots=[]
        self.ants = Ants(opts)
        
    def addplayer(self, name,sock):
        self.players.append(name)
        box = TcpBox(sock)
        box.name=name
        box.game_id = self.id
        self.bots.append( box )
        return len(self.bots)

    def run(self):
        log.info( "run game %d %s %s" %(self.id,self.map_name,self.players) )
        for i,p in enumerate(self.bots):
            p.write( "INFO: game " + str(self.id) + " on map " + str(self.map_name) + " : " + str(self.players) + "\n" )
            #~ plist = ""
            #~ for j,q in enumerate(self.players):
                #~ if j != i:
                    #~ plist += " " + q
            #~ p.write( "INFO: your opponents are: " + plist + "\n" )
        
        # finally, THE GAME !
        game_result = run_game(self.ants, self.bots, self.opts)
        
        log.info("saving game : " + str(self.id) + " turn " + str(self.ants.turn) )
        scores = self.ants.get_scores()
        ranks = [sorted(set(scores), reverse=True).index(x) for x in scores]
        game_result['playernames'] = []
        for i,p in enumerate(self.players):
            game_result['playernames'].append(p)
        rep_name = "games/"+ str(self.id)+".replay"
        f = open( rep_name, 'w' )
        json.dump(game_result,f)
        f.close()
        
        # add to game db data shared with the webserver
        g = GameData()
        g.id = self.id
        g.map = self.map_name
        g.date = asctime()
        plr = {}
        states = game_result["status"]
        for i,p in enumerate(self.players):
            if p in self.db.players:
                player = self.db.players[p]
            else:
                player = PlayerData()
                player.name = p
                self.db.players[p] = player
            player.ngames += 1
            plr[p] = (scores[i], states[i])
        g.players = plr
        self.db.games[g.id] = g    

        # pop from list if there's too many games:
        if len(self.db.games) > int(self.opts['db_max_games']):
            k = self.db.games.keys().pop(0)
            del(self.db.games[k])

        # update rankings
        if self.opts['skill'] == 'jskills':
            self.calk_ranks_js( self.players, ranks )
        else : # default
            self.calc_ranks_py( self.players, ranks )
            
        
        
   
    def calc_ranks_py( self, players, ranks ):
        class TrueSkillPlayer(object):
            def __init__(self, name, skill, rank):
                self.name = name
                self.old_skill = skill
                self.skill = skill
                self.rank = rank

        ts_players = []
        for i, p in enumerate(players):
            pdata = self.db.players[p]
            ts_players.append( TrueSkillPlayer(i, (pdata.mu,pdata.sigma), ranks[i] ) )
            
        trueskill.AdjustPlayers(ts_players)
        
        for i, p in enumerate(players):
            pdata = self.db.players[p]
            pdata.mu    = ts_players[i].skill[0]
            pdata.sigma = ts_players[i].skill[1]
            pdata.skill = pdata.mu - pdata.sigma * 3


    def calk_ranks_js( self, players, ranks ):
        #~ classpath = "{0}/JSkills_0.9.0.jar:{0}".format(
                #~ os.path.join(os.path.dirname(os.path.realpath(__file__)),
                    #~ "jskills"))
        classpath = "jskills/JSkills_0.9.0.jar"+self.opts['cp_separator']+"jskills"
        tsupdater = subprocess.Popen(["java", "-cp", classpath, "TSUpdate"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for i,p in enumerate(players):
            pdata = self.db.players[p]
            tsupdater.stdin.write("P %s %d %f %f\n" % (p, ranks[i], pdata.mu, pdata.sigma))
        tsupdater.stdin.write("C\n")
        tsupdater.stdin.flush()
        tsupdater.wait()
        for player in players:
            # this might seem like a fragile way to handle the output of TSUpdate
            # but it is meant as a double check that we are getting good and
            # complete data back
            result = tsupdater.stdout.readline().split()
            if str(player) != result[0]:
                log.error("Unexpected player name in TSUpdate result. %s != %s"
                        % (player, result[0]))
                return False
            pdata = self.db.players[player]
            pdata.mu    = float(result[1].replace(",","."))
            pdata.sigma = float(result[2].replace(",","."))
            pdata.skill = pdata.mu - pdata.sigma * 3

class TCPGameServer(object):        
    def __init__(self, opts, game_db, port=1234, backlog=5):
        self.opts = opts
        self.db = game_db
        self.clients = []
        
        # tcp binding options
        self.port = port
        self.backlog = backlog
        
        self.bind()
        
    def bind(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('',self.port))
        log.info('Listening to port %d ...' % self.port)
        self.server.listen(self.backlog)
        
        
    def shutdown(self):
        log.info('Shutting down server...')
        self.server.close()
        self.server=None

    def select_map(self):
        id = 1 + int(11 * random.random())
        base_name = 'symmetric_'+str(id)+'.map'
        map_name = os.path.join( 'maps', 'symmetric_maps', base_name)
        data = ""
        f = open(map_name, 'r')
        for line in f:
            data += line
            if line.startswith('players'):
                nplayers = line.split()[1]
        f.close()
        return base_name, data, int(nplayers)
        
    
    def create_game(self):
        # we might crash..
        if self.db.latest % 10 == 1:
            game_db.save(self.db)
            
        # play it again, sam.
        self.db.latest += 1
        
        # get a map and create antsgame
        map_name, map_data, nplayers = self.select_map()
        opts = self.opts
        opts['map'] = map_data
       
        log.info( "game %d %s needs %d players" %(self.db.latest,map_name,nplayers) )
        return TcpGame( self.db, opts, map_name, nplayers )
                
                
    def serve(self):

        # have to create the game before collecting respective num of players:
        self.next_game = self.create_game()
        
        while self.server:
            client, address = self.server.accept()
            data = client.recv(4096).strip()
            name = data.split()[1]
            log.info('user %s connected: %d to game %d' % (name,client.fileno(),self.next_game.id))
            # start game if enough players joined
            if self.next_game.addplayer( name, client ) == self.next_game.nplayers:
                game = self.next_game
                game.start()

                self.next_game = self.create_game()
                
        self.shutdown()
