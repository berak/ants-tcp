#!/usr/bin/env python

import sys
import os
import string



def check_map_dir(mapdir):
	"""
	test all maps in dir for hives totally surrounded by water
	"""
	
	maps={}
	for root,dirs,filenames in os.walk(mapdir):
		for filename in filenames:
			mf = open(mapdir+"/"+filename,"r")
			data = ""
			for line in mf:
				if line.startswith('players'):	p = int(line.split()[1])
				if line.startswith('rows'):		r = int(line.split()[1])
				if line.startswith('cols'):		c = int(line.split()[1])
				if line.startswith('m'):		data += line.split()[1] + "\n"
			mf.close()
			maps[filename] = [p,r,c,data]
			
	for m in maps:
		data = maps[m][3].split("\n")
		rows = maps[m][1]
		cols = maps[m][2]
		for row,line in enumerate(data):
			for col in range(len(line)):
				is_water = 0
				d = line[col]
				if d in string.digits:
					if data[row][ (cols + col + 1 ) % cols ] == '%': is_water += 1
					if data[row][ (cols + col - 1 ) % cols ] == '%': is_water += 1
					if data[ ( row + rows + 1 ) % rows ][col] == '%': is_water += 1
					if data[ ( row + rows - 1 ) % rows ][col] == '%': is_water += 1
				if is_water == 4:
					print "%s player %s [%d %d]" % (m,d, row,col)



check_map_dir(sys.argv[1])
