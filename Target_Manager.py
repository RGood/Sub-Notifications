import time

class TargetManager():
	
	def __init__(self,comment,sub):
		self.comment = comment
		self.sub = sub
		self.targets = []
		self.count = 0
		self.last_check = 0
		
	def add_target(self,target):
		self.targets+=[target]
		
	def get_targets(self):
		return self.targets
		
	def remove_target(self,target):
		try:
			self.targets.remove(target)
		except ValueError:
			pass
		
	def target_count(self):
		return len(self.targets)
		
	def increment(self):
		self.count+=1
		
	def get_count(self):
		return self.count
		
	def get_sub(self):
		return self.sub
		
	def get_comment(self):
		return self.comment
		
	def reset_time(self):
		self.last_check = time.time()
		
	def get_time(self):
		return self.last_check