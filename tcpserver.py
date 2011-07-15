#!/usr/bin/env python

import select
import signal
import socket
import sys
import os
import logging
import json
import random
import threading
import trueskill

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
        
class TcpPlayer(object):
    def __init__( self, sock, address, name ):
        
        self.address = address
        self.sock = sock
        self.name = name
        self.id = 0
        self.game = None
        self.poll_string = None
        
    def __del__(self):
        #~ log.info( "rip, player " + self.name )
        try:
            self.sock.close()
        except:
            pass
                    
    def write(self,s):
        #~ log.info( self.name + "> " + s )
        try:
            self.sock.sendall(s)
        except:
            log.warning("invalid player socket! " + self.name)
            
    #~ def read(self):
        #~ return self.sock.recv(8012)
    def poll(self):
        return self.poll_string
    def clear(self):
        self.poll_string=None

    
class TcpGame(object):
    def __init__( self, db, opts, map_name, nplayers ):
        self.db = db
        self.id = db.latest
        self.opts = opts
        self.players = []
        self.bot_status = []
        self.ants = Ants(opts)
        self.map_name = map_name
        self.timestep = 0
        self.nplayers = nplayers
        
    #~ def __del__(self):
        #~ log.info( "rip, game   " + str(self.id) )
    
    def step( self ):
        t = time()
        timed_out = (t - self.timestep > self.opts['turntime']*0.001)
        
        inp_ok = 0
        for i,p in enumerate(self.players):
            if not self.ants.is_alive(i): continue
            if not p.sock: continue
            if p.poll(): inp_ok += 1
                
        if (inp_ok == len(self.players)) or timed_out:
            self.timestep = time()
            return self.do_turn()
            
        return True
        
    def turn(self):
        return "game " + str(self.id) + " turn " + str(self.ants.turn) + " : "
        
    def do_turn( self ):
        self.ants.start_turn()
        for i,p in enumerate(self.players):
            s = p.poll()
            #~ log.info( self.turn() + p.name + " : " + str(s) )
            p.clear()
            if not self.ants.is_alive(i): 
                if self.bot_status[i] != "eliminated":
                    log.debug( self.turn() + p.name + " got eliminated !")
                    p.write("INFO: "+p.name+" got eliminated !\n")
                self.bot_status[i] = "eliminated"
                continue
            if s == None:
                log.warning( self.turn() + p.name + " timed out !")
                if self.bot_status[i] != "timed out":
                    log.debug( self.turn() + p.name + " timed out !")
                self.bot_status[i] = "timed out"
                p.write("INFO: "+p.name+" timed out !\n")
                continue
                
            self.bot_status[i] = "survived"
                
            try:
                #~ valid, ignored, invalid = self.ants.do_moves(i, s.split('\r\n')) 
                # ;) Rabidus
                valid, ignored, invalid = self.ants.do_moves(i, s.replace('\r','\n').replace('\n\n','\n').split('\n')) 
            except:
                log.error("!!!!!!!! do_moves failed " + str(self.ants.turn) + " : " + str(p.name))
                
            if ignored:
                txt = " ignored: " + str(ignored) 
                p.write( "INFO: " + txt + '\n' )
                #~ log.debug(self.turn() +p.name +txt)
            if invalid:
                txt = " invalid: " + str(invalid) 
                p.write( "INFO: " + txt + '\n' )
                #~ log.debug( self.turn()  +p.name  + txt)
                
        try:
            self.ants.finish_turn()
        except:
            log.error("!!!!!!!! finish_turn failed "  + str(self.ants.turn) + " : " + str(self.id))
        
        # finished ?
        if ( self.ants.turn >= self.ants.turns) or ( self.ants.game_over() ):
            try:
                self.ants.finish_game()
                self.save_game()
            except:
                log.error(" !!!!!!!!!! finish game failed "  + str(self.ants.turn) + " : " + str(self.id) + " !!!!!!!!!!! ")
            return False # finished
        # alive
        else:           
            for i,p in enumerate(self.players):
                if self.ants.is_alive(i) and p.sock:
                    p.write( 'turn ' + str(self.ants.turn) + '\n' + self.ants.get_player_state(i) + "go\n" )
        return True

    def save_game(self):
        log.info("saving game : " + str(self.id) )
        scores = self.ants.get_scores()
        ranks = [sorted(set(scores), reverse=True).index(x) for x in scores]
        game_result = {
            'challenge': 'ants',
            'game_id': self.id,
            'status': self.bot_status,
            'score': scores,
            'rank': ranks,
            'replayformat': 'json',
            'replaydata': self.ants.get_replay(),
            'playernames': [],
        }
        for i,p in enumerate(self.players):
            game_result['playernames'].append(p.name)
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
        for i,p in enumerate(self.players):
            if p.name in self.db.players:
                player = self.db.players[p.name]
            else:
                player = PlayerData()
                player.name = p.name
                self.db.players[p.name] = player
            #~ player.games.append(g.id)
            player.ngames += 1
            plr[p.name] = scores[i]
        g.players = plr
        self.db.games[g.id] = g    

        # pop from list if there's too many games:
        if len(self.db.games) > int(self.opts['db_max_games']):
            k = self.db.games.keys().pop(0)
            del(self.db.games[k])
        
        log.info("db : " + str(len(self.db.games)) + " games")
        log.info("db : " + str(len(self.db.players)) + " players")
        
        # send final game info to players:
        end_line  = 'INFO: hope, you enjoyed game ' + str(self.id) + '.\n'
        end_line += 'INFO: players: '
        for i,p in enumerate(self.players):
            end_line += ' ' + p.name
        end_line += '\nINFO: scores :  %s\n' % ' '.join([str(s) for s in scores])
        end_line += 'end\n'
        
        for i,p in enumerate(self.players):
            try:
                p.write( end_line )
            except:
                continue
                
        self.calc_ranks( self.players, ranks )
        
        
    def calc_ranks( self, players, ranks ):
        class TrueSkillPlayer(object):
            def __init__(self, name, skill, rank):
                self.name = name
                self.old_skill = skill
                self.skill = skill
                self.rank = rank

        ts_players = []
        for i, p in enumerate(players):
            pdata = self.db.players[p.name]
            ts_players.append( TrueSkillPlayer(i, (pdata.mu,pdata.sigma), ranks[i] ) )
            
        trueskill.AdjustPlayers(ts_players)
        
        for i, p in enumerate(players):
            pdata = self.db.players[p.name]
            pdata.mu    = ts_players[i].skill[0]
            pdata.sigma = ts_players[i].skill[1]
            pdata.skill = pdata.mu - pdata.sigma * 3


class TCPGameServer(object):    
    def __init__(self, opts, game_db, port=1234, backlog=5):
        self.opts = opts
        self.db = game_db
        self.clients = []
        self.clientmap = {}
        self.games = {}
        
        # tcp binding options
        self.port = port
        self.backlog = backlog
        self.running = False
        self.force_shutdown = False
        
        self.bind()
        
    def bind(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('',self.port))
        log.info('Listening to port %d ...' % self.port)
        self.server.listen(self.backlog)
        
        
    def shutdown(self):
        log.info('Shutting down server...')
        # Close existing client sockets
        for o in self.clients:
            o.close()
        # Close the server
        self.server.close()


    def select_map(self):
        id = 1 + int(199 * random.random())
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
        log.info( "next game is " + str(self.db.latest) + " : " + map_name + " needs " + str(nplayers) + " players." )
        opts = self.opts
        opts['map'] = map_data
       
        return TcpGame( self.db, opts, map_name, nplayers )
                
                
    def start_game(self, game):
        log.info( "starting game " + str(game.id) + " : " + game.map_name )
        game.ants.start_game()
        game.timestep = time()
            
        # send info and turn 0    
        for i,p in enumerate(game.players):
            game.bot_status.append("survived")
            p.write( "INFO: you joined game " + str(game.id) + " on map " + str(game.map_name) + "\n" )
            plist = ""
            for j,q in enumerate(game.players):
                if j != i:
                    plist += " " + str(q.name)
            p.write( "INFO: your opponents are: " + plist + "\n" )
            p.write( game.ants.get_player_start(i) + 'ready\n' )
     
        # cache it
        self.games[game.id] = game
        

    def check_games(self):
        for k, g in self.games.iteritems():
            if not g.step():
                log.info("finished game " + str(k) )
                for i,p in enumerate(g.players):
                    self.kill_player( p.sock )
                break


    def kill_player(self, client):
        if client == None:
            return
            
        try: 
            client.close()
            self.clients.remove(client)
        except:
            log.warning( str(client) + "was already closed" )
            pass

        try:
            p = self.clientmap[client]
            p.sock = None
            del(self.clientmap[client])
        except:
            log.warning( str(client) + "wasn't in the clientmap" )
            pass
        try:
            if p.game == self.db.latest:
                g = self.next_game
            else:
                g = self.games[p.game]
        except:
            log.warning( str(p.name) + " had no game" )
            pass
            
        try:
            if g.ants.turn < 1:
                g.players.remove(p)
                return
        except:
            log.warning( str(p.name) + " could not be removed" )
            pass
        try:
            g.ants.kill_player(p.id)
            alive=0
            for i,p in enumerate(g.players):
                if g.ants.is_alive(i) and p.sock : alive += 1
            if alive == 0:
                del(self.games[g.id])
        except:
            log.warning( str(p.name) + " was already dead" )
            pass
            


    def serve(self):
        self.running = True
        last_update = time()

        # have to create the game before collecting respective num of players:
        self.next_game = self.create_game()
        
        # meet 'the select loop from hell'.
        while self.running or (len(self.clients) > 0 and not self.force_shutdown):
            if (time() - last_update) >= 10.0:
                log.info('%d connections, %d / %d idle, %d games' % (len(self.clients), len(self.next_game.players), self.next_game.nplayers, len(self.games)))
                last_update = time()
                
            self.check_games()
            
            try:
                inputready,outputready,exceptready = select.select([self.server] + self.clients, [], [], 0.1)
            except select.error, e:
                log.exception(e)
                break
            except socket.error, e:
                log.exception(e)
                break
                
            for s in inputready:
                
                if s == self.server:
                    # handle the server socket
                    client, address = self.server.accept()
                    if not client:
                        continue
                    try:
                        player_data = client.recv(4096).strip()
                        player_name = player_data.split()[1]
                        log.info('user %s connected: %d from %s' % (player_name,client.fileno(), address))
                        player = TcpPlayer( client, address, player_name )
                        player.id = len(self.next_game.players)
                        player.game = self.next_game.id
                        self.next_game.players.append( player )
                        player.write('INFO: hello ' + player.name + ', we still need ' +str(self.next_game.nplayers-len(self.next_game.players))+ ' more players for the upcoming game.\n')
                        self.clientmap[client] = player
                        self.clients.append(client)
                    except:
                        continue
                            
                    # start game if enough players joined
                    if len(self.next_game.players) == self.next_game.nplayers:
                        self.start_game(self.next_game)
                        # create next game 
                        self.next_game = self.create_game()
                    
                else:
                    # handle all other sockets
                    player = self.clientmap[s]
                    try:
                        data = s.recv(BUFSIZ)
                        player.poll_string = data
                                
                    except socket.error, e:
                        # Remove
                        log.warning('client socket error: %s' % e)
                        self.kill_player( s )
        self.shutdown()




#~ def main():
    #~ gid = 0
    #~ try: # to start numbering with the last game played
        #~ f = open( "games/last", 'r')
        #~ gid = int(f.read())
        #~ f.close()
    #~ except:
        #~ pass
        
    #~ tcp = TCPGameServer( game_id=gid-1 )

    #~ try:
        #~ tcp.serve()
    #~ except:
        #~ tcp.shutdown() # notify clients of our failure .
        #~ raise

#~ if __name__ == "__main__":
    #~ main()
