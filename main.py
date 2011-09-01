#!/usr/bin/env python

import threading
import socket
import sys


import tcpserver
import webserver
import game_db


class TcpThread(threading.Thread):
	def __init__(self, opts, db, port, game_data_lock):
		threading.Thread.__init__(self)
		self.server = tcpserver.TCPGameServer( opts, db, port, game_data_lock )

	def run(self):
		self.server.serve()


class WebThread(threading.Thread):
	def __init__(self, opts, db, port, game_data_lock):
		threading.Thread.__init__(self)
		self.server = webserver.AntsHttpServer(('', port), webserver.AntsHttpHandler)
		self.server.db = db
		self.server.opts = opts
		self.server.game_data_lock = game_data_lock
		
	def run(self):
		self.server.serve_forever()


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
		
		## web opts:
		'style': 'light', # or 'dark'
		'host': socket.gethostname(),
		
		'wep_port':web_port,
		'tcp_port':tcp_port,
	}
	
	db  = game_db.load()
	game_data_lock = threading.Lock()

	tcp = TcpThread( opts, db, tcp_port, game_data_lock )	
	web = WebThread( opts, db, web_port, game_data_lock )
	
	try:
		tcp.start()
		web.start()
	except:
		game_db.save( db )		
		raise
		
	
if __name__ == "__main__":
    main()

