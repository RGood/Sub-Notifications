# oauth_notifications.py  #
# Written by /u/The1RGood #
###########################
#==================================================Config stuff====================================================
import ConfigParser
import time, prawlimitless
import pymongo
import webbrowser
from threading import Timer
from threading import Thread
from flask import Flask, request
from filter_handler import *
from Target import *

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]
subs = {}
access_information = None
scope = "identity privatemessages read"

app = Flask(__name__)

CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = 'http://127.0.0.1:65010/authorize_callback'
#==================================================End Config======================================================

def kill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."

@app.route('/authorize_callback')
def authorized():
    global access_information
    state = request.args.get('state', '')
    code = request.args.get('code', '')
    access_information = r.get_access_information(code)
    user = r.get_me()
    text = 'Sub Notifications Bot has been successfully started.'
    kill()
    return text
		

#==================================================Botting Functions===============================================
#Update list of subs subscribed to notifications about them
def fetch_subscribed():
	n_subscribed = {}
	c = coll.find()
	for e in c:
		targets = {}
		for s in e['filters'].keys():
			targets[s] = target_from_filter(s,e['filters'][s])
		n_subscribed[e['sub']] = targets
	return n_subscribed

#Check if a comment mentioning a sub meets the threshold
def check_comment(comment,sub,targets,count):
	#Logging
	try:
		print("Checking comment: "+comment.permalink)
	except:
		pass
	try:
		comment.refresh()
	except:
		untrack_notification(comment.name)
		try:
			print("Dropping comment: "+comment.permalink)
			print("Reason: Deleted.")
		except:
			pass
		return
	#If it's been edited, drop it
	if(not mentions_sub(comment.body.lower(),sub[1:])):
		untrack_notification(comment.name)
		try:
			print("Dropping comment: "+comment.permalink)
			print("Reason: Edited.")
		except:
			pass
		return
	#If the threshold is met:
	to_remove = []
	for t in targets:
		try:
			if subs[t[0]][t[1]].check_out(comment):
				print("Notifying "+sub+" they've been mentioned")
				title = 'Your subreddit has been mentioned in /r/' + comment.subreddit.display_name+'!'
				body = comment.permalink+'?context=3\n\n________\n\n'+comment.body+'\n\n________\n\n[^^What ^^is ^^this?](https://www.reddit.com/r/SubNotifications/comments/3dxono/general_information/)'
				#Notify the sub
				r.send_message(subs[t[0]][t[1]].name,title,body)
				to_remove += [t]
		except Exception as e:
			print(e)
			to_remove += [t]
			
	for t in to_remove:
		targets.remove(t)
	
	if(len(targets)>0 and count<24):
		t=Timer(3600, check_comment, [comment,sub,targets,count+1])
		t.daemon=True
		t.start()
	else:
		untrack_notification(comment.name)
		print("Dropping comment: "+comment.permalink)
		print("Reason: All targets notified or expired.")
	
#This bit is to avoid repeated comment checking.
seen = []
def push_to_seen(comment):
	global seen
	seen.insert(0,comment)
	if(len(seen)>10000):
		seen.pop()
		
tracked = []
def track_notification(comment):
	global tracked
	tracked += [comment]
	
def untrack_notification(comment):
	global tracked
	tracked.remove(comment)
	
#This makes sure a sub notification is accurate, and not part of the name of a different sub
def mentions_sub(body,sub):
	result = (sub in body)
	if(result):
		result &= ((body.find(sub) + len(sub) == len(body)) or not (body[body.find(sub) + len(sub)].isalnum() or body[body.find(sub) + len(sub)]=='_'))
	if(result):
		result &= ((body.find(sub)==0) or not (body[body.find(sub)-1].isalnum() or body[body.find(sub) - 1]=='_'))
	return result

def refresh_access():
	while(True):
		time.sleep(540)
		print 'Refreshing Credentials'
		try:
			r.refresh_access_information(access_information['refresh_token'],update_session=True)
			print 'Access refreshed'
		except:
			print 'Refresh failed'
		
#==================================================End Botting Functions===========================================

r = prawlimitless.Reddit('OAuth Notificationier by /u/The1RGood')
r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
webbrowser.open(r.get_authorize_url('DifferentUniqueKey',scope,True))
app.run(debug=False, port=65010)
#amt = Thread(target=refresh_access,args=())
#amt.daemon=True
#amt.start()
#==================================================================================================================
print 'Bot Starting'
offset = 1
while(True):
	try:
		r.refresh_access_information(access_information['refresh_token'],update_session=True)
		subs = fetch_subscribed()
		if(len(subs.keys()) == 0):
			print "Subscriptions list empty! Investigate!"
		comments = r.get_comments('all',limit=(200+offset%101))
		for c in comments:
			if(c.name not in seen and c.name not in tracked):
				push_to_seen(c.name)
				for n in subs.keys():
					if mentions_sub(c.body.lower(),n[1:]) and c.subreddit.display_name.lower() != n[3:]:
						ts = []
						for t in subs[n].keys():
							if(subs[n][t].check_inc(c)):
								print("Comment found mentioning "+n)
								ts += [[n,t]]
						if(len(ts)>0):
							track_notification(c.name)
							Thread(target=check_comment,args=(c,n,ts,0,)).start()
	except KeyboardInterrupt:
		print("Break.")
		break
	except:
		pass
	offset+=1