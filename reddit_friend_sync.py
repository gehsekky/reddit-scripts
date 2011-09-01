#! /usr/bin/env python

"""Script for syncing friends across multiple reddit accounts

User needs to put in their login info below

Example:

login_info = [
["user1", "pass1"], 
["user2", "pass2"], 
["user3", "pass3"]
]

"""

# login info array
login_info = [
]

#DO NOT MODIFY BELOW THIS LINE

import urllib
import urllib2
import cookielib
import re
import json
import time

login_url = "http://www.reddit.com/api/login/"
friends_list_url = "http://www.reddit.com/prefs/friends/"
friends_api_url = "http://www.reddit.com/api/friend/"
self_info_url = "http://www.reddit.com/api/me.json"
cookie_jar = None

# cycle through login info array and build friends list
friends = []
for userpass in login_info:
	print "getting friends for " + userpass[0]
	cookie_jar = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
	urllib2.install_opener(opener)
	postdata = urllib.urlencode(dict(user=userpass[0], passwd=userpass[1], api_type="json"))
	req = urllib2.Request(login_url + userpass[0], postdata)
	rsp = urllib2.urlopen(req)
	cookie_jar.extract_cookies(rsp, req)
	content = rsp.read()

	# now get friends list html
	req = urllib2.Request(friends_list_url)
	rsp = urllib2.urlopen(req)
	content = rsp.read()
	
	# regex parse page for friends
	parsed_friends = []
	for friend_match in re.finditer('<td><span\sclass="user"><a\shref="http://www.reddit.com/user/.*?/" >(?P<friendname>.*?)</a>', content):
		parsed_friends.append(friend_match.group("friendname"))
	
	# add friends to friend list
	for friend_name in parsed_friends:
		if (friends.count(friend_name) == 0):
			friends.append(friend_name)
	
	# throttle
	time.sleep(2)

# sync friends list on each account
for userpass in login_info:
	print "syncing friends for " + userpass[0]
	cookie_jar = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
	urllib2.install_opener(opener)
	postdata = urllib.urlencode(dict(user=userpass[0], passwd=userpass[1], api_type="json"))
	req = urllib2.Request(login_url + userpass[0], postdata)
	rsp = urllib2.urlopen(req)
	cookie_jar.extract_cookies(rsp, req)
	content = rsp.read()

	# get /api/me info
	req = urllib2.Request(self_info_url)
	rsp = urllib2.urlopen(req)
	jsondata = json.load(rsp)
	container_id = jsondata["kind"] + "_" + jsondata["data"]["id"]
	modhash = jsondata["data"]["modhash"]
	
	# add friends
	for friend in friends:
		postdata = urllib.urlencode(dict(action="add", type="friend", 
										 name=friend, uh=modhash, 
										 container=container_id))
		req = urllib2.Request(friends_api_url, postdata)
		rsp = urllib2.urlopen(req)
		# throttle
		time.sleep(2)

	# throttle
	time.sleep(2)