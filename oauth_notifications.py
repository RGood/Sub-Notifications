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

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]
subscribed = {}
access_information = None
scope = "identity privatemessages"

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
		n_subscribed[e['name']] = e['karma']
	return n_subscribed

#Check if a comment mentioning a sub meets the threshold
def check_comment(comment,sub,count):
	#Logging
	print("Hour elapsed. Checking comment: "+comment.permalink)
	try:
		comment.refresh()
	except:
		print("Dropping comment: "+comment.permalink)
		print("Reason: Deleted.")
		untrack_notification(comment.name)
	#If it's been edited, drop it
	if(not mentions_sub(comment.body.lower(),sub[1:])):
		print("Dropping comment: "+comment.permalink)
		print("Reason: Edited.")
		untrack_notification(comment.name)
		return
	#If the threshold is met:
	if comment.ups > subscribed[sub]:
		body = comment.permalink+'?context=3\n\n________\n\n[^^What ^^is ^^this?](https://www.reddit.com/r/SubNotifications/comments/3dxono/general_information/)'
		#Notify the sub
		Thread(target=r.send_message,args=(sub,body,)).start()
		#Logging
		untrack_notification(comment.name)
		print("Notifying "+sub+" they've been mentioned")
	#If a comment is less than 24 hours old and doesn't meet the threshold
	elif(count < 24):
		#Check again in an hour
		t=Timer(3600, check_comment, [comment,sub,count+1])
		t.daemon=True
		t.start()
	#If a comment is 1 day old without meeting the threshold, it is dropped.
	else:
		print("Dropping comment: "+comment.permalink)
		print("Reason: Expired.")
		untrack_notification(comment.name)

#Schedule a comment to be checked
def schedule_check(comment,sub):
	t=Timer(3600, check_comment, [comment,sub,0])
	t.daemon=True
	t.start()
	print("Comment added to queue: "+comment.permalink)
	
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
	
def increment_count(sub):
	res = coll.find_one({'name':n})
	count = 0
	if(res != None):
		try:
			count = res['count']+1
		except Exception:
			count=1
		coll.update_one({'name':res['name']},{'$set':{'count':count}})
	
#This makes sure a sub notification is accurate, and not part of the name of a different sub
def mentions_sub(body,sub):
	result = (sub in body)
	if(result):
		result &= ((body.find(sub) + len(sub) == len(body)) or not (body[body.find(sub) + len(sub)].isalnum() or body[body.find(sub) + len(sub)]=='_'))
	if(result):
		result &= ((body.find(sub)==0) or not (body[body.find(sub)-1].isalnum() or body[body.find(sub) - 1]=='_'))
	return result

def refresh_access():
	global access_information
	while(True):
		time.sleep(1800)
		print 'Refreshing Credentials'
		r.refresh_access_information(access_information['refresh_token'],update_session=True)
		print 'Access refreshed'
		
#==================================================End Botting Functions===========================================

r = prawlimitless.Reddit('OAuth Notificationier by /u/The1RGood')
r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
webbrowser.open(r.get_authorize_url('DifferentUniqueKey',scope,True))
app.run(debug=False, port=65010)
amt = Thread(target=refresh_access,args=())
amt.daemon=True
amt.start()
#==================================================================================================================
print 'Bot Starting'
offset = 0
while(True):
	try:
		subscribed = fetch_subscribed()
		if(len(subscribed.keys()) == 0):
			print "Subscriptions list empty! Investigate!"
		comments = prawlimitless.helpers.comment_stream(r,'all',limit=200)
		for c in comments:
			if(c.name not in seen and c.name not in tracked):
				push_to_seen(c.name)
				for n in subscribed.keys():
					if mentions_sub(c.body.lower(),n[1:]) and c.subreddit.display_name.lower() != n[3:]:
						track_notification(c.name)
						Thread(target=increment_count,args=(n,)).start()
						print("Comment found mentioning "+n)
						schedule_check(c,n)
	except KeyboardInterrupt:
		print("Break.")
		break
	except Exception as e:
		print(e)
	offset+=1