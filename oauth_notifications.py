# oauth_notifications.py  #
# Written by /u/The1RGood #
###########################
#==================================================Config stuff====================================================
import configparser
import time
import praw
from praw.handlers import MultiprocessHandler
import pymongo
import webbrowser
from threading import Timer
from threading import Thread
from flask import Flask, request
from filter_handler import *
from Target import *
from Target_Manager import *
import json
import sys, traceback
import re
from AchievementHandler import *

Config = configparser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]
subs = {}
achievements = []
access_information = None
scope = "identity privatemessages read"
ac = db['Achievements']

app = Flask(__name__)

CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = Config.get('Reddit Access','callback')
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
    print(code)
    try:
        r.get_access_information(code)
    except:
        traceback.print_exc(file=sys.stdout)
    user = r.get_me()
    text = 'Bot started on /u/' + user.name
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
#comment = get_comment
#sub = get_sub
#targets = get_targets
#count = increment / get_count
def check_comment(target_manager):
	#Logging
	try:
		print("Checking comment: "+target_manager.get_comment().permalink)
	except:
		traceback.print_exc(file=sys.stdout)
	try:
		if(target_manager.get_count()>0):
			target_manager.get_comment().refresh()
	except Exception as e:
		try:
			print("Dropping comment: "+target_manager.get_comment().permalink)
			print("Could not refresh.")
			traceback.print_exc(file=sys.stdout)
		except:
			pass
		return True
	#If it's been edited, drop it
	if(not mentions_sub(target_manager.get_comment().body.lower(),target_manager.get_sub()[1:])):
		try:
			print("Dropping comment: "+target_manager.get_comment().permalink)
			print("Reason: Edited.")
		except:
			pass
		return True
	#If the threshold is met:
	to_remove = []
	for t in target_manager.get_targets():
		try:
			if subs[t[0]][t[1]].check_out(target_manager.get_comment()):
				print("Sending notification about"+target_manager.get_sub())
				title = 'Your subreddit has been mentioned in /r/' + target_manager.get_comment().subreddit.display_name+'!'
				body = 'Author: /u/'+target_manager.get_comment().author.name +'\n\n['+target_manager.get_comment().submission.title+']('+target_manager.get_comment().permalink+'?context=3)\n\n___\n\n'+target_manager.get_comment().body+'\n\n___\n\n[^- ^What ^is ^this?](https://www.reddit.com/r/SubNotifications/comments/3dxono/general_information/)\n\n[^- ^Contact ^My ^Creator](https://www.reddit.com/message/compose/?to=The1RGood&subject=Sub%20Notifications%20Bot)'
				#Notify the sub
				r.send_message(subs[t[0]][t[1]].name,title,body)
				res = AchievementHandler(subs[t[0]][t[1]].name,target_manager.get_sub(),ac).add_notification()
				if(res):
					achievements+=[{
						"name":subs[t[0]][t[1]].name,
						"sub":target_manager.get_sub(),
						"achievement":res
					}]
				res = AchievementHandler(subs[t[0]][t[1]].name,target_manager.get_sub(),ac).user_mention(target_manager.get_comment().author.name)
				if(res):
					achievements+=[{
						"name":subs[t[0]][t[1]].name,
						"sub":target_manager.get_sub(),
						"achievement":res
					}]
				to_remove += [t]
		except:
			traceback.print_exc(file=sys.stdout)
			to_remove += [t]
			
	for t in to_remove:
		target_manager.remove_target(t)
	
	if(target_manager.target_count()>0 and target_manager.get_count()<24):
		target_manager.increment()
		return False
	else:
		print("Dropping comment: "+target_manager.get_comment().permalink)
		print("Reason: All targets notified or expired.")
		return True
	
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
	
#This makes sure a sub notification is accurate, and not part of the name of a different sub
def mentions_sub(body,sub):
	result = (sub in body)
	if(result):
		result &= ((body.find(sub) + len(sub) == len(body)) or not (body[body.find(sub) + len(sub)].isalnum() or body[body.find(sub) + len(sub)]=='_'))
	if(result):
		result &= ((body.find(sub)==0) or not (body[body.find(sub)-1].isalnum() or body[body.find(sub) - 1]=='_'))
	return result
	
def handle_mail():
	regex = "[a-zA-Z0-9\s_-]*"
	mail = r.get_inbox(limit=25)
	for m in mail:
		if(m.name not in seen_mail):
			push_to_mail(m.name)
			if m.subject == "Action: Unsubscribe" and m.parent_id == None:
				body = None
				try:
					body = json.loads(m.body)
					if(not re.fullmatch(regex,body['subreddit'])):
						m.reply('Unable to parse subreddit. Please double-check the subreddit(s) being unsubscribed from.')
						return
						
					target = ("/r/" + m.subreddit.display_name.lower()) if (m.subreddit != None) else (m.author.name)
					print("Unsubscribing " + target + " from " + body['subreddit'])
					subreddits = body['subreddit'].split(' ')
					for s in subreddits:
						coll.update({'sub':"/r/"+body['subreddit'].lower()},{'$unset' : {'filters.'+target:""}})
					names = ""
					for s in subreddits:
						names+=s+"    \n"
					m.reply("You have been successfully unsubscribed from the following subreddit" + (':\n\n' if len(subreddits)==1 else 's:\n\n') + names)
				except:
					print("Error parsing unsubscribe request.")
					m.reply("There was an error processing your request. Please check the JSON syntax and try again.\n\nIf you cannot resolve the problem, please message /u/The1RGood.")
			elif m.subject == "Action: Subscribe" and m.parent_id == None:
				body = None
				try:
					body = json.loads(m.body.replace('\n', ''))
					if(not re.fullmatch(regex,body['subreddit'])):
						m.reply('Unable to parse subreddit. Please double-check the subreddit(s) being subscribed to.')
						return
						
					filters = {}
					inc_filters = {}
					out_filters = {}
					
					inc_filters['not_user'] = body['filter-users']
					inc_filters['not_subreddit'] = body['filter-subreddits']
					out_filters['karma'] = body['karma']
					
					filters['inc_filters'] = inc_filters
					filters['out_filters'] = out_filters
					
					print("Filters made")
					
					target = ("/r/" + m.subreddit.display_name.lower()) if (m.subreddit != None) else (m.author.name)
					print("Subscribing " + target + " to " + body['subreddit'])
					res = AchievementHandler(target,"/r/"+body['subreddit'],ac).add_config()
					if(res):
						achievements+=[{
							"name":target,
							"sub":"/r/"+body['subreddit'],
							"achievement":res
						}]
					subreddits = body['subreddit'].split(' ')
					for s in subreddits:
						coll.find_one_and_update({'sub':"/r/"+s.lower()},{'$set': {'filters.'+target : filters}}, upsert=True)
					names = ""
					for s in subreddits:
						names+=s+"    \n"
					m.reply("You have been successfully subscribed to the following subreddit" + (':\n\n' if len(subreddits)==1 else 's:\n\n') + names)
				except:
					print("Error parsing subscribe request.")
					m.reply("There was an error processing your request. Please check the JSON syntax and try again.\n\nIf you cannot resolve the problem, please message /u/The1RGood.")
			else:
				if(m.subreddit):
					res = AchievementHandler("/r/" + m.subreddit.display_name,"/r/"+body['subreddit'],ac).add_reply()
					if(res):
						achievements+=[{
							"name":"/r/" + m.subreddit.display_name,
							"sub":"/r/"+body['subreddit'],
							"achievement":res
						}]

def handle_comments(comments):
	to_remove = []
	for c in comments:
		if((c.get_time == 0) or (c.get_time() < (time.time() - 3600))):
			c.reset_time()
			result = check_comment(c)
			if(result):
				to_remove+=[c]
	for c in to_remove:
		comments.remove(c)

#==================================================End Botting Functions===========================================
#handler = MultiprocessHandler('localhost', 10101)
r = praw.Reddit('OAuth Notificationier by /u/The1RGood',api_request_delay=0.66)
r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
print(r.get_authorize_url('DifferentUniqueKey',scope,True))
app.run(debug=False, port=65010)
#==================================================================================================================
def main():
	global subs
	mail = r.get_inbox(limit=25)
	for m in mail:
		push_to_mail(m.name)
	
	active_comments = []
	last_active = 0
	
	print('Bot Starting')
	offset = 0
	while(True):
		try:
			handle_mail()
			subs = fetch_subscribed()
			if(len(subs.keys()) == 0):
				print("Subscriptions list empty! Investigate!")
			#comments = r.get_comments('all',limit=(200+offset%101))
			comments = r.get_content('https://www.reddit.com/comments',limit=(200+offset%101))
			for c in comments:
				if(c.name not in seen):
					push_to_seen(c.name)
					for n in subs.keys():
						if mentions_sub(c.body.lower(),n[1:]) and c.subreddit.display_name.lower() != n[3:]:
							tm = TargetManager(c,n)
							for t in subs[n].keys():
								if(subs[n][t].check_inc(c)):
									print("Comment found mentioning "+n)
									tm.add_target([n,t])
							if(tm.target_count()>0):
								active_comments += [tm]
			handle_comments(active_comments)
			if(len(active_comments)!=last_active):
				last_active = len(active_comments)
				print("There are " + str(len(active_comments)) + " active comments.")
		except KeyboardInterrupt:
			print("Break.")
			break
		except:
			traceback.print_exc(file=sys.stdout)
			#pass
		offset+=1
		
if __name__ == '__main__':
	main()
