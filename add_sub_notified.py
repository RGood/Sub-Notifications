import pymongo
import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read('sn_info.cfg')

client = pymongo.MongoClient(Config.get('Mongo Info','conn_str'))
db = client[Config.get('Mongo Info','database')]
coll = db[Config.get('Mongo Info','collection')]

name = raw_input('Enter sub name: ')
if(name[0:2]=='r/'):
	name = '/'+name
elif(name[0:3]!='/r/'):
	name = '/r/'+name

karma = int(raw_input('Enter karma: '))

sub = {}
sub['name'] = name.lower()
sub['karma'] = karma
sub['count'] = 0

coll.update({'name':name},sub,upsert=True)