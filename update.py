#!/usr/bin/env python
import os, re, sys, urllib2, json, subprocess, tempfile

WWWBROWSER = "firefox"
GROUPURL = "http://www.mangaupdates.com/groups.html?id=%i"
SCRIPTNAME = "mangaupdates_group.user.js"
CURRDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.join(CURRDIR, "src")
GROUPSJSON = os.path.join(SRCDIR, "groups.json")
GROUPSJSCRIPT = os.path.join(SRCDIR, "groups.js")
VERSIONJSON = os.path.join(SRCDIR, "version.json")
NUMSHARDS = 20
GROUPSDIR = os.path.join(SRCDIR, 'groups')
UPGRADEWARNING = '''(function () {if(typeof(localStorage) !== "undefined" && !localStorage.getItem('loadletter.urlfix.onlinedeprecated')) {alert("The version of mangaupdates-urlfix you're using is old, if you're getting this message you should probably reinstall it using the latest and faster version from https://github.com/loadletter/mangaupdates-urlfix"); localStorage.setItem('loadletter.urlfix.onlinedeprecated', 'true');} })();\n'''

import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from dbconf import DSN

def jsonloadf(filename):
	with open(filename) as f:
		data = json.load(f, 'utf-8')
	return data

def jsonsavef(filename, data):
	with open(filename, 'wb') as f:
		json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
	
def dumpqueue():
	print "Connecting to database"
	conn = psycopg2.connect(DSN)
	cur = conn.cursor()
	data = None
	try:
		cur.execute("SELECT id, groupid, groupwww, refer, remoteip, uagent FROM posts ORDER BY id")
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
	
def reviewqueue(data, curgroups):
	datadict = {}
	good = []
	#make a dictionary with group as key and a list of rows as value
	for row in data:
		gid = row[1]
		if str(gid) in curgroups and curgroups[str(gid)] == row[2]:
			print "Ignored unchanged:", gid
			continue
		cleanedurl = urlcleanup(row)
		if gid in datadict:
			datadict[gid].append(row)
			datadict[gid].extend(cleanedurl)
		else:
			datadict[gid] = [row] + cleanedurl
	#do review
	for k, v in datadict.iteritems():
		print "Loading group:", k
		muurl = GROUPURL % int(k)
		urls = map(lambda x: x[2].encode('utf-8'), v)
		browserargs = [WWWBROWSER, muurl] + urls
		subprocess.call(browserargs)
		while True:
			print "I) Ignore"
			for c in range(len(v)):
				print "%i)" % c, repr(v[c])
			r = raw_input('> ')
			if r.upper() == 'I':
				break
			try:
				ir = int(r)
				assert(0 <= ir < len(v))
			except (ValueError, AssertionError):
				print "Wrong choice"
			else:
				good.append(v[ir])
				break
	return good

def urlcleanup(row):
	originalurl = row[2]
	url = row[2]
	#make everything lowercase
	url = url.lower()
	#add protocol string if missing
	if not (url.startswith('http://') or url.startswith('https://')):
		url = 'http://' + url
	#replace the various blogspot tld with generic .com
	if '.blogspot.' in url:
		#url = re.sub('blogspot(\.[A-Za-z]{2,6})+', 'blogspot.com', url) #preserve everything after tld
		url = re.sub('blogspot(\.[A-Za-z]{2,6})+(/|$)', 'blogspot.com/', url) #always add slash
	if url != originalurl:
		#make a list because tuple doesn't support item assignment
		newrow = list(row)
		newrow[2] = url
		return [tuple(newrow)]
	return []

def incversion(ver):
	""" look for the last sequence of number(s) in a string and increment """
	lastnum = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')
	res = lastnum.search(ver)
	if res:
		incnum = str(int(res.group(1))+1)
		start, end = res.span(1)
		ver = ver[:max(end - len(incnum), start)] + incnum + ver[end:]
	return ver

def mergedict(origin_dict, update_dict):
	origin_dict.update(update_dict)

def mergediff(origin_dict, update_dict, verbose=True, output=sys.stdout):
	for k, v in update_dict.iteritems():
		if k in origin_dict and origin_dict[k] == v:
			if verbose:
				print >>output, "Unchanged {%s : %s}" % (k, v)
		elif k in origin_dict and origin_dict[k] != v:
			out = "Updated {%s : %s} ==> {%s : %s}" % (k, origin_dict[k], k, v) if verbose else "Updated %s" % k
			print >>output, out
		else:
			out = "Added {%s : %s}" % (k, v) if verbose else "Added %s" % k
			print >>output, out

def row2dict(row, outdict={}):
	outdict.update({str(row[1]) : row[2]})
	return outdict

def tmpfile_object():
	fdesc, path = tempfile.mkstemp()
	return os.fdopen(fdesc, 'wb'), path

def createonlinegroups(groups):
	with open(GROUPSJSCRIPT, 'wb') as f:
		f.write(UPGRADEWARNING)
		f.write("var urlfix_grouplist = ")
		json.dump(groups, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
		f.write(";\n")

def creategroupshards(groups):
	for i in range(NUMSHARDS):
		shardpath = os.path.join(GROUPSDIR, "%i.js" % i)
		with open(shardpath, 'wb') as f:
			shardgroups = dict(filter(lambda x: int(x[0]) % NUMSHARDS == i, groups.iteritems()))
			f.write("var urlfix_grouplist_shard = %i;\n" % i)
			f.write("var urlfix_grouplist = ")
			json.dump(shardgroups, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
			f.write(";\n")
			print i,

def updatefromdb():
	print "Proceed? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)
	
	print "Loading groups from file"
	currentgroups = jsonloadf(GROUPSJSON)
	currentversion = jsonloadf(VERSIONJSON)
	print "Current version:", currentversion
	
	dbrows = dumpqueue()
	printqueue(dbrows)
	tmpdict = {}
	for tr in dbrows:
		row2dict(tr, tmpdict)
	mergediff(currentgroups, tmpdict)
	print
	print "------------------------------------------------"
	
	print "Continue with browser review? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)
	
	good = reviewqueue(dbrows, currentgroups)
	gooddict = {}
	for r in good:
		row2dict(r, gooddict)
	
	print "-------------------"
	mergediff(currentgroups, gooddict)
	print "-------------------"
	#create changelog file
	newver = incversion(currentversion)
	changelog, changelogpath = tmpfile_object()
	print >>changelog, "Release %s" % newver
	print >>changelog
	mergediff(currentgroups, gooddict, verbose=False, output=changelog)
	changelog.close()
	
	print "Merge? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)
	
	mergedict(currentgroups, gooddict)
	print "Done!"
	print "New version will be:", newver
	
	print "Save data? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)

	print "Writing new online groups (groups.js).."
	createonlinegroups(currentgroups)
	print "Writing new new online groups (",
	creategroupshards(currentgroups)
	print ").."
	
	print "Writing groups.."
	jsonsavef(GROUPSJSON, currentgroups)
	print "Writing version.."
	jsonsavef(VERSIONJSON, newver)
	print "Done!"

	print "Commit changes? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)
	
	#commit changes
	print "Calling git commit.."
	gitargs = ["git", "commit", "-a", "-F", changelogpath]
	rc = subprocess.call(gitargs, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	if rc != 0:
		print "Git returned %i, aborting.." % rc
		sys.exit(1)
	#tag
	print "Calling git tag.."
	gitargs = ["git", "tag", newver]
	rc = subprocess.call(gitargs, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	if rc != 0:
		print "Git returned %i, aborting.." % rc
		sys.exit(1)
	#delete
	print "Delete from database? (y/n)"
	answer = raw_input("[y]>" )
	if answer != 'n':
		deletequeued(map(lambda x: x[0], dbrows))
	
	os.remove(changelogpath)
	print "Done!"
	print "Don't forget to push both commits (to gh-pages too) and tags!!!"
	
def main():
	updatefromdb()
    
if __name__ == '__main__':
    main()
