import pymongo
import sys
import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]

if(len(sys.argv) > 1):
	name = sys.argv[1]
else:
	name = raw_input('Enter sub name: ')
if(name[0:2]=='r/'):
	name = '/'+name
elif(name[0:3]!='/r/'):
	name = '/r/'+name

c = coll.find_one({'name':name})
if(c != None):
	print str(c['karma']) + " karma required for "+name
	try:
		print str(c['count']) + " mentions since subscription."
	except Exception:
		print "0 mentions since subscription."
else:
	print "That sub is not subscribed."