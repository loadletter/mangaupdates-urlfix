#!/usr/bin/env python2
#semi-automates the search for groups on common hosts
import json
import requests
import sys
import re
import subprocess
import urllib
from BeautifulSoup import BeautifulSoup
from update import GROUPSJSON, jsonloadf

INVALID = "You specified an invalid group id."
WWWBROWSER = "firefox"
DOSEARCH = True
QUERYURL = 'http://google.com/search?q=%s&ie=utf-8&oe=utf-8'
AUTONOVEL = True

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
		print "Found", repr(n), "on novelupdates, parsing url..."
		soup = BeautifulSoup(req.text)
		gi = soup.find('table', {'class' : 'groupinfo'})
		url = gi.find('a')['href']
		results.append(url)
		if '.blogspot.' in url:
			url2 = re.sub('blogspot(\.[A-Za-z]{2,6})+(/|$)', 'blogspot.com/', url)
			if url2 != url:
				results.append(url2)
	return results

def fujo(n):
	results = []
	for website in ['http://%s.tumblr.com', 'http://%s.livejournal.com']:
		url = website % n
		req = requests.get(url)
		if req.status_code == 200:
			print "Found", repr(n), "on", url.split('.')[-2]
			results.append(url)
	return results

def get_content(url):
	req = requests.get(url)
	soup = BeautifulSoup(req.text)
	return soup.find('td', {'id': 'main_content'})

def get_end_id():
	con = get_content('http://www.mangaupdates.com/groups.html')
	for a in con.findAll('a'):
		if a.text == 'Last' and a['title'].startswith('Goto page'):
			last_page = a['href']
			break
	con = get_content(last_page)
	urls = con.findAll('a', {'alt': 'Group Info'})
	last_url = urls[-1]['href']
	return int(last_url.split('=')[-1])

def get_start_id():
	groups = jsonloadf(GROUPSJSON)
	first_id = max(groups.keys(), key=int)
	return int(first_id)

def submit_result(gid, url):
	postreq = requests.post('http://mufix.herokuapp.com/' + 'submit', data={"groupid" : gid, "refer" : "meme", "groupwww" : url})
	if "Sent" in postreq.text:
		print "OK"
	else:
		print "Error!"

def run(start_id, end_id):
	print start_id, "-->", end_id
	for g in range(start_id, end_id + 1):
		urls = []
		muurl = 'http://www.mangaupdates.com/groups.html?id=%i' % g
		req = requests.get(muurl)
		t = req.text
		if INVALID in t:
			print "Invalid group:", g
			continue
		name = parse_name(t)
		if "Novel" in t:
			if AUTONOVEL:
				novelurls = novel(name)
				if novelurls:
					print "Found URL:", repr(novelurls[-1])
					print "Submitting...",
					submit_result(g, novelurls[-1])
					continue
			else:
				urls.extend(novel(name))
		elif name.lower().replace(' ', '') == name and name[0] != '_':
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
					submit_result(g, urls[ir])
					break

		elif DOSEARCH:
			browserargs = [WWWBROWSER, muurl, QUERYURL % ('"' + urllib.quote(name) + '"')]
			subprocess.call(browserargs)

if __name__ == "__main__":
	run(get_start_id() + 1, get_end_id())
