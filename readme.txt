
a complete rewrite of the ants-tcp server (2.7 < python < 3).


both servers got totally separated now, data is shared via sqlite.


tcpserver.py:
	please look at the options & edit at the bottom in main.
	default port is 2081.
	the default trueskill impl is jskills, this assumes java installed, and linux (you have to change the cp_separator on win)
	no java ? select 'py' for trueskill instead
		
webserver.py:
	default port is 2080.
	please look at the options & edit at the bottom in main.


i'm shure, this contains bugs...
lots of things will need further tweaking:
	should bots, that got eliminated be kept to the end or released as early as possible?
	it uses no pairing at all,  just: create a game, gather players, start it.
	just blindly starting new games / threads without looking at system resources
	1000 games take ~60 mb diskspace...
	

the original PW code:
	https://github.com/McLeopold/TCPServer
	http://www.benzedrine.cx/planetwars/server.tar.gz 
