#!/usr/bin/env python

import os, re, sys, urllib2, multiprocessing, json

def jsonloadf(filename):
	f = open(filename)
	return json.load(f, 'utf-8')

def jsonsavef(filename, data):
	f = open(filename, 'w')
	json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')

if __name__ == '__main__':
    main()
