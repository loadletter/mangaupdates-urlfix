#!/usr/bin/env python
import os, re, sys, urllib2, json, psycopg2
from dbconf import DSN

WWWBROWSER = "firefox"

def jsonloadf(filename):
	f = open(filename)
	return json.load(f, 'utf-8')

def jsonsavef(filename, data):
	f = open(filename, 'w')
	json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
	
def dumpqueue()
	conn = psycopg2.connect(DSN)
	cur = conn.cursor()
	
	data = None
	try:
		cur.execute("SELECT id, groupid, groupwww, refer, remoteip, uagent FROM posts")
		data = cur.fetchall()
	except:
		print "Database Error"
		conn.rollback()
		
	if not data:
		print "No data, exiting..."
		sys.exit(0)
	
	conn.commit()
	cur.close()
	conn.close()
	
	return data

def deletequeued(id_list):
	conn = psycopg2.connect(DSN)
	cur = conn.cursor()
	
	delete_list = map(lambda x: (x,), id_list)
	try:
		cur.executemany("DELETE FROM posts WHERE id = %s", delete_list)
	except:
		print "Database Error, couldn't delete:", repr(a)
		conn.rollback()
	
	conn.commit()
	cur.close()
	conn.close()
	
	
	
if __name__ == '__main__':
    main()
