def create_filter(inc,out):
	filters = {}
	filters['inc_filters'] = inc
	filters['out_filters'] = out
	return filters
	
def get_default_inc():
	filters = {}
	filters['not_user'] = ['automoderator','totesmessenger']
	return filters

def get_default_out():
	filters = {}
	filters['karma'] = 1
	return filters