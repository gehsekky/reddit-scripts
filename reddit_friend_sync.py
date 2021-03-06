#! /usr/bin/env python

"""Script for syncing friends across multiple reddit accounts

User needs to put in their login info below

Example:

login_info = [
["user1", "pass1"], 
["user2", "pass2"], 
["user3", "pass3"]
]

add_self_to_friends should be either "True" or "False" (without quotations)

"""

# login info array
login_info = [
]

# add user to user's set of friends? (helps for finding your own posts on page)
add_self_to_friends = True

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

def make_http_request(method, url, **postdata):
    """Make an http request and set cookies"""
    global cookie_jar
    time.sleep(2) # throttle
    if not cookie_jar:
        cookie_jar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        urllib2.install_opener(opener)
    if postdata:
        postdata = urllib.urlencode(postdata)
    if method == "GET":
        url += "?"
        for key in postdata:
            url+= key + "=" + postdata[key] + "&"
        postdata = None
    req = urllib2.Request(url, postdata)
    rsp = urllib2.urlopen(req)
    cookie_jar.extract_cookies(rsp, req)
    return rsp

print "starting reddit_friend_sync"
# cycle through login info array and build friends list
allfriends = []
friends = {}
for userpass in login_info:
    print "getting friends for " + userpass[0]
    # login
    make_http_request("POST", login_url + userpass[0], user=userpass[0], passwd=userpass[1], api_type="json")
    
    # now get friends list html
    rsp = make_http_request("GET", friends_list_url)
    content = rsp.read()
    
    # regex parse page for friends
    parsed_friends = []
    for friend_match in re.finditer('<td><span\sclass="user"><a\shref="http://www.reddit.com/user/.*?/" >(?P<friendname>.*?)</a>', content):
        parsed_friends.append(friend_match.group("friendname"))
        
    # see if we add ourself to friend's list
    if add_self_to_friends:
        if allfriends.count(userpass[0]) == 0:
            allfriends.append(userpass[0])
    
    # add friends to friend dictionary under key for username
    friends[userpass[0]] = parsed_friends
    
    # add friends to big friends list
    for friend_name in parsed_friends:
        if allfriends.count(friend_name) == 0:
                allfriends.append(friend_name)

# sync friends list on each account
for userpass in login_info:
    print "syncing friends for " + userpass[0]
    # login
    make_http_request("POST", login_url + userpass[0], user=userpass[0], passwd=userpass[1], api_type="json")
    
    # get /api/me info
    rsp = make_http_request("GET", self_info_url)
    jsondata = json.load(rsp)
    container_id = jsondata["kind"] + "_" + jsondata["data"]["id"]
    modhash = jsondata["data"]["modhash"]
    
    # add friends that current user doesn't already have (reduce api calls)
    friends_to_add = [x for x in allfriends if x not in set(friends[userpass[0]])]
    for friend_to_add in friends_to_add:
        print "\tadding " + friend_to_add
        make_http_request("POST", friends_api_url, action="add", type="friend", name=friend_to_add, uh=modhash, container=container_id)

print "finishing reddit_friend_sync"