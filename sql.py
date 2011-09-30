# A minimal SQLite shell
#
# ## reset the player ranks:
# update players set skill=0.0, mu=50.0, sigma=13.3, rank=1000, ngames=0;
#
# ## retrieve a replay:
# select json from replays where id=13 ;
#

import sqlite3
import zlib

con = sqlite3.connect("antsdb.sqlite3")
con.isolation_level = None
cur = con.cursor()

buffer = ""

print "Enter your SQL commands(split by: ';') to execute in sqlite3."
print "Enter a blank line to exit."

while True:
    line = raw_input()
    if line == "":
        break
    buffer += line
    if sqlite3.complete_statement(buffer):
        try:
            buffer = buffer.strip()
            cur.execute(buffer)
            cmd = buffer.lstrip().upper()
            if cmd.startswith("SELECT"):
                if cmd.find("REPLAYS")>-1:
                    print zlib.decompress(cur.fetchall()[0][0])
                else:                
                    print cur.fetchall()
        except sqlite3.Error, e:
            print "An error occurred:", e.args[0]
        buffer = ""

con.close()
