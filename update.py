#!/usr/bin/env python
import os, re, sys, urllib2, json, psycopg2, subprocess
from dbconf import DSN

WWWBROWSER = "firefox"
GROUPURL = "http://www.mangaupdates.com/groups.html?id=%i"

def jsonloadf(filename):
	f = open(filename)
	return json.load(f, 'utf-8')

def jsonsavef(filename, data):
	f = open(filename, 'w')
	json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
	
def dumpqueue():
	print "Connecting to database"
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
	
	print "Got %i rows" % len(data)
	
	conn.commit()
	cur.close()
	conn.close()
	
	return data

def deletequeued(id_list):
	print "Connecting to database"
	conn = psycopg2.connect(DSN)
	cur = conn.cursor()
	
	delete_list = map(lambda x: (x,), id_list)
	try:
		cur.executemany("DELETE FROM posts WHERE id = %s", delete_list)
	except:
		print "Database Error, couldn't delete:", repr(a)
		conn.rollback()
		cur.close()
		conn.close()
		return
	
	print "Deleted %i rows" % len(id_list)
	
	conn.commit()
	cur.close()
	conn.close()
	
def printqueue(data):
	print "------------------------------------------------"
	print "(id, groupid, groupwww, refer, remoteip, uagent)"
	for row in data:
		print repr(row)
	
	print
	print "------------------------------------------------"
	
def reviewqueue(data):
	goodlist = []
	badlist = []
	for row in data:
		print "Loading:", repr(row)
		muurl = GROUPURL % int(row[1])
		browserargs = [WWWBROWSER, '"%s"' % muurl, '"%s"' % row[2].encode('utf-8')]
		subprocess.call(browserargs)
		actionrow(row, goodlist, badlist)
	
	return goodlist, badlist

def actionrow(row, goodlist, badlist):
	while True:
		print "1) Accept"
		print "2) Ignore"
		print "3) Delete"
		answer = raw_input()
		if answer not in ['1', '2', '3']:
			print "Error"
			continue
		break
	answer = int(answer)
	if answer == 1:
		goodlist.append(row)
	elif answer == 3:
		badlist.append(row)
	return answer


if __name__ == '__main__':
    main()
