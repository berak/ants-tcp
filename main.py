#!/usr/bin/env python

import threading
import socket
import sys


import tcpserver
import webserver
import game_db


class TcpThread(threading.Thread):
	def __init__(self, opts, db, port):
		threading.Thread.__init__(self)
		self.server = tcpserver.TCPGameServer( opts, db, port )

	def run(self):
		self.server.serve()

class WebThread(threading.Thread):
	def __init__(self, opts, db, port):
		threading.Thread.__init__(self)
		self.server = webserver.AntsGameServer(('', port), webserver.AntsGameHandler)
		self.server.db = db
		self.server.opts = opts
		
	def run(self):
		self.server.serve_forever()


def main():
	
	web_port = 2080
	tcp_port = 2081

	tcp_opts = {
		#~ 'verbose_log': sys.stderr,
		'serial': False,
		'verbose': False,
		'turns':350,
		'loadtime': 5000, 
		'turntime': 5000,
		'viewradius2': 77,
		'attackradius2': 5,
		'spawnradius2': 1,
		'attack': 'focus',
		'food': 'symmetric',
		
		# non-ants args
		'skill': 'jskills',		# select trueskill implementation: 'py'(trueskill.py) or 'jskills'(java JSkills_0.9.0.jar) 
		'cp_separator': ';',	# if using java trueskill, you need to tell the separator for the classpath, its ';' for win and ':' for nix
		'db_max_games': 100,	# how many games should be kept on the webserver
	}

	web_opts = {
		'style': 'light', # or 'dark'
		'host': socket.gethostname(),
	}
	
	db  = game_db.load()
	tcp = TcpThread( tcp_opts, db, tcp_port )	
	web = WebThread( web_opts, db, web_port )
	
	try:
		tcp.start()
		web.start()
	except:
		game_db.save( db )		
		raise
		
	
if __name__ == "__main__":
    main()

