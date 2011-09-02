#!/usr/bin/env python

import threading
import socket
import sys
import os


import tcpserver
import webserver
import game_db


class TcpThread(threading.Thread):
	def __init__(self, opts, db, port, game_data_lock, maps):
		threading.Thread.__init__(self)
		self.server = tcpserver.TCPGameServer( opts, db, port, game_data_lock, maps )

	def run(self):
		self.server.serve()


class WebThread(threading.Thread):
	def __init__(self, opts, db, port, game_data_lock, maps):
		threading.Thread.__init__(self)
		self.server = webserver.AntsHttpServer(('', port), webserver.AntsHttpHandler)
		self.server.db = db
		self.server.opts = opts
		self.server.maps = maps
		self.server.game_data_lock = game_data_lock
		self.server.radmin_page = "rad_27d4" # secret_url whithout leading /
		
	def run(self):
		self.server.serve_forever()



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
			maps[filename] = (p,r,c)
	return maps


def main():
	
	web_port = 2080
	tcp_port = 2081

	# all opts in one dict, so we can show them on http
	opts = {
		## tcp opts:
		'serial': False,
		'verbose': False,
		'turns':500,
		'loadtime': 5000, 
		'turntime': 5000,
		'viewradius2': 77,
		'attackradius2': 5,
		'spawnradius2': 1,
		'attack': 'focus',
		'food': 'symmetric',
		
		## non-ants related tcp opts
		'skill': 'jskills',		# select trueskill implementation: 'py'(trueskill.py) or 'jskills'(java JSkills_0.9.0.jar) 
		'cp_separator': ';',	# if using java trueskill, you need to tell the separator for the classpath, its ';' for win and ':' for nix
		'db_max_games': 100,	# how many games should be kept on the webserver
		'multi_games': True,    # allow users to play multiple games at the same time
								# if set to False, players will get rejected until their latest game ended
		## web opts:
		'style': 'light', # or 'dark'
		'host': socket.gethostname(),
		
		'wep_port':web_port,
		'tcp_port':tcp_port,
	}

	db  = game_db.load()
	maps = load_map_info()
	game_data_lock = threading.Lock()

	tcp = TcpThread( opts, db, tcp_port, game_data_lock, maps )	
	web = WebThread( opts, db, web_port, game_data_lock, maps )
	
	try:
		tcp.start()
		web.start()
	except:
		game_db.save( db )		
		raise
		
	
if __name__ == "__main__":
    main()

