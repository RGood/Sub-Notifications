# oauth PRAW template by /u/The1RGood #
#==================================================Config stuff====================================================
import ConfigParser
import time, praw
import webbrowser
import pymongo
import json
from flask import Flask, request
from threading import Thread

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]
subs = {}
access_information = None
scope = "identity privatemessages read"

access_information = ''
scope = "identity privatemessages submit read" #SET THIS. SEE http://praw.readthedocs.org/en/latest/pages/oauth.html#oauth-scopes FOR DETAILS.
#==================================================End Config======================================================
#==================================================OAUTH APPROVAL==================================================
app = Flask(__name__)

CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = 'http://127.0.0.1:65010/authorize_callback'

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
	text = 'Bot successfully started.'
	kill()
	return text
	
def refresh_access():
	while(True):
		time.sleep(1800)
		r.refresh_access_information(access_information['refresh_token'])
	
r = praw.Reddit('OAuth FLASK Template Script'
                'https://praw.readthedocs.org/en/latest/'
                'pages/oauth.html for more info.')
r.set_oauth_app_info(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
webbrowser.open(r.get_authorize_url('DifferentUniqueKey',scope,True))
app.run(debug=False, port=65010)
#amt = Thread(target=refresh_access,args=())
#amt.daemon=True
#amt.start()
#==================================================END OAUTH APPROVAL-=============================================
def push_to_seen(m):
	seen.insert(0,m)
	if(len(seen)>100):
		seen.pop()

print 'Buffering old mail...'
seen = []
mail = r.get_messages(limit=50)
for m in mail:
	push_to_seen(m.name)
	
print('Scanning.')
running = True
while(running):
	try:
		r.refresh_access_information(access_information['refresh_token'])
		mail = r.get_messages(limit=25)
		for m in mail:
			if(m.name not in seen):
				push_to_seen(m.name)
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
						
						print "Filters made"
						
						target = ("/r/" + m.subreddit.display_name) if (m.subreddit != None) else (m.author.name)
						print("Subscribing " + target + " to " + body['subreddit'])
						coll.find_one_and_update({'sub':"/r/"+body['subreddit'].lower()},{'$set': {'filters.'+target : filters}}, upsert=True)
						m.reply("You have been successfully subscribed.")
					except:
						print("Error parsing subscribe request.")
						m.reply("There was an error processing your request. Please check the JSON syntax and try again.\n\nIf you cannot resolve the problem, please message /u/The1RGood.")
	except KeyboardInterrupt:
		print("Break.")
		break
	except:
		print("Err state. Restarting.")