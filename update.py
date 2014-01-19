#!/usr/bin/env python
import os, re, sys, urllib2, json, subprocess


WWWBROWSER = "firefox"
GROUPURL = "http://www.mangaupdates.com/groups.html?id=%i"
CURRDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.join(CURRDIR, "src")

if len(sys.argv) == 2 and sys.argv[1] == 'remotedb':
	import psycopg2
	from dbconf import DSN

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

def incversion(ver):
	""" look for the last sequence of number(s) in a string and increment """
	lastnum = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')
	res = lastnum.search(ver)
	if res:
		incnum = str(int(res.group(1))+1)
		start, end = res.span(1)
		ver = ver[:max(end - len(incnum), start)] + incnum + ver[end:]
	return ver

def main():
	if len(sys.argv) < 2:
		print "Missing argument\nUsage:"
		print "update.py remotedb"
		print "update.py localjson filename"
		sys.exit(2)
    
if __name__ == '__main__':
    main()
