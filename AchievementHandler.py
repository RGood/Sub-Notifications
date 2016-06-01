class AchievementHandler():
	
	def __init__(self,name,sub,coll):
		self.coll = coll
		self.name = name
		self.sub = sub
		
	def get_record(self):
		record = coll.find_one({"name":self.name,"sub":self.sub})
		if(record):
			return record
		else:
			record = {
				"name":self.name,
				"sub":self.sub,
				"notifications":0,
				"replies":0,
				"config":0,
				"mentions":{},
				"gilded":False,
				"mod":False,
				"admin":False,
				"controversial":False
			}
			return coll.insert_one(record)
			
	def save_record(self,record):
		coll.update({"name":self.name,"sub":self.sub},record,upsert=False)	
		
	def user_mention(self,user):
		record = get_record()
		try:
			record['mentions']['user']+=1
		except KeyError:
			record['mentions']['user'] = 1
		save_record(record)
		value = record['mentions']['user']
		if(value==10):
			return {
				'type':'Single-User',
				'name':"Obsession I",
				'description': "/u/"+user+" has mentioned your subreddit "+str(value)+" times."
			}
		elif(value==25):
			return {
				'type':'Single-User',
				'name':"Obsession II",
				'description': "/u/"+user+" has mentioned your subreddit "+str(value)+" times."
			}
		elif(value==50):
			return {
				'type':'Single-User',
				'name':"Obsession III",
				'description': "/u/"+user+" has mentioned your subreddit "+str(value)+" times."
			}
		elif(value==100):
			return {
				'type':'Single-User',
				'name':"Obsession IV",
				'description': "/u/"+user+" has mentioned your subreddit "+str(value)+" times."
			}
		else:
			return None
		
		
	def add_notification(self):
		record = get_record
		record['notifications']+=1
		save_record(record)
		value = record['notifications']
		if(value==10):
			return {
				'type':'Notifications',
				'name':'Ears Burning I',
				'description':"You have received "+str(value)+" notifications."
			}
		elif(value==100):
			return {
				'type':'Notifications',
				'name':'Ears Burning II',
				'description':"You have received "+str(value)+" notifications."
			}
		elif(value==1000):
			return {
				'type':'Notifications',
				'name':'Ears Burning III',
				'description':"You have received "+str(value)+" notifications."
			}
		elif(value==5000):
			return {
				'type':'Notifications',
				'name':'Ears Burning IV',
				'description':"You have received "+str(value)+" notifications."
			}
		else:
			return None
		
	def add_reply(self):
		record = get_record()
		record['replies']+=1
		save_record(record)
		#Check value and return possible achievement
		value = record['replies']
		if(value==5):
			'type':'Reply',
			'name':'Chatty I',
			'description':"You have sent "+str(value)+" replies to subreddit notifications."
		elif(value==50):
			'type':'Reply',
			'name':'Chatty II',
			'description':"You have sent "+str(value)+" replies to subreddit notifications."
		elif(value==500):
			'type':'Reply',
			'name':'Chatty III',
			'description':"You have sent "+str(value)+" replies to subreddit notifications."
		elif(value==5000):
			'type':'Reply',
			'name':'Chatty IV',
			'description':"You have sent "+str(value)+" replies to subreddit notifications."
		elif(value==10000):
			'type':'Reply',
			'name':'Chatty IV',
			'description':"You have sent "+str(value)+" replies to subreddit notifications."
		else:
			return None
		
	def add_config(self):
		record = get_record()
		record['config']+=1
		save_record(record)
		#Check value and return possible achievement
		value = record['config']
		if(value==5):
			'type':'Config',
			'name':'Stay With The Times I',
			'description':"You have updated the config "+str(value)+" times."
		elif(value==10):
			'type':'Config',
			'name':'Stay With The Times II',
			'description':"You have updated the config "+str(value)+" times."
		elif(value==50):
			'type':'Config',
			'name':'Stay With The Times III',
			'description':"You have updated the config "+str(value)+" times."
		elif(value==100):
			'type':'Config',
			'name':'Stay With The Times IV',
			'description':"You have updated the config "+str(value)+" times."
		else:
			return None
		
		
	def flag_gilded(self):
		record = get_record()
		if(!record['gilded']):
			record['gilded'] = True
			save_record(record)
			#Return achievement
			return {
				'type':'Gild',
				'name':'Golden Mention',
				'description':'Your subreddit has been mentioned in a gilded comment.'
			}
			
	def flag_mod(self):
		record = get_record()
		if(!record['mod']):
			record['mod'] = True
			save_record(record)
			return {
				'type':'Mod',
				'name':'Mod Mention',
				'description':'Your subreddit has been mentioned by a distinguished moderator comment.'
			}
			
	def flag_admin(self):
		record = get_record()
		if(!record['admin']):
			record['admin'] = True
			save_record(record)
			#Return achievement
			return {
				'type':'Admin',
				'name':'Serious Business',
				'description':'Your subreddit has been mentioned by a distinguished administrator comment.'
			}
			
	def flag_controversial(self):
		record = get_record()
		if(!record['controversial']):
			record['controversial'] = True
			save_record(record)
			#Return achievement
			return {
				'type':'Controversial',
				'name':'Not The Best PR',
				'description':'Your subreddit has been mentioned in a controversial comment.'
			}