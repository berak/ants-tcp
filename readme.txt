
a complete rewrite of the ants-tcp server (in python).

this time it's creating a list of tcp-sandboxes and passes that to (hacked) engine.py


start it by (editing and) running main.py

current ports are:
	web_port = 2080
	tcp_port = 2081
	
	remember to adjust your firewall.


the default trueskill impl is trueskill.py, 
if you got java installed, you'll want to use jskills.

lots of things will need further tweaking:
	should bots, that got eliminated/timeout be kept to the end or released as early as possible?
	currently, it uses no pairing at all,  just: create a game, gather players, start it.
	zillions of threads, and not  a *single* lock ...
	mcleo's source had a nice webcache for the http part


this was the original PW code:
	'https://github.com/McLeopold/TCPServer', 
	*link to dhartmei's c-src
