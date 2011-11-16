
the running ones i know of:
	http://ants.fluxid.pl    		// fluxid		(DE)
	http://tcpants.com       		// romans01		(US)
	http://ash.webfactional.com/	// ash0d		(US) calif.
	http://213.88.39.97:2080/		// accoun		(RU)


most of it is written in python, you'll need version >= 2.6 for this (fractions)
also you'll need php5.3 for the default trueskill impl, or java for the jskills version

you will need to start 
 * tcpserver.py (to run the games), as well as 
 * webserver.py (to show the results to the outer world).

people, who want to play a game here will need to download [your_webserver_url]/clients/tcpclient.py to proxy their bot-io to the tcpserver
(please also look at http://aichallenge.org/forums/viewtopic.php?f=25&t=1861 for delt0r's gui-bot_wrapper, which makes using this *even more fun*.)


feel free to edit/change anything you like, after all, it's YOU, who will be hosting that..
please fork it on github, to make it easy for me and others to pull in any good idea/change you have.


tcpserver.py:
	please look at the options & edit at the bottom in main.
	default port is 2081.
	about the trueskill impl:
		the most stable implementation is the php one. it needs php 5.3, though.
		this is choosen by default, now.
		as a fallback, the previous 'jskills' and 'py' impls are supplied here, too.
			(jskills has problems with draws, thus breaks sometimes)
			(trueskill.py has a bias problem, mu won't rise properly) 
		
webserver.py:
	default port is 2080.
	please look at the options & edit at the bottom in main.
	change the 'host' option to url of your website


sql.py:
	small sql admin shell to peek into the db, extract a replay, 
	reset the rankings, whatever.



problem/todo section:
	fluxid reported/(cursed) a lot of hanging threads, resulting in not freeing socket fds.
	hope that got fixed by adding a proper timeout on the accepted client socks, killing those zombies.
		please send an issue, if you still get this.

	you can't just force people playing constantly here, so the ranking 
	suffers from players playing a few good games and never return,
	fluctuations in the player skills present, and such.
	
	there's no pairing. just first comes, first served.
	
	

the previous PW code:
	https://github.com/McLeopold/TCPServer
	http://www.benzedrine.cx/planetwars/server.tar.gz 
