import logging
# import argparse
import sys
# from triangular import Triangular
from single import Single

class Run():
	def __init__(self):	
		pass

	def create_triangular(self):
		self.triangular = Triangular()	

	def exec_command(self):
		# self.create_triangular()
		# self.triangular.loop()
		self.single = Single()
		self.single.loop()

	def init_logger(self):
		level = logging.DEBUG
		logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)	

	def main(self):
		self.init_logger()
		self.exec_command()	


def main():
	cli = Run()
	cli.main()

if __name__ == '__main__':
	main()	

