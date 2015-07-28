import ConfigParser
import pymongo

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]

sub = raw_input('Enter sub name: ')
if(sub[0:2]=='r/'):
	sub = '/'+sub
elif(sub[0:3]!='/r/'):
	sub = '/r/'+sub
	
name = raw_input('Enter subscriber name: ')

karma = int(raw_input('Enter karma: '))

not_user = [] 
excluded = raw_input('Enter user to ignore: ')
while(excluded!=''):
	not_user+=[excluded]
	excluded = raw_input('Enter user to ignore: ')
	
not_subreddit = []
excluded = raw_input('Enter subreddit to ignore: ')
while(excluded!=''):
	not_subreddit+=[excluded]
	excluded = raw_input('Enter subreddit to ignore: ')
	
filters = {}
inc_filters = {}
out_filters = {}

inc_filters['not_user'] = not_user
inc_filters['not_subreddit'] = not_subreddit
out_filters['karma'] = karma

filters['inc_filters'] = inc_filters
filters['out_filters'] = out_filters

coll.find_one_and_update({'sub':sub},{'$set': {'filters.'+name : filters}}, upsert=True)