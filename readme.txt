
the running ones i know of:
	http://ants.fluxid.pl    		// fluxid		(DE)
	http://tcpants.com       		// romans01		(US)
	http://ash.webfactional.com/	// ash0d		(US) calif.
	http://213.88.39.97:2080/		// accoun		(RU)



you will need to start 
 * tcpserver.py (to run the games), as well as 
 * webserver.py (to show the results to the outer world).

people, who want to play a game here will need to download [your_webserver_url]/clients/tcpclient.py to proxy their bot-io to the tcpserver
(please also look at http://www.mabs.at/ewing/AntWatcher2000.jar for delt0r's gui-bot_wrapper, which makes using this *even more fun*.)


feel free to edit/change anything you like, after all, it's YOU, who will be hosting that, (not me ;)
please fork it on github, to make it easy for me to pull in any good idea/change you have.


tcpserver.py:
	please look at the options & edit at the bottom in main.
	default port is 2081.
	about the trueskill impl:
		the default is 'jskills', this assumes java installed. (breaks sometimes, but more accurate than the py version)
		(the contest currently runs the moserware-php version, not included here. things to come.)
		
webserver.py:
	default port is 2080.
	please look at the options & edit at the bottom in main.
	change the 'host' option to url of your website


sql.py:
	small sql admin shell to peek into the db, extract a replay, reset the rankings, whatever.




the original PW code:
	https://github.com/McLeopold/TCPServer
	http://www.benzedrine.cx/planetwars/server.tar.gz 
