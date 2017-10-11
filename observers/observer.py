import abc

class Observer(metaclass=abc.ABCMeta):
	def begin_opportunity_finder(self, depths, fee):
		pass

	def end_opportunity_finder(self):
		pass

	@abc.abstractmethod
	def opportunity(self, item):
		pass		