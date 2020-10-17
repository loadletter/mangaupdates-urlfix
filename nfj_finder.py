#!/usr/bin/env python2
#semi-automates the search for groups on common hosts
import json
import requests
import sys
import re
import subprocess
import urllib
import time
from BeautifulSoup import BeautifulSoup
from update import GROUPSJSON, jsonloadf

INVALID = "You specified an invalid group id."
WWWBROWSER = "firefox"
DOSEARCH = True
#QUERYURLS = ['https://mangadex.org/groups/0/1/%s', 'http://google.com/search?q=%s&ie=utf-8&oe=utf-8', 'http://yandex.com/yandsearch?text=%s']
QUERYURLS = ['https://mangadex.cc/groups/0/1/%s', 'http://google.com/search?q=%s&ie=utf-8&oe=utf-8'] 
AUTONOVEL = True
RUN_OFFSET = 100
LAST_OFFSET = 20

requests_s = requests.Session()
requests_s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})

def parse_name(data):
	soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
	return soup.find('div', {'class' : 'p-1 col-6 specialtext'}).text

def get_slug(n):
	a = re.sub('[^a-z0-9\-\.\ ]', '' , n.lower())
	b = re.sub('[\ \.]+', '-', a)
	return b

def novel(n):
	results = []
	slug = get_slug(n)
	req = requests_s.get('http://www.novelupdates.com/group/%s/' % slug)
	if req.status_code == 200:
		print "Found", repr(n), "on novelupdates, parsing url..."
		soup = BeautifulSoup(req.text)
		gi = soup.find('table', {'class' : 'groupinfo'})
		try:
			url = gi.find('a')['href']
		except:
			return []
		results.append(url)
		if '.blogspot.' in url:
			url2 = re.sub('blogspot(\.[A-Za-z]{2,6})+(/|$)', 'blogspot.com/', url)
			if url2 != url:
				results.append(url2)
	return results

def fujo(n):
	results = []
	for website in ['http://%s.tumblr.com', 'http://%s.livejournal.com']:
		url = website % n.lower()
		try:
			req = requests_s.get(url)
		except requests.exceptions.InvalidURL:
			pass
		else:
			if req.status_code == 200:
				print "Found", repr(n), "on", url.split('.')[-2]
				results.append(url)
	return results

def get_start_id():
	groups = jsonloadf(GROUPSJSON)
	first_id = max(groups.keys(), key=int)
	return int(first_id)

def submit_result(gid, url):
	postreq = requests_s.post('http://mufix.herokuapp.com/' + 'submit', data={"groupid" : gid, "refer" : "meme", "groupwww" : url})
	if "Sent" in postreq.text:
		print "OK"
	else:
		print "Error!"

def run(start_id):
	print "START:", start_id
	invalid_count = 0
	last_valid = None
	for g in range(start_id, start_id + RUN_OFFSET):
		sys.stderr.write("\r[%d]" % g)
		sys.stderr.flush()

		if invalid_count > LAST_OFFSET:
			print "END:", last_valid
			break
				
		urls = []
		muurl = 'https://www.mangaupdates.com/groups.html?id=%i' % g
		try:
			req = requests_s.get(muurl)
		except requests.exceptions.ConnectionError:
			print "Connection error:", g
			continue
		t = req.text
		if INVALID in t:
			print "Invalid group:", g
			invalid_count += 1
			continue
		name = parse_name(t)
		invalid_count = 0
		last_valid = g
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
		#if re.match('^[A-Za-z0-9\- ]+$', name):
		#	urls.extend(fujo(name.replace(' ','')))
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
			browserargs = [WWWBROWSER, muurl]
			#browserargs += map(lambda x: x % ('"' + urllib.quote(name.encode('utf-8')) + '"'), QUERYURLS)
			browserargs += map(lambda x: x % (urllib.quote(name.encode('utf-8'))), QUERYURLS)
			time.sleep(1)
			subprocess.call(browserargs)
	if invalid_count <= LAST_OFFSET:
		print "SHORT RUN!"

if __name__ == "__main__":
	if len(sys.argv) > 1:
		run(int(sys.argv[1]))
	else:
		run(get_start_id() + 1)
