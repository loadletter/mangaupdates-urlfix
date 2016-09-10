#!/usr/bin/env python2
#semiautomates the search for groups on common hosts
import json
import requests
import sys
import re
import subprocess
from BeautifulSoup import BeautifulSoup

INVALID = "You specified an invalid group id."
WWWBROWSER = "firefox"

def parse_name(data):
	soup = BeautifulSoup(data)
	return soup.find('td', {'class' : 'specialtext'}).text

def get_slug(n):
	a = re.sub('[^a-z0-9\-\.\ ]', '' , n.lower())
	b = re.sub('[\ \.]+', '-', a)
	return b

def novel(n):
	results = []
	slug = get_slug(n)
	req = requests.get('http://www.novelupdates.com/group/%s/' % slug)
	if req.status_code == 200:
		print "Found on novelupdates, parsing url..."
		soup = BeautifulSoup(req.text)
		gi = soup.find('table', {'class' : 'groupinfo'})
		results.append(gi.find('a')['href'])
	return results

def fujo(n):
	results = []
	for website in ['http://%s.tumblr.com', 'http://%s.livejournal.com']:
		url = website % n
		req = requests.get(url)
		if req.status_code == 200:
			print "Found on", url.split('.')[-2]
			results.append(url)
	return results

def run(start_id, end_id):
	for g in range(start_id, end_id):
		urls = []
		muurl = 'http://www.mangaupdates.com/groups.html?id=%i' % g
		req = requests.get(muurl)
		t = req.text
		if INVALID in t:
			print "Invalid group:", g
		else:
			name = parse_name(t)
			if "Novel" in t:
				urls.extend(novel(name))
			elif name.lower().replace(' ', '') == name:
				urls.extend(fujo(name))
			else:
				print "Nothing special about", g
		if urls:
			browserargs = [WWWBROWSER, muurl] + urls
			subprocess.call(browserargs)
			while True:
				print "I) Ignore"
				for c, u in enumerate(urls):
					print "%i)" % c, repr(u)
				r = raw_input('> ')
				if r.upper() == 'I':
					break
				try:
					ir = int(r)
					assert(0 <= ir < len(urls))
				except (ValueError, AssertionError):
					print "Wrong choice"
				else:
					postreq = requests.post('http://mufix.herokuapp.com/' + 'submit', data={"groupid" : g, "refer" : "meme", "groupwww" : urls[ir]})
					if "Sent" in postreq.text:
						print "OK"
					else:
						print "Error!"
					break

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print "Usage:", sys.argv[0], "startID endID"
	run(int(sys.argv[1]), int(sys.argv[2]))
