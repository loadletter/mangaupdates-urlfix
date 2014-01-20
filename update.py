#!/usr/bin/env python
import os, re, sys, urllib2, json, subprocess, tempfile


WWWBROWSER = "firefox"
GROUPURL = "http://www.mangaupdates.com/groups.html?id=%i"
SCRIPTNAME = "mangaupdates_group.user.js"
CURRDIR = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.join(CURRDIR, "src")
GROUPSJSON = os.path.join(SRCDIR, "groups.json")
VERSIONJSON = os.path.join(SRCDIR, "version.json")
SCRIPTEMPLATE = os.path.join(SRCDIR, SCRIPTNAME)
USERSCRIPT = os.path.join(CURRDIR, SCRIPTNAME)
METASCRIPT = os.path.join(CURRDIR, SCRIPTNAME.replace(".user.", ".meta."))

if len(sys.argv) == 2 and sys.argv[1] == 'remotedb':
	import psycopg2
	from dbconf import DSN

def jsonloadf(filename):
	with open(filename) as f:
		data = json.load(f, 'utf-8')
	return data

def jsonsavef(filename, data):
	with open(filename, 'w') as f:
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
		browserargs = [WWWBROWSER, muurl, row[2].encode('utf-8')]
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
	return os.fdopen(fdesc, 'w'), path

def fillheader(version):
	with open(SCRIPTEMPLATE + ".head") as f:
		data = f.read()
	return data.replace('<!--VERSION_PLACEHOLDER--!>', version)

def createuserscript(scriptheader, groups):
	with open(SCRIPTEMPLATE + ".bottom") as fin:
		bottom = fin.read()
	
	with open(USERSCRIPT, 'w') as f:
		f.write(scriptheader)
		f.write("var groups = ")
		json.dump(groups, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
		f.write(";\n")
		f.write(bottom)

def createmetascript(scriptheader):
	with open(METASCRIPT, 'w') as f:
		f.write(scriptheader)

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
	
	print "Continue with browser review? (y/n)"
	answer = raw_input("[n]> ")
	if answer != 'y':
		sys.exit(0)
	
	good, bad = reviewqueue(dbrows)
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

	print "Loading header..."
	header = fillheader(newver)
	print "Writing new userscript (user.js).."
	createuserscript(header, currentgroups)
	print "Writing new userscript (meta.js).."
	createmetascript(header)
	
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
	subprocess.call(gitargs, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	#tag
	print "Calling git tag.."
	gitargs = ["git", "tag", newver]
	subprocess.call(gitargs, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
	
	#ask what to delete (nothing, bad, good, both)
	while True:
		print "Delete from database?"
		print "0) None"
		print "1) Bad"
		print "2) Good"
		print "3) All"
		answer = raw_input()
		if answer not in ['0', '1', '2', '3']:
			print "Error"
			continue
		break
	answer = int(answer)
	
	if answer == 0:
		sys.exit(0)
	elif answer == 1:
		deletelist = map(lambda x: x[0], bad)
	elif answer == 2:
		deletelist = map(lambda x: x[0], good)
	elif answer == 3:
		deletelist = map(lambda x: x[0], bad) + map(lambda x: x[0], good)
		
	deletequeued(deletelist)
	os.remove(changelogpath)
	print "Done!"
	print "Don't forget to push both commits and tags!!!"
	
def main():
	if len(sys.argv) < 2:
		print "Missing argument\nUsage:"
		print "update.py remotedb"
		print "update.py localjson filename"
		sys.exit(2)
	
	if sys.argv[1] == "remotedb":
		updatefromdb()
    
if __name__ == '__main__':
    main()
