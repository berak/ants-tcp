from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler 
import os
import re
import threading
import logging
import json
import random
import time
import SimpleHTTPServer
import socket

import game_db
from tcpserver import load_map_info

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

style = """
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
"""

table_lines = 100

class AntsHttpServer(HTTPServer):
    def __init__(self, *args):
        self.opts = None

        ## anything static gets cached on startup here.
        self.cache = {}
        self.cache_file("/favicon.ico","favicon.ico")
        self.cache_file("/tcpclient.py", "clients/tcpclient.py")
        self.cache_dir("js")
        self.cache_dir("maps")
        self.cache_dir("data/img")
        
        self.maps = load_map_info()
        self.db = game_db.GameDB()
        
        HTTPServer.__init__(self, *args)


    def cache_file(self,fname,fpath):
        try:
            f = open(fpath,"rb")
            data = f.read()
            f.close()
            log.info("added static %s to cache." % fname)
            self.cache[fname] = data
        except Exception, e:
            log.error("caching %s failed. %s" % (fname,e))


    def cache_dir(self,dir):
        for root,dirs,filenames in os.walk(dir):
            for filename in filenames:
                fname = "/" + dir + "/" + filename
                fpath = dir + "/" + filename
                self.cache_file(fname,fpath)

        
class AntsHttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, *args):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, *args)
    
    ## this suppresses logging from SimpleHTTPRequestHandler
    ## comment this method if you want to see them
    ##def log_message(self,format,*args):
    ##    pass
    
                
    def send_head(self, type='text/html'):
        self.send_response(200)
        self.send_header('Content-type',type)
        self.end_headers()
        
    def header(self, title):
        self.send_head()
        
        head = """<html><head>
        <link rel="icon" href='/favicon.ico'>
        <title>"""  + title + """</title>
        <style>"""  + style + """</style>"""
        if str(self.server.opts['sort'])=='True':
            head += """
                <script type="text/javascript" src="/js/jquery-1.2.6.min.js"></script> 
                <script type="text/javascript" src="/js/jquery.tablesorter.min.js"></script>
                """
        head += """</head><body><b> &nbsp;&nbsp;&nbsp;
        <a href='/' name=top> Games </a> &nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/ranking'> Rankings </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/maps'> Maps </a> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href='/tcpclient.py' title='get the python client'> Client.py </a>
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
        apic="^^^"
        return "<p><br> &nbsp;<a href=#top title='crawl back to the top'> " + apic + "</a>"
    
    
    def serve_visualizer(self, match):
        try:
            junk,gid = match.group(0).split('.')
            replaydata = self.server.db.get_replay(gid)
        except Exception, e:
            self.send_error(500, '%s' % (e,))
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
                        var options = new Options();
                        options.data_dir = '/data/';
                        options.embedded = true;
                        var visualizer = new Visualizer(document.body, options);
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
        return """<table id='games' class='tablesorter' width='98%'>
            <thead><tr><th>Game </th><th>Players</th><th>Turns</th><th>Date</th><th>Map</th></tr></thead>"""
        
        
    def game_line(self, g):
        html = "<tr><td width=10%><a href='/replay." + str(g[0]) + "' title='Run in Visualizer'> Replay " + str(g[0]) + "</a></td><td>"
        for key, value in sorted(json.loads(g[1]).iteritems(), key=lambda (k,v): (v,k), reverse=True):
            html += "&nbsp;&nbsp;<a href='/player/" + str(key) + "' title='"+str(value[1])+"'>"+str(key)+"</a> (" + str(value[0]) + ") &nbsp;"
        html += "</td><td>" + str(g[4]) + "</td>"
        html += "</td><td>" + str(g[2]) + "</td>"
        html += "<td><a href='/map/" + str(g[3]) + "' title='View the map'>" + str(g[3]) + "</a></td>"
        html += "</tr>\n"
        return html
        
        
    def rank_head(self):
        return """<table id='players' class='tablesorter' width='98%'>
            <thead><tr><th>Player</th><th>Rank</th><th>Skill</th><th>Mu</th><th>Sigma</th><th>Games</th><th>Last Seen</th></tr></thead>"""
        
    def page_counter(self,url,nelems):
        if nelems < table_lines: return ""
        html = "<table class='tablesorter'><tr><td>Page</td><td>&nbsp;&nbsp;"
        for i in range(min((nelems+table_lines)/table_lines,10)):
            html += "<a href='"+url+"p"+str(i)+"'>"+str(i)+"</a>&nbsp;&nbsp;&nbsp;"
        html += "</td></tr></table>"
        return html
        
    def rank_line( self, p ):
        html  = "<tr><td><a href='/player/" + str(p[1]) + "'>"+str(p[1])+"</a></td>" 
        html += "<td>%d</td>"    % p[4]
        html += "<td>%2.4f</td>" % p[5]
        html += "<td>%2.4f</td>" % p[6]
        html += "<td>%2.4f</td>" % p[7]
        html += "<td>%d</td>"    % p[8]
        html += "<td>%s</td>"    % p[3]
        html += "</tr>\n"
        return html
        
    def serve_maps(self, match):
        html = self.header( "%d maps" % len(self.server.maps) )
        html += "<table id='maps' class='tablesorter' width='70%'>"
        html += "<thead><tr><th>Mapname</th><th>Players</th><th>Rows</th><th>Cols</th></tr></thead>"
        html += "<tbody>"
        for k,v in self.server.maps.iteritems():
            html += "<tr><td><a href='/map/"+str(k)+"'>"+str(k)+"</a></td><td>"+str(v[0])+"</td><td>"+str(v[1])+"</td><td>"+str(v[2])+"</td></tr>\n"
        html += "</tbody>"
        html += "</table>"
        html += self.footer()
        html += self.footer_sort('maps')
        html += "</body></html>"
        self.wfile.write(html)


    def serve_main(self, match):
        html = self.header(self.server.opts['host'])
        html += self.game_head()
        html += "<tbody>"
        offset=0
        if match and (len(match.group(0))>2):
            offset=table_lines * int(match.group(0)[2:])
            
        for g in self.server.db.get_games(offset,table_lines):
            html += self.game_line(g)            
        html += "</tbody></table>"
        html += self.page_counter("/", self.server.db.num_games() )
        html += self.footer()
        html += self.footer_sort('games')
        html += "</body></html>"
        self.wfile.write(html)
        
        
    def serve_player(self, match):
        player = match.group(0).split("/")[2]
        res = self.server.db.get_player((player,))
        if len(res)< 1:
            self.send_error(404, 'Player Not Found: %s' % self.path)
            return            
        html = self.header( player )
        html += self.rank_head()
        html += "<tbody>"
        html += self.rank_line( res[0] )
        html += "</tbody></table>"
        html += self.game_head()
        html += "<tbody>"
        offset = 0
        if match:
            toks = match.group(0).split("/")
            if len(toks)>3:
                offset=table_lines * int(toks[3][1:])
        for g in self.server.db.get_games_for_player(offset, table_lines, player):
            html += self.game_line(g)                
        html += "</tbody></table>"
        html += self.page_counter("/player/"+player+"/", self.server.db.num_games_for_player(player) )
        html += self.footer()
        html += self.footer_sort('games')
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
        for p in self.server.db.retrieve("select * from players order by skill desc limit ? offset ?",(table_lines,offset)):
            html += self.rank_line( p )            
            
        html += "</tbody></table>"
        html += self.page_counter("/ranking/", self.server.db.num_players() )
        html += self.footer()
        html += self.footer_sort('players')
        html += "</body></html>"
        self.wfile.write(html)
    
    
    def serve_map( self, match ):      
        try:
            mapname = match.group(0).split('/')[2]
            m = self.server.cache["/maps/"+mapname]
        except:
            self.send_error(404, 'Map Not Found: %s' % self.path)
            return
        w=0
        h=0
        s=5
        jsmap = "var jsmap=[\n"
        for line in m.split('\n'):
            line = line.strip().lower()
            if not line or line[0] == '#':
                continue
            key, value = line.split(' ')
            if key == 'm':
                jsmap += '\"' + value + "\",\n"
            if key == 'rows':
                h = int(value)
            if key == 'cols':
                w = int(value)
        jsmap += "]\n"
        
        html = self.header(mapname)
        html += "&nbsp;&nbsp;&nbsp;<canvas width="+str(s*w)+" height="+str(s*h)+" id='C'><p>\n<script>\n"+jsmap+"var square = " + str(s) + "\n"
        html +=""" 
            var colors = { '%':'#1e3f5d', '.':'#553322', 'a':'#4ca9c8', 'b':'#6a9a2a', 'c':'#8a2b44', 'd':'#ff5d00', 'e':'#4ca9c8', 'f':'#6a9a2a', 'g':'#8a2b44', 'h':'#ff5d00', '0':'#4ca9c8', '1':'#6a9a2a', '2':'#8a2b44', '3':'#ff5d00', '4':'#4ca9c8', '5':'#6a9a2a', '6':'#8a2b44', '7':'#ff5d00' }            
            var C = document.getElementById('C')
            var V = C.getContext('2d');
            for (var r=0; r<jsmap.length; r++) {
                var line = jsmap[r]
                for (var c=0; c<line.length; c++) {
                    V.fillStyle = colors[line[c]]
                    V.fillRect(c*square,r*square,square,square);
                }
            }
            </script>
            </canvas>
            """
        html += self.footer()
        html += "</body></html>"
        self.wfile.write(html)
            
            
    ## static files aer served from cache
    def serve_file(self, match):
        mime = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','js':'text/javascript','py':'application/python','html':'text/html'}
        try:
            junk,end = match.group(0).split('.')
            mime_type = mime[end]
        except:
            mime_type = 'text/plain'
            
        fname = match.group(0)
        if not fname in self.server.cache:
            self.send_error(404, 'File Not Found: %s' % self.path)
            return
            
        self.send_head(mime_type)
        self.wfile.write(self.server.cache[fname] )
        
        
    def do_GET(self):
                
        if self.path == '/':
            self.serve_main(None)
            return
            
        for regex, func in (
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




 
def main():

    web_port = 2080
    opts = {
        ## web opts:
        'sort': 'True',			# include tablesorter & jquery and have sortable tables(requires ~70kb additional download)

        ## read only info
        'host': socket.gethostname(),
    }


    web = AntsHttpServer(('', web_port), AntsHttpHandler)
    web.opts = opts
    web.serve_forever()

if __name__ == "__main__":
    main()


