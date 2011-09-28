
a complete rewrite of the ants-tcp server (2.6 < python < 3).


both servers got separated now, data is shared via sqlite.


tcpserver.py:
	please look at the options & edit at the bottom in main.
	default port is 2081.
	the default trueskill impl is jskills, this assumes java installed
	no java ? select 'py' for trueskill instead
		
webserver.py:
	default port is 2080.
	please look at the options & edit at the bottom in main.


sql.py:
	small sql shell to peek into the db, or do remote changes


	

the original PW code:
	https://github.com/McLeopold/TCPServer
	http://www.benzedrine.cx/planetwars/server.tar.gz 
