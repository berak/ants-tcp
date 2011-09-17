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
	def __init__(self, opts, db, port, game_data_lock, maps, radmin):
		threading.Thread.__init__(self)
		self.server = webserver.AntsHttpServer(('', port), webserver.AntsHttpHandler)
		self.server.db = db
		self.server.opts = opts
		self.server.maps = maps
		self.server.game_data_lock = game_data_lock
		self.server.radmin_page = radmin
		
	def run(self):
		self.server.serve_forever()



def main():
	
	web_port = 2080
	tcp_port = 2081
	
	# to change the opts below online from the webserver,
	#   set a secret admin url and access it like: /my_s3cr3t_adm1n?attack=focus
	#   or None to disable
	remote_admin = "rad_27d4"  # (no leading '/')

	# all opts in one dict, so we can show them on http
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
		
		## non-ants related tcp opts
		'trueskill': 'jskills',		# select trueskill implementation: 'py'(trueskill.py) or 'jskills'(java JSkills_0.9.0.jar) 
		'cp_separator': ';',	# if using java trueskill, you need to tell the separator for the classpath, its ';' for win and ':' for nix
		'db_max_games': 1000,	# how many game_infos should be kept in memory
		'multi_games': 'True',  # allow users to play multiple games at the same time
								# if set to False, players will have to wait until their latest game ended
		## web opts:
		'style': 'light',		# or 'dark'
		'sort': 'True',			# include tablesorter & jquery and have sortable tables(requires ~70kb additional download)
		
		## read only info
		'host': socket.gethostname(),
		'web_port':web_port,
		'tcp_port':tcp_port,
	}

	db  = game_db.load()
	maps = tcpserver.load_map_info()
	game_data_lock = threading.Lock()

	tcp = TcpThread( opts, db, tcp_port, game_data_lock, maps )	
	web = WebThread( opts, db, web_port, game_data_lock, maps, remote_admin )
	
	try:
		tcp.start()
		web.start()
	except:
		game_db.save( db )		
		raise

	
if __name__ == "__main__":
    main()

