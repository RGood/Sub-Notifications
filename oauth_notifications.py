# oauth_notifications.py  #
# Written by /u/The1RGood #
###########################
#==================================================Config stuff====================================================
import configparser
import time, praw
import pymongo
import webbrowser
from threading import Timer
from threading import Thread
from flask import Flask, request
from filter_handler import *
from Target import *

Config = configparser.ConfigParser()
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
    return("Shutting down...")

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
	except Exception as e:
		untrack_notification(comment.name)
		try:
			print("Dropping comment: "+comment.permalink)
			print(e)
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
				body = 'Author: /u/'+comment.author.name +'\n\n[Link]('+comment.permalink+'?context=3)\n\n___\n\n'+comment.body+'\n\n___\n\n[^- ^What ^is ^this?](https://www.reddit.com/r/SubNotifications/comments/3dxono/general_information/)\n\n[^- ^Contact ^My ^Creator](https://www.reddit.com/message/compose/?to=The1RGood&subject=Sub%20Notifications%20Bot)'
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
seen_mail = []
def push_to_mail(comment):
	global seen_mail
	seen_mail.insert(0,comment)
	if(len(seen_mail)>10000):
		seen_mail.pop()

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
	
def handle_mail():
	mail = r.get_messages(limit=25)
	for m in mail:
		if(m.name not in seen_mail):
			push_to_mail(m.name)
			if m.subject == "Action: Unsubscribe" and m.parent_id == None:
				body = None
				try:
					body = json.loads(m.body)
					target = ("/r/" + m.subreddit.display_name) if (m.subreddit != None) else (m.author.name)
					print("Unsubscribing " + target + " from " + body['subreddit'])
					coll.update({'sub':"/r/"+body['subreddit'].lower()},{'$unset' : {'filters.'+target:""}})
					m.reply("You have been successfully unsubscribed.")
				except:
					print("Error parsing unsubscribe request.")
					m.reply("There was an error processing your request. Please check the JSON syntax and try again.\n\nIf you cannot resolve the problem, please message /u/The1RGood.")
			elif m.subject == "Action: Subscribe" and m.parent_id == None:
				body = None
				try:
					body = json.loads(m.body)
					
					filters = {}
					inc_filters = {}
					out_filters = {}
					
					inc_filters['not_user'] = body['filter-users']
					inc_filters['not_subreddit'] = body['filter-subreddits']
					out_filters['karma'] = body['karma']
					
					filters['inc_filters'] = inc_filters
					filters['out_filters'] = out_filters
					
					print("Filters made")
					
					target = ("/r/" + m.subreddit.display_name) if (m.subreddit != None) else (m.author.name)
					print("Subscribing " + target + " to " + body['subreddit'])
					coll.find_one_and_update({'sub':"/r/"+body['subreddit'].lower()},{'$set': {'filters.'+target : filters}}, upsert=True)
					m.reply("You have been successfully subscribed.")
				except:
					print("Error parsing subscribe request.")
					m.reply("There was an error processing your request. Please check the JSON syntax and try again.\n\nIf you cannot resolve the problem, please message /u/The1RGood.")
		
#==================================================End Botting Functions===========================================

r = praw.Reddit('OAuth Notificationier by /u/The1RGood')
r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
webbrowser.open(r.get_authorize_url('DifferentUniqueKey',scope,True))
app.run(debug=False, port=65010)
#==================================================================================================================
mail = r.get_messages(limit=25)
for m in mail:
	push_to_mail(m.name)

print('Bot Starting')
offset = 0
while(True):
	try:
		r.refresh_access_information(access_information['refresh_token'],update_session=True)
		handle_mail()
		subs = fetch_subscribed()
		if(len(subs.keys()) == 0):
			print("Subscriptions list empty! Investigate!")
		comments = r.get_comments('all',limit=(200+offset%101))
		#comments = praw.helpers.comment_stream('r','all',limit=200)
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