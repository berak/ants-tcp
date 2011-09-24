#!/usr/bin/env python

import select
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

from math import ceil, sqrt
from time import time,sleep
import json

from time import time,asctime
import datetime

from ants import Ants
from engine import run_game

import game_db


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


BUFSIZ = 4096



## ugly global, but the last thing you'll want here are circular refs! 
class Bookkeeper:
    players=set()
    games=set()

book = Bookkeeper()


def load_map_info():
	maps={}
	for root,dirs,filenames in os.walk("maps"):
		for filename in filenames:
			mf = open("maps/"+filename,"r")
			for line in mf:
				if line.startswith('players'):	p = int(line.split()[1])
				if line.startswith('rows'):		r = int(line.split()[1])
				if line.startswith('cols'):		c = int(line.split()[1])
			mf.close()
			maps[filename] = [p,r,c,0]
	return maps




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
        self.start()
        
    def __del__(self):
        #~ print "__del__", self.game_id, self.name, self
        try:
            book.players.remove( self.name )
        except: pass            
        self._close()
                
    def run( self ):
        while self.sock:
            line=""
            while(self.sock):
                try:
                    c = self.sock.recv(1)
                except Exception, e:
                    self._close()
                    break                
                if ( not c ):
                    break
                elif ( c=='\r' ):
                    continue
                elif ( c=='\n' ):
                    break
                else:
                    line += c
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
        try: 
            ## you died of dysentry
            self.write("end\nyou timed out.\n\n")
        except: pass
            
        self._close()
        

    def write(self, str):
        try:
            self.sock.sendall(str)
        except Exception, e:
            #~ log.warning("writing to invalid socket %s  game:%d [%s]" % (self.name,self.game_id,str.replace('\n','')) )
            pass

    def write_line(self, line):
        return self.write(line + "\n")

    def read_line(self, timeout=0):
        if (len(self.inp_lines) == 0) or (not self.sock):
            return None
        line = self.inp_lines[0]
        self.inp_lines = self.inp_lines[1:]
        return line


    ## dummies
    def release(self):
        self._close()
        
    def pause(self):
        pass

    def resume(self):
        pass
        
    def read_error(self, timeout=0):
        return None
        
    ## never used
    #~ def retrieve(self):
        #~ print "Thread ertriev", self
        #~ pass



    
class TcpGame(threading.Thread):
    def __init__( self, id, opts, map_name, nplayers ):
        threading.Thread.__init__(self)
        self.id = id
        self.opts = opts
        self.players = []
        self.bot_status = []
        self.map_name = map_name
        self.nplayers = nplayers
        self.bots=[]
        self.ants = Ants(opts)
        
    def __del__(self):
        #~ print "__del__", self.id, self       
        try:
            book.games.remove(self.id)
        except: pass            
        for b in self.bots:
            b.kill()
            

    def run(self):
        starttime = time()
        log.info( "run game %d %s %s" % (self.id,self.map_name,self.players) )
        for i,p in enumerate(self.bots):
            p.write( "INFO: game " + str(self.id) + " " + str(self.map_name) + " : " + str(self.players) + "\n" )
        
        # finally, THE GAME !
        game_result = run_game(self.ants, self.bots, self.opts)
        
        #~ log.info("saving game : " + str(self.id) + " turn " + str(self.ants.turn) )
        try:
            states = game_result["status"]
        except: # keyerror
            log.error("broken game %d: %s" % (self.id,game_result) )
            return
            
        scores = self.ants.get_scores()
        ranks = [sorted(scores, reverse=True).index(x) for x in scores]

        # count draws
        draws = 0
        hist = [0]*len(ranks)
        for r in ranks:
            hist[r] += 1
        for h in hist:
            if h:  draws += (h-1)
            
        # save replay, add playernames to it
        game_result['playernames'] = []
        for i,p in enumerate(self.players):
            game_result['playernames'].append(p)
        rep_name = "games/"+ str(self.id)+".replay"
        f = open( rep_name, 'w' )
        json.dump(game_result,f)
        f.close()
        
        self.db = game_db.GameDB()
        plr = {}
        for i,p in enumerate(self.players):
            plr[p] = (scores[i], states[i])
            self.db.update("insert into gameindex values(?,?,?)",(None,p,self.id))
        self.db.add_game( self.id, self.map_name, self.ants.turn, draws,json.dumps(plr) )
                
        # update trueskill
        if sum(ranks) >= len(ranks)-1:
            if self.opts['trueskill'] == 'jskills':
                self.calk_ranks_js( self.players, ranks )
            else : # default
                self.calc_ranks_py( self.players, ranks )
        else:
            log.error( "game "+str(self.id)+" : ranking unsuitable for trueskill " + str(ranks) )            

        #~ # update rankings
        for i, p in enumerate(self.db.retrieve("select name from players order by skill desc",())):
            self.db.update_player_rank( p[0], i+1 )


        # dbg display
        ds = time() - starttime
        mins = int(ds / 60)
        secs = ds - mins*60
        log.info("saved game %d : %d turns %dm %2.2fs" % (self.id,self.ants.turn,mins,secs) )
        log.info("players: %s" % self.players)
        log.info("ranks  : %s   %s draws" % (ranks, draws) )
        log.info("scores : %s" % scores)
            
        
        
   
    def calc_ranks_py( self, players, ranks ):
        class TrueSkillPlayer(object):
            def __init__(self, name, skill, rank):
                self.name = name
                self.old_skill = skill
                self.skill = skill
                self.rank = rank

        ts_players = []
        for i, p in enumerate(players):
            pdata = self.db.get_player((p,))
            ts_players.append( TrueSkillPlayer(i, (pdata[0][6],pdata[0][7]), ranks[i] ) )
        
        try:
            trueskill.AdjustPlayers(ts_players)
        except Exception, e:
            log.error(e)
            return
        
        for i, p in enumerate(players):
            mu    = ts_players[i].skill[0]
            sigma = ts_players[i].skill[1]
            skill = mu - sigma * 3
            self.db.update_player_skill(p, skill, mu,sigma ); 
            

    def calk_ranks_js( self, players, ranks ):
        ## java needs ';' as separator for win23, ':' for nix&mac
        classpath = "jskills/JSkills_0.9.0.jar"+self.opts['cp_separator']+"jskills"
        tsupdater = subprocess.Popen(["java", "-cp", classpath, "TSUpdate"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                
        lines = []
        for i,p in enumerate(players):
            pdata = self.db.get_player((p,))
            lines.append("P %s %d %f %f\n" % (p, ranks[i], pdata[0][6], pdata[0][7]))
        
        for i,p in enumerate(players):
            tsupdater.stdin.write(lines[i])
        
        tsupdater.stdin.write("C\n")
        tsupdater.stdin.flush()
        tsupdater.wait()
        
        for i,p in enumerate(players):
            # this might seem like a fragile way to handle the output of TSUpdate
            # but it is meant as a double check that we are getting good and
            # complete data back
            result =  tsupdater.stdout.readline().split() 
            if len(result)<3:
                log.error("invalid jskill result " + str(result))
                return
            
            if str(p) != result[0]:
                log.error("Unexpected player name in TSUpdate result. %s != %s" % (player, result[0]))
                break
            ## hmm, java returns floats formatted like: 1,03 here, due to my locale(german) ?
            mu    = float(result[1].replace(",","."))
            sigma = float(result[2].replace(",","."))
            skill = mu -sigma * 3
            self.db.update_player_skill( p, skill, mu, sigma )



class TCPGameServer(object):        
    def __init__(self, opts, port, maps):
        self.opts = opts
        self.maps = maps

        # tcp binding options
        self.port = port
        self.backlog = 5
        
        self.bind()

    def addplayer(self, game, name, password, sock):
        p = self.db.get_player((name,))
        if len(p)==1:
            pw = p[0][2]
            if pw != password:
                log.warning("invalid password for %s : %s : %s" % (name, pw, password) )
                sock.sendall("INFO: invalid password for %s : %s\n"% (name, password) )
                sock.sendall("end\ngo\n")
                sock.close()
                return -1
        else:
            self.db.add_player(name, password)
            
        box = TcpBox(sock)
        box.name=name
        box.game_id = game.id
        game.bots.append( box )
        game.players.append(name)
        book.players.add(name)
        return len(game.bots)
        
                
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
        ## try to find a map that does not need more players than available
        max_players = len(book.players)/2
        if max_players < 2:
            max_players = 2
        base_name = random.choice( self.maps.keys() )
        #~ while( self.maps[base_name][0] < 4 ):
        while( self.maps[base_name][0] > max_players ):
            base_name = random.choice( self.maps.keys() )
        self.maps[base_name][3] += 1
        
        map_name = os.path.join( 'maps', base_name )
        data = ""
        f = open(map_name, 'r')
        for line in f:
            data += line
            if line.startswith('players'):
                nplayers = line.split()[1]
        f.close()
        return base_name, data, int(nplayers)
        
    
    def create_game(self):
        # get a map and create antsgame
        self.latest += 1
        map_name, map_data, nplayers = self.select_map()
        opts = self.opts
        opts['map'] = map_data
       
        log.info( "game %d %s needs %d players" %(self.latest,map_name,nplayers) )
        g = TcpGame( self.latest, opts, map_name, nplayers)
        book.games.add(g.id)
        return g


    def reject_client(self,client, message,dolog=True):
        try:
            if dolog:
                log.info(message)
            client.sendall("INFO: " + message + "\nend\ngo\n")
            client.close()
            client = None
        except:
            pass
            
                
    
    def serve(self):
        # have to create the game before collecting respective num of players:
        self.db = game_db.GameDB()
        self.latest = int(self.db.retrieve("select count(*) from games",())[0][0])
        self.next_game = self.create_game()
        t = 0
        while self.server:
            try:
                inputready,outputready,exceptready = select.select([self.server], [], [], 0.1)
            except select.error, e:
                log.exception(e)
                break
            except socket.error, e:
                log.exception(e)
                break

            for s in inputready:
                if s == self.server:
                    client, address = self.server.accept()
                    data = client.recv(4096).strip()
                    data = data.split(" ")
                    name = data[1]
                    password = data[2]
                    name_ok = True
                    for bw in ["shit","porn","pr0n","pron","dick","tits","hitler","fuck","gay","cunt","asshole"]:
                        if name.find(bw) > -1:
                            self.reject_client(client, "can you think of another name than '%s', please ?" % name )
                            name_ok = False
                            break
                    if not name_ok:
                        continue
                    # if in 'single game per player(name)' mode, just reject the connection here..
                    if (name in book.players) and (str(self.opts['multi_games'])=="False"):
                        self.reject_client(client, "%s is already running a game." % name, False )
                        continue
                    # already in next_game ?
                    if name in self.next_game.players:                        
                        self.reject_client(client, '%s is already queued for game %d' % (name, self.next_game.id), False )
                        continue
                        
                    # start game if enough players joined
                    avail = self.addplayer( self.next_game, name, password, client )
                    if avail==-1:
                        continue
                    log.info('user %s connected to game %d (%d/%d)' % (name,self.next_game.id,avail,self.next_game.nplayers))
                    if avail == self.next_game.nplayers:
                        game = self.next_game
                        game.start()
                        game = None

                        self.next_game = self.create_game()
                        
            # remove bots from next_game that died between connect and the start of the game
            for i, b in enumerate(self.next_game.bots):
                if (not b.sock) or (not b.is_alive):
                    log.info( "removed %s from next_game:%d" % (b.name, self.next_game.id) )
                    del( self.next_game.bots[i] )
                    del( self.next_game.players[i] )
                    
            if t % 100 == 1:
                log.info("%d games, %d players online." % (len(book.games),len(book.players)) )
            t += 1
            sleep(0.005)
                
        self.shutdown()





def main():

    tcp_port = 2081

    opts = {
        ## tcp opts:
        'turns':750,
        'loadtime': 5000, 
        'turntime': 5000,
        'viewradius2': 77,
        'attackradius2': 5,
        'spawnradius2': 1,
        'attack': 'focus',
        'food': 'symmetric',
        'food_rate': (1,8), # total food
        'food_turn': (12,30), # per turn
        'food_start': (75,175), # per land area
        'food_visible': (2,4), # in starting loc
        'cutoff_percent': 0.66,
        'cutoff_turn': 150,
        'kill_points': 2,
        
        ## non-ants related tcp opts
        'trueskill': 'jskills',	# select trueskill implementation: 'py'(trueskill.py) or 'jskills'(java JSkills_0.9.0.jar) 
        'cp_separator': ':',	# if using java trueskill, you need to tell the separator for the classpath, its ';' for win and ':' for nix
        'db_max_games': 1000,	# how many game_infos should be kept in memory
        'multi_games': 'True',  # allow users to play multiple games at the same time
                                # if set to False, players will have to wait until their latest game ended
    }
    maps = load_map_info()
    tcp = TCPGameServer( opts, tcp_port, maps )
    tcp.serve()

	
if __name__ == "__main__":
    main()

