#!/usr/bin/env python

import threading
import socket


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
		'turns':350,
		'loadtime': 3000, 
		'turntime': 2000,
		'viewradius2': 77,
		'spawnradius2': 1,
		'attackradius2': 5,
		'attack': 'power',
		'food': 'symmetric',
		# non-game args
		'db_max_games': 100, #how many games should be kept on the webserver
	}

	web_opts = {
		'style': 'light',
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

