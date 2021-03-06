class NameTarget():
	#POSSIBLE INC_FILTERS#
	# by_user
	# not_user
	# in_subreddit
	# not_subreddit
	######################
	
	#POSSIBLE OUT_FILTERS#
	# karma
	######################
	
	def __init__(self,name,inc_filters,out_filters):
		self.name = name
		self.inc_filters = inc_filters
		self.out_filters = out_filters
		
	def check_inc(self,comment):
		for f in self.inc_filters.keys():
			if(not self.pass_filter(f,self.inc_filters[f],comment)):
				return False
		return True
		
	def check_out(self,comment):
		for f in self.out_filters.keys():
			if(not self.pass_filter(f,self.out_filters[f],comment)):
				return False
		return True
			
	def pass_filter(self,f,data,comment):
		if(f=='by_user'):
			return comment.author.name.lower() in list(map(lambda name: name.lower(), data))
		if(f=='not_user'):
			return comment.author.name.lower() not in list(map(lambda name: name.lower(), data))
		if(f=='in_subreddit'):
			return comment.subreddit.display_name.lower() in list(map(lambda name: name.lower(), data))
		if(f=='not_subreddit'):
			return comment.subreddit.display_name.lower() not in list(map(lambda name: name.lower(), data))
		if(f=='karma'):
			return comment.score >= data
		return True