import filter_creation
from Target import NameTarget

def target_from_filter(name,filters):
	return NameTarget(name,filters['inc_filters'],filters['out_filters'])
	
targets = {}
def get_target(sub,name):
	global targets
	return targets[sub][name]
	
def load_targets():
	pass