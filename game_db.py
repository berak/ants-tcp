#!/usr/bin/env python

import sqlite3
import datetime
import zlib
#~ import json

class GameDB():
	
	def __init__( self, file="antsdb.sqlite3" ):
		self.con = sqlite3.connect(file);
		self.recreate()
		
	def __del__( self ):
		try:
			self.con.close()
		except: pass
		
	def recreate(self):
		cur = self.con.cursor()		
		try:
			#~ cur.execute("create table opts ( turns integer default 1000, loadtime integer default 5000, turntime integer default 5000, trueskill text default 'py' );")
			cur.execute("create table gameindex(id integer primary key autoincrement, player text, gameid integer)")
			cur.execute("create table games(id integer, players text, map text, datum date, turns integer default 0, draws integer default 0)")
			cur.execute("create table players(id integer primary key autoincrement, name text unique, password text, lastseen date, rank integer default 1000, skill real default 0.0, mu real default 50.0, sigma real default 13.3,ngames integer default 0)")
			cur.execute("create table replays(id integer, json blob)")
			self.con.commit()
		except:
			pass
			
	def now(self):
		return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") #asctime()

	def update_defered( self, sql, tup=() ):
		cur = self.con.cursor()		
		cur.execute(sql,tup)
		
	def update( self, sql, tup=() ):
		self.update_defered(sql,tup)
		self.con.commit()
		
	def retrieve( self, sql, tup=() ):
		cur = self.con.cursor()		
		cur.execute(sql,tup)
		return cur.fetchall()

	def get_replay( self, i ):
		rep = self.retrieve("select json from replays where id=?", (i,) )
		return zlib.decompress(rep[0][0])
		#~ return rep[0][0]
		
	def add_replay( self, i, txt ):
		#~ data = txt
		data = buffer(zlib.compress(txt))
		self.update("insert into replays values(?,?)", (i,data) )
		
	def add_game( self, i, map, turns, draws, players ):
		self.update("insert into games values(?,?,?,?,?,?)", (i,players,self.now(),map,turns,draws))
		
	def num_games( self ):
		return int(self.retrieve( "select count(*) from games" )[0][0])
		
	def get_games( self, offset, num):
		return self.retrieve( "select * from games order by id desc limit ? offset ?", (num,offset) )

	def get_games_for_player( self, offset, num, player):
		arr = self.retrieve( "select gameid from gameindex where player=? order by gameid desc limit ? offset ?", (player,num,offset) )
		g = []
		for a in arr:
			z = self.retrieve( "select * from games where id=?", (a[0],))
			g.append( z[0]  )
		return g
		
	def num_games_for_player( self, player ):
		return int(self.retrieve( "select count(*) from gameindex where player=?",(player,) )[0][0])


	def num_players( self ):
		return int(self.retrieve( "select count(*) from players" )[0][0])
		
	def add_player( self, name,password ):
		self.update("insert into players values(?,?,?,?,?,?,?,?,?)", (None,name,password,self.now(),1000,0.0,50.0,50.0/3.0,0))
		
	def update_player_skill( self, name, skill, mu, sig ):
		self.update_defered("update players set ngames=ngames+1,lastseen=?,skill=?,mu=?,sigma=? where name=?", (self.now(),skill,mu,sig,name))
	
	## needs a final commit() 
	def update_player_rank( self, name, rank ):
		self.update_defered("update players set rank=? where name=?", (rank,name))
		
	def get_player( self, names ):
		sql = "select * from players where name=?"
		for n in names[1:]:
			sql += " or name=?" 
		return self.retrieve(sql, names )
		
	#~ def get_opts( self, opts ):
		#~ r = self.retrieve( "select * from opts" )
		#~ if r and len(r)==1:
			#~ for i,k in enumerate(r[0].keys()):
				#~ opts[ k ] = r[0][i]
				
