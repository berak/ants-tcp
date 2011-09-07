from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler 
import os
import re
import threading
import logging
import json
import random
import time
import SimpleHTTPServer

from tcpserver import book

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
    background-color:#AAB;
}
table.tablesorter thead tr .headerSortDown {
    background-color:#BBC;
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
}
table.tablesorter tbody td tfoot {
    text-align: left;
    border: 1;
    font-size: 9;
}
"""
}

table_lines = 100

class AntsHttpServer(HTTPServer):
    def __init__(self, *args):
        self.db = None
        self.opts = None
        self.maps = None
        self.cache = {}
        HTTPServer.__init__(self, *args)
        
        
class AntsHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)
        
    def log_message(self,format,*args):
        pass
    
                
    def send_head(self, type='text/html'):
        self.send_response(200)
        self.send_header('Content-type',type)
        self.end_headers()
        
    def header(self, title):
        self.send_head()
        
        head = """<html><head>
        <link rel="icon" href='/favicon.ico'>
        <title>"""  + title + """</title>
        <style>"""  + style[self.server.opts['style']] + """</style>"""
        if str(self.server.opts['sort'])=='True':
            head += """
                <script type="text/javascript" src="/js/jquery-1.2.6.min.js"></script> 
                <script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script>
                """
        head += """</head><body><b> &nbsp;&nbsp;&nbsp;
        <a href='/' name=top> Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking'> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/settings'> Settings </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/maps'> Maps </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/clients/tcpclient.py' title='get the python client'> Client.py </a>
        <br><p></b>
        """
        return head
    
    
    def footer_sort(self, id):
        if str(self.server.opts['sort'])=='True':
            return """
                <script>
                $(document).ready(function() { $("#%s").tablesorter(); }); 
                </script>
            """ % id
        return ""
    
    def footer(self):
        #~ anum = int(1 + random.random() * 11)
        #~ apic = "<img src='/ants_pics/a"+str(anum)+".png' border=0>"
        apic="^^^"
        return "<p><br> &nbsp;<a href=#top title='crawl back to the top'> " + apic + "</a>"
    
    
    def serve_visualizer(self, match):
        try:
            junk,gid = match.group(0).split('.')
            rep_file = os.getcwd() + "/games/" + gid + ".replay"
            f = open(rep_file)
            replaydata = f.read()
            f.close()
        except:
            self.send_error(404, 'File Not Found: %s.replay' % self.path)
            return
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
        return """<table id='games' class='tablesorter' width='100%'>
            <thead><tr><th>Game </th><th>Players</th><th>Turns</th><th>Date</th><th>Map</th></tr></thead>"""
        
        
    def game_line(self, g):
        html = "<tr><td width=10%><a href='/replay." + str(g.id) + "' title='Run in Visualizer'> Replay " + str(g.id) + "</a></td><td>"
        for key, value in sorted(g.players.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            html += "&nbsp;&nbsp;<a href='/player/" + str(key) + "' title='"+str(value[1])+"'>"+str(key)+"</a> (" + str(value[0]) + ") &nbsp;"
        html += "</td><td>" + str(g.turns) + "</td>"
        html += "</td><td>" + str(g.date) + "</td>"
        html += "<td><a href='/map/" + str(g.map) + "' title='View the map'>" + str(g.map) + "</a></td>"
        html += "</tr>\n"
        return html
        
        
    def rank_head(self):
        return """<table id='players' class='tablesorter' width='100%'>
            <thead><tr><th>Player</th><th>Rank</th><th>Skill</th><th>Mu</th><th>Sigma</th><th>Games</th><th>Last Seen</th></tr></thead>"""
        
    def page_counter(self,url,nelems):
        if nelems < table_lines: return ""
        html = "<table class='tablesorter'><tr><td>Page</td><td>&nbsp;&nbsp;"
        for i in range(min((nelems+table_lines)/table_lines,16)):
            html += "<a href='"+url+"p"+str(i)+"'>"+str(i)+"</a>&nbsp;&nbsp;&nbsp;"
        html += "</td></tr></table>"
        return html
        
    def rank_line( self, p ):
        html  = "<tr><td><a href='/player/" + str(p.name) + "'>"+str(p.name)+"</a></td>" 
        html += "<td>%d</td>"    % p.rank
        html += "<td>%2.4f</td>" % p.skill
        html += "<td>%2.4f</td>" % p.mu
        html += "<td>%2.4f</td>" % p.sigma
        html += "<td>%d</td>"    % p.ngames
        html += "<td>%s</td>"    % p.lastseen
        html += "</tr>\n"
        return html
        
    def serve_maps(self, match):
        html = self.header( "%d maps" % len(self.server.maps) )
        html += "<table id='maps' class='tablesorter' width='70%'>"
        html += "<thead><tr><th>Mapname</th><th>Players</th><th>Rows</th><th>Cols</th><th>Games</th></tr></thead>"
        html += "<tbody>"
        for k,v in self.server.maps.iteritems():
            html += "<tr><td><a href='/map/"+str(k)+"'>"+str(k)+"</a></td><td>"+str(v[0])+"</td><td>"+str(v[1])+"</td><td>"+str(v[2])+"</td><td>"+str(v[3])+"</td></tr>\n"
        html += "</tbody>"
        html += "</table>"
        html += self.footer()
        html += self.footer_sort('maps')
        html += "</body></html>"
        self.wfile.write(html)
        
        
    def serve_stats(self,match):
        self.send_head("text/plain")
        i=0
        txt = "%d %d" % (len(book.players),len(book.games))
        ct={"survived":0,"eliminated":0,"timeout":0,"crashed":0}
        for ng,g in sorted(self.server.db.games.iteritems(), reverse=True):
            for np,p in g.players.iteritems():
                if i == 100:  break
                ct[ p[1] ] += 1
                i += 1
            if i == table_lines:  break
        txt += " %d" % ct["survived"] 
        txt += " %d" % ct["eliminated"] 
        txt += " %d" % ct["timeout"] 
        txt += " %d" % ct["crashed"] 
        #~ txt += " ".join([p for p in book.players])
        self.wfile.write(txt)
        
    def serve_online(self,match):
        html = self.header( "online" )
        html += "%d players<ul>" % len(book.players)
        for p in book.players:
            html += "<li>%s</li>\n" % p
        html += "</ul><br>"
        html += "%d games<ul>" % len(book.games)
        for g in book.games:
            html += "<li>%s</li>\n" % g
        html += "</ul>"
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)
        
    def serve_charts(self,match):
        html = self.header( "stats" )
        html += """
            <div bgcolor='#aaa'>
            <br> &nbsp; &nbsp; &nbsp; 
            <font size=1 color='#0f0'>Games</font>
            <font size=1 color='#f00'>Players</font>
            <br> &nbsp; &nbsp; &nbsp; 
            <canvas id="chart" width="800" height="100"></canvas>            
            <br><br><br> &nbsp; &nbsp; &nbsp; 
            <font size=1 color='#0f0'>Survived</font>
            <font size=1 color='#f00'>Eliminated</font>
            <font size=1 color='#00f'>Timeout</font>
            <font size=1 color='#0ff'>Crashed</font>
            <br> &nbsp; &nbsp; &nbsp; 
            <canvas id="gstat" width="800" height="100"></canvas>            
            <script type="text/javascript" src="/js/smoothie.js"></script>
            <script type="text/javascript" src="/js/statistics.js"></script>
            <script> loadTabs(); </script>
            </div>
            """
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)


    def serve_radmin(self, match):
        if self.server.radmin_page:
            u,q = match.group(0).split('?')
            k,v = q.split('=')
            try:
                if k in self.server.opts:
                    self.server.opts[k] = v
            except Exception,e:
                print e
        self.serve_settings(match)


    def serve_main(self, match):
        html = self.header("There are %d games and %d players active on %s" % (len(book.games),len(book.players), self.server.opts['host']) )
        html += self.game_head()
        html += "<tbody>"
        offset=0
        if match and (len(match.group(0))>2):
            offset=table_lines * int(match.group(0)[2:])
            
        self.server.game_data_lock.acquire()
        i = 0
        count=0
        for k,g in sorted(self.server.db.games.iteritems(), reverse=True):
            i += 1
            if i <= offset: continue
            html += self.game_line(g)            
            count += 1
            if count> table_lines: break
        html += "</tbody></table>"
        html += self.page_counter("/", len(self.server.db.games) )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</body></html>"
        self.server.game_data_lock.release()
        self.wfile.write(html)
        
        
    def serve_player(self, match):
        player = match.group(0).split("/")[2]
        html = self.header( player )
        html += self.rank_head()
        html += "<tbody>"
        self.server.game_data_lock.acquire()
        html += self.rank_line( self.server.db.players[player] )
        html += "</tbody></table>"
        html += self.game_head()
        html += "<tbody>"
        i = 0
        count=0
        offset = 0
        if match:
            toks = match.group(0).split("/")
            if len(toks)>3:
                offset=table_lines * int(toks[3][1:])
        for k,g in sorted(self.server.db.games.iteritems(), reverse=True):
            if player in g.players:
                i += 1
                if i <= offset: continue
                count += 1
                if count > table_lines: continue
                html += self.game_line(g)                
        self.server.game_data_lock.release()
        html += "</tbody></table>"
        html += self.page_counter("/player/"+player+"/", i )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</body></html>"
        self.wfile.write(html)

        
    def serve_settings(self, match):
        html = self.header("Settings")
        html += "<table id='sets' class='tablesorter' width='70%'>"
        html += "<thead><tr><th>Name</th><th>Value</th></tr></thead>"
        html += "<tbody>"
        for k,v in self.server.opts.iteritems():
            if k=='map': continue
            html += "<tr><td>%s</td><td>%s</td></tr>\n" % (k,v)
        html += "</tbody>"
        html += "</table>"
        html += self.footer()
        html += self.footer_sort('sets')
        html += "</body></html>"
        self.wfile.write(html)
        
        
    def serve_ranking(self, match):
        html = self.header("Rankings")
        html += self.rank_head()
        html += "<tbody>"
        offset=0
        if match:
            toks = match.group(0).split("/")
            if len(toks)>2:
                offset=table_lines * int(toks[2][1:])
        self.server.game_data_lock.acquire()
        pz = self.server.db.players.items()
        self.server.game_data_lock.release()
        
        def by_skill( a,b ):
            return cmp(b[1].skill, a[1].skill)            
        pz.sort(by_skill)        
        i = 0
        count=0
        for n,p in pz:
            i += 1
            if i <= offset: continue
            html += self.rank_line( p )            
            count += 1
            if count> table_lines: break
            
        html += "</tbody></table>"
        html += self.page_counter("/ranking/", len(self.server.db.players) )
        html += self.footer()
        html += self.footer_sort('players')
        html += "</body></html>"
        self.wfile.write(html)
    
    
    def serve_map( self, match ):      
        ####  AH;SHUCKS, i'm too lazy to parse the map from js...
        #~ square = 5
        #~ html = """
        #~ <canvas width=""" +str(w)+ " height=" +str(h+20)+ """ id='C'>
        #~ <p>
        #~ <script>
            #~ mapdata = """ + mapdata + """;
            #~ colors = {
                #~ '%':'#0f5bb7',
                #~ '.':'#049227',
                #~ '*':'#1aba87',
                #~ 'a':'#4ca9c8',
                #~ 'b':'#6a9a2a',
                #~ 'c':'#8a2b44',
                #~ 'd':'#ff5d00'
                #~ 'e':'#4ca9c8',
                #~ 'f':'#6a9a2a',
                #~ 'g':'#8a2b44',
                #~ 'h':'#ff5d00'
                #~ }
            
            #~ C = document.getElementById('C')
            #~ V = C.getContext('2d');
            #~ function drawboard(turn) {
                #~ V.clearRect(0,0,500,500)
                #~ V.fillStyle = 'white'            
                #~ // draw base board 
                #~ for (r=0; r<h; r++) {
                    #~ for (c=0; c<w; c++) {
                        #~ elm = replay['board'][r][c]
                        #~ V.fillStyle = '#606060'
                        #~ V.fillRect(c*square,r*square,square,square);
                    #~ }
                #~ }
        #~ </script>"""
            
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
            
            
    #
    ## static files will get cached in a dict
    #
    def serve_file(self, match):
        mime = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','js':'text/javascript','py':'application/python','html':'text/html'}
        try:
            junk,end = match.group(0).split('.')
            mime_type = mime[end]
        except:
            mime_type = 'text/plain'
            
        fname = os.getcwd() + match.group(0)
        if not fname in self.server.cache:
            try:    
                f = open(fname,"rb")
                output = f.read()
                f.close()
                log.info("added static %s to cache." % fname)
                ## don't cache replays.
                if match.group(0).find("replay") < 0:
                    self.server.cache[fname] = output
            except:
                self.send_error(404, 'File Not Found: %s' % self.path)
                return
        else:
            output = self.server.cache[fname] 
            
        self.send_head(mime_type)
        self.wfile.write(output)
        
        
    def do_GET(self):

        if self.path == '/':
            self.serve_main(None)
            return
            
        for regex, func in (
                ('^\/%s(.*)' % self.server.radmin_page, self.serve_radmin),
                ('^\/online', self.serve_online),
                ('^\/charts', self.serve_charts),
                ('^\/stats', self.serve_stats),
                ('^\/settings', self.serve_settings),
                ('^\/ranking/p([0-9]?)', self.serve_ranking),
                ('^\/ranking', self.serve_ranking),
                ('^\/maps', self.serve_maps),
                ('^\/map/(.*)', self.serve_map),
                ('^\/player\/(.*)', self.serve_player),
                ('^\/replay\.([0-9]+)', self.serve_visualizer),
                ('^\/p([0-9]?)', self.serve_main),
                ('^\/?(.*)', self.serve_file),
                ):
            match = re.search(regex, self.path)
            if match:
                func(match)
                return
        self.send_error(404, 'File Not Found: %s' % self.path)




 
