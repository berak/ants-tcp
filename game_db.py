#!/usr/bin/env python
#~ import cPickle as serialize
import pickle as serialize
#~ import json as serialize

class PlayerData():
	name = None
	skill = 0.0
	mu = 50.0
	sigma = 3.0
	ngames = 0
	rank = 0

class GameData():
	id = 0		# number
	date = None # time.asctime
	map = None
	turns = 0
	players={}  # {name:(score,status)}


class GameDB():
	games = {}
	players={}
	latest = 0
	
#
# global methods to allow easy serialisation for gamedb
# it's as clumsy, as it looks.
#
def load():
	db = GameDB()
	try:
		f = open("games/saved_latest", "rb")
		db.latest = serialize.load(f)
		f.close()
		f = open("games/saved_players", "rb")
		db.players = serialize.load(f)
		f.close()
		f = open("games/saved_games", "rb")
		db.games = serialize.load(f)
		f.close()
	except:
		# better empty, than corrupted
		db = GameDB()
	return db
	
def save(db):
	f = open("games/saved_latest", "wb")
	serialize.dump(db.latest,f)
	f.close()
	f = open("games/saved_players", "wb")
	serialize.dump(db.players,f)
	f.close()
	f = open("games/saved_games", "wb")
	serialize.dump(db.games,f)
	f.close()

