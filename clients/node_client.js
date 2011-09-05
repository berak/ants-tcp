var net = require('net'),
	sys = require('sys'),
	util = require('util'),
    spawn = require('child_process').spawn,
    http = require("http");
    


var botpath = "mybot.exe"
var botname = "lala"
var password = "letmein"
var bot = null;

var tcp = net.createConnection( 2081 );

tcp.addListener('connect', function () {	
	tcp.write('USER '+botname+' '+password+'\n'); 
    bot = spawn(botpath);
    bot.stdout.on('data', function (data) {
        stream.write(data);
    });
});
tcp.addListener('data', function (data) {
	if ( data.startsWith("INFO:") ) {
		sys.puts( data );
	} else {
		bot.stdin.write(data); 
	}
});
tcp.addListener('close', function () {
	// kill the bot
	tcp.end();
});
