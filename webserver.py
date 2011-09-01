from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler 
import os
import re
import threading
import logging
import json
import random
import time
import SimpleHTTPServer

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)

# create logger
log = logging.getLogger('web')
log.setLevel(logging.DEBUG)
# add ch to logger
log.addHandler(ch)

style = {'light':"""
a{
	text-decoration: none;
	color:#666;
}
a:hover{
	color:#aaa;
}
body {
	font-family:Calibri,Helvetica,Arial;
	font-size:9pt;
	color:#111;
}
hr {
    color:#111;
    background-color:#555;    
}
table.tablesorter {
	background-color: #CDCDCD;
	font-family: Calibri,Helvetica,Arial;
	font-size: 8pt;
	margin: 10px 10px 15px 10px;
	text-align:left;
}
table.tablesorter thead tr th tfoot  {
	background-color:#E6EEEE;
	border:1px solid #FFFFFF;
	font-size:8pt;
	padding:4px 40px 4px 4px;
	background-position:right center;
	background-repeat:no-repeat;
	cursor:pointer;
}
table.tablesorter tbody td {
	background-color:#FFFFFF;
	color:#3D3D3D;
	padding:4px;
	vertical-align:top;
}
table.tablesorter tbody tr.odd td {
    background-color:#F0F0F6;
}
table.tablesorter thead tr .headerSortUp {
    background-image:url("asc.gif");
}
table.tablesorter thead tr .headerSortDown {
    background-image:url("desc.gif");
}
table.tablesorter thead tr .headerSortDown, table.tablesorter thead tr .headerSortUp {
    background-color:#8DBDD8;
}
""",
'dark':"""
body,iframe,textarea,input,button,file,.but{
	font-family: Arial, "MS Trebuchet", sans-serif;
	background-color: #292929; 
	color:#aaa;
	border-color:#404040;
}
a{
	text-decoration: none;
	color:#bbb;
}
a:hover{
	color:#ddd;
}

table.tablesorter thead th tr tfoot {
    text-align: left;
    background-color:#666666;
    border-color:#CCCCCC;
}
table.tablesorter tbody td tfoot {
    text-align: left;
    border: 1;
    border-color:#CCCCCC;
}
"""
}


class AntsHttpServer(HTTPServer):
    def __init__(self, *args):
        self.db = None
        self.opts = None
        HTTPServer.__init__(self, *args)

        
class AntsHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)
    
                
    def header(self, title):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        return """<html><head>
        <link rel="icon" href='/favicon.ico'>
        <title>"""  + title + """</title>
        <style>"""  + style[self.server.opts['style']] + """</style>
        </head><body>
        &nbsp;
        <a href='/' name=top> Latest Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking'> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/tcpclient.py' title='get the python client'> Client.py </a>
        <br><p>
        """
        
    def footer(self):
        #~ anum = int(1 + random.random() * 11)
        #~ apic = "<img src='/ants_pics/a"+str(anum)+".png' border=0>"
        apic="^^^"
        return "<p><br> &nbsp;<a href=#top title='crawl back to the top'> " + apic + "</a>"
        
    def serve_visualizer(self, match):
        junk,gid = match.group(0).split('.')
        rep_file = os.getcwd() + "/games/" + gid + ".replay"
        f = open(rep_file)
        replaydata = f.read()
        f.close()
        html = """
            <html>
            <head>
                <title>Ant Canvas</title>
                <script type="text/javascript" src="/js/visualizer.js"></script>	
                <script type="text/javascript">
                    window.isFullscreenSupported = function() {
                        return false;
                    };

                    function init() {
                        var visualizer = new Visualizer(document.body, '/data/');
                        visualizer.loadReplayData('"""+replaydata+"""');
                    }
                </script>
                <style type="text/css">
                    html { margin:0; padding:0; }
                    body { margin:0; padding:0; overflow:hidden; }
                </style>
            </head>
            <body>
               <script>init();</script>
            </body>
            </html>
            """
        self.wfile.write(html)

    def game_head(self):
        return """<table id='myTable' class='tablesorter' width='100%'>
            <thead><tr><th>Game </th><th>Players</th><th>Turns</th><th>Date</th><th>Map</th></tr></thead>"""
            
    def game_line(self, g):
        html = "<tr><td><a href='/replay." + str(g.id) + "' title='Run in Visualizer'> Replay " + str(g.id) + "</a></td><td>"
        for key, value in sorted(g.players.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            html += "&nbsp;&nbsp;<a href='/player/" + str(key) + "' title='"+str(value[1])+"'>"+str(key)+"</a> (" + str(value[0]) + ") &nbsp;"
        html += "</td><td>" + str(g.turns) + "</td>"
        html += "</td><td>" + str(g.date) + "</td>"
        html += "<td><a href='/map/" + str(g.map) + "' title='View the map'>" + str(g.map) + "</a></td>"
        html += "</tr>"
        return html
        
    def rank_head(self):
        return """<table id='plTable' class='tablesorter' width='100%'>
            <thead><tr><th>Player</th><th>Rank</th><th>Skill</th><th>Mu</th><th>Sigma</th><th>Games</th></tr></thead>"""
            
    def rank_line( self, p ):
        html  = "<tr><td><a href='/player/" + str(p.name) + "'>"+str(p.name)+"</a></td>" 
        html += "<td>" + str(p.rank) + "</td>"
        html += "<td>" + str(p.skill) + "</td>"
        html += "<td>" + str(p.mu)    + "</td>"
        html += "<td>" + str(p.sigma) + "</td>"
        #~ html += "<td>" + str(len(p.games)) + "</td>"
        html += "<td>" + str(p.ngames) + "</td>"
        html += "</tr>"
        return html
        
    def serve_main(self):
        html = self.header("latest games on " + str(self.server.opts['host']) )
        html += self.game_head()
        html += "<tbody>"
        self.server.game_data_lock.acquire()
        for k,g in sorted(self.server.db.games.iteritems(), reverse=True):
            html += self.game_line(g)
        self.server.game_data_lock.release()
        html += "</tbody></table>"
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)
        
    def serve_player(self, match):
        player = match.group(0).split("/")[2]
        log.info( "PLAYER : " + match.group(0) )
        html = self.header( player )
        html += self.rank_head()
        html += "<tbody>"
        self.server.game_data_lock.acquire()
        html += self.rank_line( self.server.db.players[player] )
        html += "</tbody></table>"
        html += self.game_head()
        html += "<tbody>"
        for k,g in sorted(self.server.db.games.iteritems(), reverse=True):
            if player in g.players:
                html += self.game_line(g)
        self.server.game_data_lock.release()
        html += "</tbody></table>"
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)

        
    def serve_settings(self, match):
        html = self.header("Settings")
        html += "<table>"
        for k,v in self.server.opts.iteritems():
            if k=='map': continue
            html += "<tr><td>%s</td><td>%s</td></tr>\n" % (k,v)
        html += "</table>"
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)
        
    def serve_ranking(self, match):
        html = self.header("Rankings")
        html += self.rank_head()
        html += "<tbody>"
        
        self.server.game_data_lock.acquire()
        pz = self.server.db.players.items()
        self.server.game_data_lock.release()
        
        def by_skill( a,b ):
            return cmp(b[1].skill, a[1].skill)            
        pz.sort(by_skill)        
        for n,p in pz:
            html += self.rank_line( p )
            
        html += "</tbody></table>"
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)
        
    def serve_map( self, match ):
        style = """
            <style>
                .A { border:0; background-color:#f0f; width:5; height:5; }
                .B { border:0; background-color:#f00; width:5; height:5; }
                .C { border:0; background-color:#0f0; width:5; height:5; }
                .D { border:0; background-color:#0ff; width:5; height:5; }
                .E { border:0; background-color:#ccc; width:5; height:5; }
                .F { border:0; background-color:#ff0; width:5; height:5; }
                .G { border:0; background-color:#22a; width:5; height:5; }
            </style>
            """
        mapname = match.group(0).split('/')[2]
        fname = os.getcwd() + "/maps/" + mapname 
        f = open(fname,"rb")
        m = f.read()
        f.close()
        result = self.header(mapname) + style + "<table border=0>\r\n"
        for line in m.split('\n'):
            line = line.strip().lower()
            if not line or line[0] == '#':
                continue
            key, value = line.split(' ')
            if key == 'm':
                result +="<tr>"
                for pix in value:
                    if pix=='a': c='A'
                    if pix=='b': c='B'
                    if pix=='c': c='C'
                    if pix=='d': c='D'
                    if pix=='.': c='E'
                    if pix=='*': c='F'
                    if pix=='%': c='G'
                    result +="<td class='"+c+"'/>"
                result +="<tr>"
        result += "</table>" + self.footer()
            
        self.wfile.write(result)
            
        

    def serve_file(self, match):
        mime = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','js':'text/javascript','py':'application/python'}
        junk,end = match.group(0).split('.')
        try:
            mime_type = mime[end]
        except:
            mime_type = 'text/plain'
        fname = os.getcwd() + match.group(0)
        f = open(fname,"rb")
        self.send_response(200)
        self.send_header('Content-type',mime_type)
        self.end_headers()
        self.wfile.write(f.read())
        f.close()
        
            
    def do_GET(self):
        log.info(self.path)

        if self.path == '/':
            self.serve_main()
            return
            
        for regex, func in (
                ('^\/settings', self.serve_settings),
                ('^\/ranking', self.serve_ranking),
                ('^\/map/(.*)', self.serve_map),
                ('^\/player\/(.*)', self.serve_player),
                ('^\/replay\.([0-9]+)', self.serve_visualizer),
                ('^\/?(.*)', self.serve_file),
                ):
            match = re.search(regex, self.path)
            if match:
                func(match)
                return
        self.send_error(404, 'File Not Found: %s' % self.path)




 
