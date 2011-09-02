
a complete rewrite of the ants-tcp server (2.7 < python < 3).

this time i hacked engine.py to take a list of tcp-sandboxes,
	needs multithreading now, but has much better and faster gameplay that way.
	.. take it with a grain of salt ..

start it by (editing and) running main.py


the default trueskill impl is trueskill.py, 
if you also got java installed, you'll want to use jskills.

i'm shure, this contains bugs...
lots of things will need further tweaking:
	should bots, that got eliminated be kept to the end or released as early as possible?
	it uses no pairing at all,  just: create a game, gather players, start it.
	just blindly starting new games / threads without looking at system resources
	
finally, this was the original PW code:
	'https://github.com/McLeopold/TCPServer', 
	*link to dhartmei's c-src
