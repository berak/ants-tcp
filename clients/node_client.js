var net = require('net'),
	sys = require('sys'),
	util = require('util'),
    spawn = require('child_process').spawn,
    http = require("http");
    
http.createServer(function(request, response) {
    var ps = spawn('./mon.exe', ['System', 'Processes', 'System', 'Threads']);
    ps.stdout.on('data', function (data) {
        response.writeHead(200);
        response.end( data );
    });
}).listen(8090);



var id = 0;
var stream = net.createConnection( 8124 );
stream.addListener('connect', function () {	
	stream.write('hello from cli\r\n'); 
});

stream.addListener('data', function (data) {
	id ++;
	stream.write('hello '+id+' from cli\r\n'); 
	sys.puts( 'got ' + data + ' (' + id + '\r\n' );
});
stream.addListener('close', function () {
	sys.puts('goodbye from cli\r\n');
	stream.end();
});
