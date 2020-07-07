#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Unit test.

written by pyLeo.
"""
# # # Import current path.
import sys

sys.path.append('..')
# # # Analog Function.
from loguru import logger
from accessor.request_crawler import RequestCrawler
from accessor.selenium_crawler import SeleniumCrawler
from booster.aes_formatter import AESFormatter
from booster.basic_formatter import BasicFormatter
from booster.basic_parser import BasicParser
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser
from hammer.data_tester import a

logger.add("unit_tester.log", colorize=True, enqueue=True,
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

if __name__ == '__main__':
	RC = RequestCrawler()
	SC = SeleniumCrawler()
	AP = AESFormatter()
	BF = BasicFormatter()
	BP = BasicParser()
	DF = DateFormatter()
	DP = DomParser()
	AP.logger = logger
	RC.logger = logger
	SC.logger = logger
	BF.logger = logger
	BP.logger = logger
	DF.logger = logger
	DP.logger = logger
	
	import random
	islocal = random.randint(0, 1)
	