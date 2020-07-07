# -*- coding: utf-8 -*-
# =============================================================================
# Copyright (c) 2018-, pyLeo Developer. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
"""The scraper is use for website process interaction."""
from accessor.request_worker import RequestWorker
from accessor.request_crawler import RequestCrawler
from booster.aes_formatter import AESFormatter
from booster.basic_formatter import BasicFormatter
from booster.basic_parser import BasicParser
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser
from fortifier.persqn_refactor import CFRefactor, CPRefactor


class PersQNScraper(RequestWorker):
	"""AK采集器

	"""
	
	def __init__(self) -> None:
		RequestWorker.__init__(self)
		self.RCR = RequestCrawler()  # 请求爬行器。
		self.AFR = AESFormatter()  # AES格式器。
		self.BFR = BasicFormatter()  # 基础格式器。
		self.BPR = BasicParser()  # 基础解析器。
		self.CFR = CFRefactor()  # 回调格式器。
		self.CPR = CPRefactor(False)  # 接入解析器。
		self.DFR = DateFormatter()  # 日期格式器。
		self.DPR = DomParser()  # 文档解析器。
		
		self.departure_name = ""
		self.arrival_name = ""
		self.base_header = {}
		
		self.total_price: float = 0.0  # 总价
		self.record: str = ""  # 票号
	
	def init_to_assignment(self) -> bool:
		"""Assignment to logger. 赋值日志。

		Returns:
			bool
		"""
		self.RCR.logger = self.logger
		self.AFR.logger = self.logger
		self.BFR.logger = self.logger
		self.BPR.logger = self.logger
		self.CFR.logger = self.logger
		self.CPR.logger = self.logger
		self.DFR.logger = self.logger
		self.DPR.logger = self.logger
		return True
	
	def process_to_main(self, process_dict: dict = None) -> dict:
		"""Main process. 主程序入口。

		Args:
			process_dict (dict): Parameters. 传参。

		Returns:
			dict
		"""
		task_id = process_dict.get("task_id")
		log_path = process_dict.get("log_path")
		source_dict = process_dict.get("source_dict")
		enable_proxy = process_dict.get("enable_proxy")
		address = process_dict.get("address")
		self.retry_count = process_dict.get("retry_count")
		if not self.retry_count:
			self.retry_count = 1
		# # # 初始化日志。
		self.init_to_logger(task_id, log_path)
		self.init_to_assignment()
		# # # 同步返回参数。
		self.callback_data = self.CFR.format_to_async()
		# # # 解析接口参数。
		if not self.CPR.parse_to_interface(source_dict):
			self.callback_data['msg'] = "请通知技术检查接口数据参数。"
			return self.callback_data
		self.logger.info(source_dict)
		# # # 启动爬虫，建立header。
		self.RCR.set_to_session()
		self.RCR.set_to_proxy(enable_proxy, address)
		self.user_agent, self.init_header = self.RCR.build_to_header("Chrome")
		
		if self.process_to_name():
			if self.process_to_index():
		# if self.get_cityName():
		# 		if self.query_from_price():
		# 			if self.query_from_passengers():
		# 				if self.query_from_pricetag():
		# 					if self.query_from_token():
		# 						if self.post_token():
		# 							if self.get_order():
										self.process_to_return()
										self.logger.removeHandler(self.handler)
										return self.callback_data
		# # # 错误返回。
		self.callback_data["occupyCabinId"] = self.CPR.task_id
		self.callback_data['msg'] = self.callback_msg
		# self.callback_data['msg'] = "解决问题中，请手工站位。"
		self.callback_data["carrierAccount"] = ""
		self.callback_data['carrierAccountAgent'] = self.CPR.username
		self.logger.info(self.callback_data)
		self.logger.removeHandler(self.handler)
		return self.callback_data
	
	def process_to_name(self):
		self.RCR.url = 'https://www.qunar.com/suggest/livesearch2.jsp'
		self.RCR.param_data = (
			('lang', 'zh'),
			('q', self.CPR.departure_code),
			('sa', 'true'),
			('ver', '1'),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Host": "www.qunar.com",
			"Upgrade-Insecure-Requests": "1",
		})
		self.RCR.post_data = None
		if self.RCR.request_to_get("json"):
			result = self.RCR.page_source.get("result")
			if result:
				for i in result:
					if i.get("code") == self.CPR.departure_code:
						self.departure_name = i.get("key")
						break
				self.RCR.url = 'https://www.qunar.com/suggest/livesearch2.jsp'
				self.RCR.param_data = (
					('lang', 'zh'),
					('q', self.CPR.arrival_code),
					('sa', 'true'),
					('ver', '1'),
				)
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Host": "www.qunar.com",
					"Upgrade-Insecure-Requests": "1",
				})
				self.RCR.post_data = None
				if self.RCR.request_to_get("json"):
					result = self.RCR.page_source.get("result")
					if result:
						for i in result:
							if i.get("code") == self.CPR.arrival_code:
								self.arrival_name = i.get("key")
								break
						return True
			
		self.logger.info(f"获取航站名字失败(*>﹏<*)【name】")
		self.callback_msg = "获取航站名字失败"
		return False
	
	def process_to_index(self, count: int = 0, max_count: int = 1) -> bool:
		"""Index process. 首页过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
		if count >= max_count:
			return False
		else:
			# # # # 更新超时时间。
			# self.RCR.timeout = 10
			# # # # 请求接口服务。
			# self.RCR.url = 'http://119.3.234.171:33334/produce/wn/'
			# self.RCR.param_data = None
			# self.RCR.header = None
			# self.RCR.post_data = {"wn": "header"}
			# if not self.RCR.request_to_post("json", "json"):
			# 	self.logger.info(f"请求刷值地址失败(*>﹏<*)【119.3.234.171:33334】")
			# 	self.callback_msg = "请求刷值地址失败，请通知技术检查程序。"
			# 	return self.process_to_index(count + 1, max_count)
			# # # # 获取abck。
			# value = self.RCR.page_source.get("value")
			# if not value:
			# 	self.logger.info(f"刷值数量不够用(*>﹏<*)【119.3.234.171:33334】")
			# 	self.callback_msg = "刷值数量不够用，请通知技术检查程序。"
			# 	return self.process_to_index(count + 1, max_count)
			value = "{'accept': 'text/javascript, text/html, application/xml, text/xml, */*', 'x-requested-with': 'XMLHttpRequest', 'app': '0%2C0%2C%2C0', 'pre': 'd6640a8b-d84129-294af873-70b4e145-13ff1932e3d2', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.3494.0 Safari/537.36', 'content-type': 'application/x-www-form-urlencoded', 'cookie': 'QN1=00000d00306c2025e430fe54; QN300=organic; QN99=3845; QN205=organic; QN277=organic; csrfToken=GHPGk7869bi62PfkiGoAexB5TKgjd8UJ; QN269=6EB57AA053B311EA91F1FA163E10E623; QN601=536815699ebdd34e5bf2ae63fa5f6e46; QN163=0; QN667=B; QN48=f39bf5f1-0e49-4542-8921-4e4e0a7ad0a8; fid=3997ca83-d8af-49f8-84b6-1f2358f361bc; SplitEnv=D; F235=1582184086986; QN267=3129464094a96b800; QN621=fr%3Dqunarindex; Alina=c6dbcc85-09cb23-8142f460-3982d706-133bc4391087; QunarGlobal=10.88.67.22_-3109e6c5_17060ef6d9b_-3c6f%7C1582184089020; quinn=7892ab520d50eab5fe00b3bed3d06bed5f064b7fb0a24152df845e49a7729261e2b454c55723aa1ec728bcc339293134; _abck=6bf0e2f3-ddc2-4bbc-8bb7-a051283990e9~0~1582184089104~-1~-1~-1; QN271=0ff1972e-413b-4d1e-81bd-6974bf422c65; QN170=101.22.59.80_211061_0_MxVwCqOng7CIZYjmKA5w2ydEh6unf7kJoPF%2F87U4aB0%3D', 'referer': 'https://flight.qunar.com/site/oneway_list_inter.htm?searchDepartureAirport=%E5%93%88%E5%B0%94%E6%BB%A8&searchArrivalAirport=%E5%8F%B0%E5%8C%97&searchDepartureTime=2020-03-06&searchArrivalTime=2020-03-13&nextNDays=0&startSearch=true&fromCode=HRB&toCode=TPE&from=qunarindex&lowestPrice=null&favoriteKey=&showTotalPr=null&adultNum=1&childNum=0&cabinClass='}"

			# # # 重新整理header
			self.base_header = self.BPR.parse_to_eval(value)
			# if self.base_header:
			# 	self.base_header['Referer'] = ""
			# 	self.base_header['User-Agent'] = ""
			# 	self.base_header.pop("Referer")
			# 	self.base_header.pop("User-Agent")


			# print(self.base_header['pre'])
			# print(self.base_header['referer'])
			# print(self.base_header['es'])
			app = self.base_header['app']
			pre = self.base_header['pre']
			print(app, pre)
			b = self.base_header['cookie']
			c = b.split("; ")
			for i in c:
				d, temp_list = self.BPR.parse_to_regex("(.*?)=", i)
				e, temp_list = self.BPR.parse_to_regex(".*?=(.*)", i)
				self.RCR.set_to_cookies(True, [{"name": d, "value": e, "domain": ".qunar.com", "path": "/"}])


			a = "https://flight.qunar.com/touch/api/inter/wwwsearch?depCity=%E5%93%88%E5%B0%94%E6%BB%A8&arrCity=%E5%8F%B0%E5%8C%97&depDate=2020-03-06&adultNum=1&childNum=0&ex_track=&from=qunarindex&carrier=&queryId=10.88.67.22%3Al%3A-3109e6c5%3A17060ef6d9b%3A-3c5a&es=DJiaxi%2BCmavqWiqCaxv%2BaifCB7vqmiUCDaV%2FxJxqCii75JWC%7C1582181677867&_v=8&st=1582184089214"

			b = self.BPR.parse_to_params(a)
			c = dict(b)
			query_id = c['queryId']
			es = c['es']
			st = c['st']
			print(query_id, es, st)

			# import time
			# t = time.time() * 1000
			# self.RCR.url = "https://flight.qunar.com/touch/api/inter/wwwsearch?depCity=%E8%A5%BF%E5%AE%89&arrCity=%E9%A6%96%E5%B0%94&depDate=2020-03-05&adultNum=1&childNum=0&ex_track=&from=qunarindex&carrier=&queryId=10.90.71.109%3Al%3A3202db46%3A1705a03ed60%3A-1a99&es=UoOIsBDI2%2BBSsa0cCGaUsStI2%2BB1s8DIUoDUsQ61%2BSLIAQSI%7C1582080756032&_v=8&st=1582083029837"
			# self.RCR.param_data = None
			self.RCR.url = "https://flight.qunar.com/touch/api/inter/wwwsearch"
			self.RCR.param_data = (('depCity', self.departure_name), ('arrCity', self.arrival_name),
			                       ('depDate', self.CPR.flight_date),
			                       ('adultNum', self.CPR.adult_num),
			                       ('childNum', self.CPR.child_num),
			                       ("ex_track", ""),
			                       ('from', 'qunarindex'),
			                       ("carrier", ""),
			                       ('queryId', query_id),
			                       ('es', es),
			                       ('_v', '8'), ('st', st))

			referer_url = (
				("searchDepartureAirport", self.departure_name),
				("searchArrivalAirport", self.departure_name),
				("searchDepartureTime", self.CPR.flight_date),
				("searchArrivalTime", ""),
				("nextNDays", "0"), ("startSearch", "true"),
				("fromCode", self.CPR.departure_code), ("toCode", self.CPR.arrival_code),
				("from", "qunarindex"),
				("lowestPrice", "null"),
				("favoriteKey", ""),
				("showTotalPr", "null"),
				("adultNum", self.CPR.adult_num),
				("childNum", self.CPR.child_num),
				("cabinClass", ""),
			)
			referer_url = self.BPR.parse_to_url(referer_url)
			print(referer_url)

			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": 'text/javascript, text/html, application/xml, text/xml, */*',
				'Content-Type': 'application/x-www-form-urlencoded',
				"Host": "flight.qunar.com",
				"Referer": "https://flight.qunar.com/site/oneway_list_inter.htm?" + referer_url,
				'app': app,
				'pre': pre,
				# "cookie": self.base_header['cookie'],
				'X-Requested-With': 'XMLHttpRequest'
			})
			if self.RCR.request_to_get("json"):
				total, temp_list = self.BPR.parse_to_path("$.result.ctrlInfo.total", self.RCR.page_source)
				print(total)
				prices, temp_list = self.BPR.parse_to_path("$.result.flightPrices", self.RCR.page_source)
				# query_id, temp_list = self.BPR.parse_to_path("$.result.ctrlInfo.queryId", self.RCR.page_source)
				print(query_id)
				for k, v in prices.items():
					if k == "Z21264":
						flight_code = v['journey']['flightCode']
				print(flight_code)


				self.RCR.url = "https://flight.qunar.com/touch/api/inter/wwwsearch"
				self.RCR.param_data = (
					('from', 'qunarindex'), ("ex_track", "3w"),
					('depCity', self.departure_name), ('arrCity', self.arrival_name),
					('adultNum', self.CPR.adult_num), ('childNum', self.CPR.child_num),
				    ('depDate', self.CPR.flight_date), ('retDate', ""),
				    ("hasApply", "true"),
					('queryId', query_id),
					("isSupportPack", "true"),
                   ("flightCode", flight_code),
					('st', st),
                   ('es', es),
                   ('_v', '3'),
				)
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Accept": 'text/javascript, text/html, application/xml, text/xml, */*',
					'Content-Type': 'application/x-www-form-urlencoded',
					"Host": "flight.qunar.com",
					"Referer": "https://flight.qunar.com/site/oneway_list_inter.htm?" + referer_url,
					'bp': "1%2C0%2C47051%2C0",
					'pre': pre,
					"ppap": "e4q2p",
					'X-Requested-With': 'XMLHttpRequest'
				})
				if self.RCR.request_to_get("json"):
					print(self.RCR.page_source)
					return True
			# # # 爬取首页
	
	# def process_to_index(self, count: int = 0, max_count: int = 1) -> bool:
	# 	"""Index process. 首页过程。
	#
	# 	Args:
	# 		count (int): 累计计数。
	# 		max_count (int): 最大计数。
	#
	# 	Returns:
	# 		bool
	# 	"""
	# 	if count >= max_count:
	# 		return False
	# 	else:
	# 		# # # # 更新超时时间。
	# 		# self.RCR.timeout = 10
	# 		# # # # 请求接口服务。
	# 		# self.RCR.url = 'http://119.3.234.171:33334/produce/wn/'
	# 		# self.RCR.param_data = None
	# 		# self.RCR.header = None
	# 		# self.RCR.post_data = {"wn": "header"}
	# 		# if not self.RCR.request_to_post("json", "json"):
	# 		# 	self.logger.info(f"请求刷值地址失败(*>﹏<*)【119.3.234.171:33334】")
	# 		# 	self.callback_msg = "请求刷值地址失败，请通知技术检查程序。"
	# 		# 	return self.process_to_index(count + 1, max_count)
	# 		# # # # 获取abck。
	# 		# value = self.RCR.page_source.get("value")
	# 		# if not value:
	# 		# 	self.logger.info(f"刷值数量不够用(*>﹏<*)【119.3.234.171:33334】")
	# 		# 	self.callback_msg = "刷值数量不够用，请通知技术检查程序。"
	# 		# 	return self.process_to_index(count + 1, max_count)
	#
	#
	# 		# value = "{'accept': 'text/javascript, text/html, application/xml, text/xml, */*', 'x-requested-with': 'XMLHttpRequest', 'app': '0%2C0%2C%2C0', 'pre': 'd6640a8b-d84129-294af873-70b4e145-13ff1932e3d2', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.3494.0 Safari/537.36', 'content-type': 'application/x-www-form-urlencoded', 'cookie': 'QN1=00000d00306c2025e430fe54; QN300=organic; QN99=3845; QN205=organic; QN277=organic; csrfToken=GHPGk7869bi62PfkiGoAexB5TKgjd8UJ; QN269=6EB57AA053B311EA91F1FA163E10E623; QN601=536815699ebdd34e5bf2ae63fa5f6e46; QN163=0; QN667=B; QN48=f39bf5f1-0e49-4542-8921-4e4e0a7ad0a8; fid=3997ca83-d8af-49f8-84b6-1f2358f361bc; SplitEnv=D; F235=1582184086986; QN267=3129464094a96b800; QN621=fr%3Dqunarindex; Alina=c6dbcc85-09cb23-8142f460-3982d706-133bc4391087; QunarGlobal=10.88.67.22_-3109e6c5_17060ef6d9b_-3c6f%7C1582184089020; quinn=7892ab520d50eab5fe00b3bed3d06bed5f064b7fb0a24152df845e49a7729261e2b454c55723aa1ec728bcc339293134; _abck=6bf0e2f3-ddc2-4bbc-8bb7-a051283990e9~0~1582184089104~-1~-1~-1; QN271=0ff1972e-413b-4d1e-81bd-6974bf422c65; QN170=101.22.59.80_211061_0_MxVwCqOng7CIZYjmKA5w2ydEh6unf7kJoPF%2F87U4aB0%3D', 'referer': 'https://flight.qunar.com/site/oneway_list_inter.htm?searchDepartureAirport=%E5%93%88%E5%B0%94%E6%BB%A8&searchArrivalAirport=%E5%8F%B0%E5%8C%97&searchDepartureTime=2020-03-06&searchArrivalTime=2020-03-13&nextNDays=0&startSearch=true&fromCode=HRB&toCode=TPE&from=qunarindex&lowestPrice=null&favoriteKey=&showTotalPr=null&adultNum=1&childNum=0&cabinClass='}"
	#
	# 		# # 重新整理header
	# 		# self.base_header = self.BPR.parse_to_eval(value)
	# 		# if self.base_header:
	# 		# 	self.base_header['Referer'] = ""
	# 		# 	self.base_header['User-Agent'] = ""
	# 		# 	self.base_header.pop("Referer")
	# 		# 	self.base_header.pop("User-Agent")
	#
	# 		# print(self.base_header['pre'])
	# 		# print(self.base_header['referer'])
	# 		# print(self.base_header['es'])
	# 		# app = self.base_header['app']
	# 		# pre = self.base_header['pre']
	# 		# print(app, pre)
	# 		# b = self.base_header['cookie']
	# 		# c = b.split("; ")
	# 		# for i in c:
	# 		# 	d, temp_list = self.BPR.parse_to_regex("(.*?)=", i)
	# 		# 	e, temp_list = self.BPR.parse_to_regex(".*?=(.*)", i)
	# 		# 	self.RCR.set_to_cookies(True, [{"name": d, "value": e, "domain": "flight.qunar.com", "path": "/"}])
	# 		#
	# 		# a = "https://flight.qunar.com/touch/api/inter/wwwsearch?depCity=%E5%93%88%E5%B0%94%E6%BB%A8&arrCity=%E5%8F%B0%E5%8C%97&depDate=2020-03-06&adultNum=1&childNum=0&ex_track=&from=qunarindex&carrier=&queryId=10.88.67.22%3Al%3A-3109e6c5%3A17060ef6d9b%3A-3c5a&es=DJiaxi%2BCmavqWiqCaxv%2BaifCB7vqmiUCDaV%2FxJxqCii75JWC%7C1582181677867&_v=8&st=1582184089214"
	# 		#
	# 		# b = self.BPR.parse_to_params(a)
	# 		# c = dict(b)
	# 		# query_id = c['queryId']
	# 		# es = c['es']
	# 		# print(query_id, es)
	#
	# 		import time
	# 		t = time.time() * 1000
	#
	#
	# 		self.RCR.url = "https://m.flight.qunar.com/h5/flight/"
	# 		self.RCR.param_data = None
	# 		self.RCR.header = self.BFR.format_to_same(self.init_header)
	# 		self.RCR.header.update({
	# 			"Host": "m.flight.qunar.com",
	# 			"Upgrade-Insecure-Requests": "1"
	# 		})
	# 		self.RCR.request_to_get()
	#
	# 		self.RCR.url = "https://m.flight.qunar.com/flight/api/touchInterList"
	# 		self.RCR.param_data = None
	# 		referer_url = (
	# 			("depCity", self.departure_name),
	# 			("arrCity", self.departure_name),
	# 			("goDate", self.CPR.flight_date),
	# 			("from", "touch_index_search"),
	# 			("adultNum", self.CPR.adult_num),
	# 			("childNum", self.CPR.child_num),
	# 			("cabinType", "0"),
	# 			("flightType", "oneWay"),
	# 		)
	# 		referer_url = self.BPR.parse_to_url(referer_url)
	# 		print(referer_url)
	#
	# 		# self.RCR.header = self.BFR.format_to_same(self.init_header)
	# 		# self.RCR.header.update({
	# 		# 	"Accept": 'application/json, text/javascript',
	# 		# 	'Content-Type': 'application/json',
	# 		# 	"Host": "m.flight.qunar.com",
	# 		# 	"Origin": "https://m.flight.qunar.com",
	# 		# 	"Referer": "https://m.flight.qunar.com/ncs/page/interlist?" + referer_url,
	# 		# 	# 'app': app,
	# 		# 	# 'pre': pre,
	# 		# 	# "cookie": self.base_header['cookie'],
	# 		# 	'X-Requested-With': 'XMLHttpRequest'
	# 		# })
	#
	# 		# self.RCR.post_data = {
	# 		# 	"adult": self.CPR.adult_num, "arrCity": self.arrival_name, "cabinType": "0",
	# 		# 	"child": self.CPR.child_num, "depCity": self.departure_name, "flightType":"oneWay",
	# 		# 	"from": "touch_index_search", "goDate": self.CPR.flight_date, "firstRequest": False,
	# 		# 	"more": 1, "sort": 5,
	# 		#     "r": 1582186748428, "touchVersion": "v2", "_v": 22, "_rgb": 251749, "underageOption": "",
	# 		#     "queryId": "10.88.100.203:l:-60477c99:170612a2b41:-3b56", "reqSource": "touch",
	# 		# 	"st": 1582186746856, "__m__": "1c654d47430176713fed17068229c042"}
	#
	# 		self.RCR.header = {'b8639d': '875b029de417d183fd6fa90bd257ca01e91a654a',
	# 		                   'origin': 'https://m.flight.qunar.com',
	# 		                   'pre': '8870ec27-77af71-21467458-28abef68-6dea239aff63',
	# 		                   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3494.0 Safari/537.36',
	# 		                   'content-type': 'application/json', 'accept': 'application/json, text/javascript',
	# 		                   'x-requested-with': 'XMLHttpRequest', 'wps': '6',
	# 		                   # 'cookie': 'QN1=000031002f10202673b85eb6; QN667=C; QN48=81f74906-cfa6-466d-b0a6-b57a78b9f85f; F234=1582188663887; QN668=51%2C55%2C58%2C52%2C51%2C58%2C58%2C56%2C56%2C53%2C58%2C59%2C59; QN300=organic; QN621=fr%3Dtouch_index_search; Alina=7b5003d6-807e12-08439e49-50ad0190-44d58b9204c1; QN601=290b7a37eeecf03fc9293bb75f09c16f; quinn=0720ce1258c59ff89c72890316a4ac6480b93026924c0d1de688548baa331d4df919dd376e9b0d6dd5c39ac2a35ff661; F235=1582188665049; SC1=97de759a0b1628e35aff6453bfaf7a7d; SC18=',
	# 		                   'referer': 'https://m.flight.qunar.com/ncs/page/interlist?depCity=%E9%A9%AC%E5%B0%BC%E6%8B%89&arrCity=%E9%A6%99%E6%B8%AF&goDate=2020-04-21&from=touch_index_search&adult=1&child=0&cabinType=0&flightType=oneWay&_firstScreen=1&_gogokid=12'}
	# 		self.RCR.post_data = {"adult":"1","arrCity":"香港","cabinType":"0","child":"0","depCity":"马尼拉",
	# 		                      "flightType":"oneWay","from":"touch_index_search","goDate":"2020-04-21",
	# 		                      "firstRequest":False,"more":1,"sort":5,"r":1582188668255,"touchVersion":"v2","_v":22,
	# 		                      "_rgb":251749,"underageOption":"","queryId":"10.88.100.203:l:-60477c99:170612a2b41:-2bdd","reqSource":"touch","st":1582188666599,"__m__":""}
	#
	# 		if self.RCR.request_to_post("json", "json"):
	# 			print(self.RCR.page_source)
	# 			# total, temp_list = self.BPR.parse_to_path("$.result.ctrlInfo.total", self.RCR.page_source)
	# 			# print(total)
	# 			# prices, temp_list = self.BPR.parse_to_path("$.result.flightPrices", self.RCR.page_source)
	# 			# query_id, temp_list = self.BPR.parse_to_path("$.result.ctrlInfo.queryId", self.RCR.page_source)
	# 			# print(query_id)
	# 			# for k, v in prices.items():
	# 			# 	if k == "Z21264":
	# 			# 		flight_code = v['journey']['flightCode']
	# 			# print(flight_code)
	# 			#
	# 			# import time
	# 			# t = time.time() * 1000
	# 			# self.RCR.url = "https://flight.qunar.com/touch/api/inter/wwwsearch"
	# 			# self.RCR.param_data = (('depCity', self.departure_name), ('arrCity', self.arrival_name),
	# 			#                        ('depDate', self.CPR.flight_date), ('retDate', ""),
	# 			#                        ("ex_track", "3w"), ("hasApply", "true"), ("isSupportPack", "true"),
	# 			#                        ('adultNum', self.CPR.adult_num),
	# 			#                        ('childNum', self.CPR.child_num),
	# 			#                        ('from', 'qunarindex'), ('queryId', query_id),
	# 			#                        ("flightCode", flight_code),
	# 			#                        ('es', es),
	# 			#                        ('_v', '3'), ('st', int(t)))
	# 			# self.RCR.header = self.BFR.format_to_same(self.init_header)
	# 			# self.RCR.header.update({
	# 			# 	"Accept": 'text/javascript, text/html, application/xml, text/xml, */*',
	# 			# 	'Content-Type': 'application/x-www-form-urlencoded',
	# 			# 	"Host": "flight.qunar.com",
	# 			# 	"Referer": "https://flight.qunar.com/site/oneway_list_inter.htm?" + referer_url,
	# 			# 	'app': app,
	# 			# 	'pre': pre,
	# 			# 	# "cookie": self.base_header['cookie'],
	# 			# 	'X-Requested-With': 'XMLHttpRequest'
	# 			# })
	# 			# if self.RCR.request_to_get("json"):
	# 			# 	print(self.RCR.page_source)
	# 			# 	return True
	#
	# # # # 爬取首页


	
	#
	# def query_from_price(self, count=0) -> bool:
	# 	"""selenium获取twellkey qt
	# 	:return:  bool
	# 	"""
	# 	# # # 爬取首页
	# 	# self.SCR.url = f'https://flight.qunar.com/site/oneway_list_inter.htm?searchDepartureAirport={self.CPR.depCityName}&searchArrivalAirport={self.CPR.arrCityName}&searchDepartureTime={self.CPR.departureDate}&nextNDays=0&startSearch=true&fromCode={self.CPR.departureAircode}&toCode={self.CPR.arrivalAircode}&from=qunarindex&lowestPrice=null&favoriteKey=&showTotalPr=null&adultNum={self.CPR.adultCount}&childNum={self.CPR.childrenCount}&cabinClass='
	# 	# # self.SCR.url = "http://www.ip138.com"
	# 	# # self.SCR.url = 'https://www.qunar.com'
	# 	# if count >3 :
	# 	#     self.logger.info("请求页面请重试")
	# 	#     self.callback_msg = "请求页面超时 请重试"
	# 	#     return self.query_from_price(count)
	# 	# self.SCR.set_url()
	# 	# self.SCR.set_refresh()
	# 	# self.merchant = ''
	# 	# while not self.SCR.set_click('css',f'div[class="m-airfly-lst"] div[class="b-airfly"][data-reactid*="{self.CPR.flightNum}"]'):
	# 	#     if count > 3:
	# 	#         self.logger.info("请求页面请重试")
	# 	#         self.callback_msg = "请求页面超时 请重试"
	# 	#         return False
	# 	#     self.SCR.set_refresh()
	# 	#     # if self.SCR.driver.find_element_by_xpath('//*[@id="root"]/div/div[3]/div[1]/div[3]/div[5]/div/a[text()="下一页"]'):
	# 	#     self.SCR.set_to_wait('xpath', '//*[@id="root"]/div/div[3]/div[1]/div[3]/div[5]/div/a[text()="下一页"]', 5)
	# 	#     if not self.SCR.set_click('xpath','//*[@id="root"]/div/div[3]/div[1]/div[3]/div[5]/div/a[text()="下一页"]'):
	# 	#             self.logger.info("选取航班失败 请确认是否有该航班")
	# 	#             self.callback_msg = "选取航班失败 请确认是否有该航班"
	# 	#             self.SCR.set_refresh()
	# 	#             # return self.query_from_price()
	# 	#     self.SCR.set_to_wait('css',f'div[class="m-airfly-lst"] div[class="b-airfly"][data-reactid*="{self.CPR.flightNum}"]',5)
	# 	#     self.logger.info(count)
	# 	#     count += 1
	# 	# # # 爬取首页
	# 	self.SCR.url = f'https://flight.qunar.com/site/oneway_list_inter.htm?searchDepartureAirport={self.CPR.depCityName}&searchArrivalAirport={self.CPR.arrCityName}&searchDepartureTime={self.CPR.departureDate}&nextNDays=0&startSearch=true&fromCode={self.CPR.departureAircode}&toCode={self.CPR.arrivalAircode}&from=qunarindex&lowestPrice=null&favoriteKey=&showTotalPr=null&adultNum={self.CPR.adultCount}&childNum={self.CPR.childrenCount}&cabinClass='
	#
	# 	# self.SCR.url = "http://www.ip138.com"
	# 	# self.SCR.url = 'https://www.qunar.com'
	#
	# 	while not self.SCR.set_url():
	# 		self.SCR.delete_cookies()
	# 	# self.SCR.set_refresh()
	# 	time.sleep(5)
	# 	self.SCR.set_to_wait('css',
	# 	                     f'div[class="m-airfly-lst"] div[class="b-airfly"][data-reactid*="{self.CPR.flightNum}"]',
	# 	                     40)
	#
	# 	# time.sleep(1000)
	# 	while not self.SCR.set_click('css',
	# 	                             f'div[class="m-airfly-lst"] div[class="b-airfly"][data-reactid*="{self.CPR.flightNum}"]'):
	# 		self.SCR.set_refresh()
	# 		# self.SCR.set_to_wait('xpath', '//*[@id="root"]/div/div[3]/div[1]/div[3]/div[5]/div/a[text()="下一页"]', 5)
	# 		# if not self.SCR.set_click('xpath','//*[@id="root"]/div/div[3]/div[1]/div[3]/div[5]/div/a[text()="下一页"]'):
	# 		# self.logger.info("出现登录提示框")
	# 		# self.callback_msg = "出现封禁"
	# 		# self.SCR.set_quit()
	# 		# return False
	# 		# self.SCR.set_to_wait('css',f'div[class="m-airfly-lst"] div[class="b-airfly"][data-reactid*="{self.CPR.flightNum}"]',5)
	# 		count += 1
	# 		if count > 1:
	# 			self.logger.info("出现登录提示框")
	# 			self.callback_msg = "出现封禁"
	# 			self.SCR.set_quit()
	# 			return False
	# 	try:
	# 		self.SCR.set_click('xpath', '//*[@id="QunarPopBoxClosePop"]')
	# 	except:
	# 		pass
	# 	self.SCR.set_to_wait('xpath',
	# 	                     f'//div[@class="m-airfly-lst"]/div[contains(@data-reactid,"{self.CPR.flightNum}")]//div[2]/div//div/div//div//span/div[text()="低价特惠"]/../../../../../div/div[4]',
	# 	                     10)
	#
	# 	if self.SCR.set_click("xpath", "/html/body/div[6]/div/div[3]/div[2]/form/div[2]/label"):
	# 		self.logger.info("出现登录提示框")
	# 		self.callback_msg = "出现封禁"
	# 		self.SCR.set_quit()
	# 		return False
	# 	if not self.SCR.set_click('xpath',
	# 	                          f'//div[@class="m-airfly-lst"]/div[contains(@data-reactid,"{self.CPR.flightNum}")]//div[2]/div//div/div//div//span/div[text()="低价特惠"]/../../../../../div/div[4]'):
	# 		if count > 3:
	# 			self.logger.info("选取低价特惠失败 请确认是否有低价特惠")
	# 			self.callback_msg = "选取低价特惠失败 请确认是否有低价特惠"
	# 			return False
	# 		return self.query_from_price(count)
	# 	cookie = {}
	# 	for i in self.SCR.driver.get_cookies():
	# 		cookie[i["name"]] = i["value"]
	# 		self.UCR.set_to_cookies([{'name': str(i["name"]), 'value': str(i["value"])}])
	# 	# with open("cookies.txt", "w") as f:
	# 	#     f.write(json.dumps(cookie))
	# 	# input()
	# 	# time.sleep(1000)
	# 	wn_data = str(self.SCR.driver.get_log("performance"))
	# 	window = self.SCR.driver.current_window_handle
	# 	handles = self.SCR.driver.window_handles  # 获取当前窗口句柄集合（列表类型）
	# 	self.SCR.driver.switch_to.window(handles[-1])  # 切换窗口
	#
	# 	time.sleep(15)
	# 	self.page = self.SCR.driver.page_source
	# 	# self.logger.info('self.page')
	# 	self.merchant = \
	# 		self.DPR.parse_as_attributes('xpath', 'text', '//*[@id="vendorinfo-section"]/div[1]/div/p[1]/text()',
	# 		                             self.page)[0]
	#
	# 	try:
	# 		self.twellkey = re.findall('twellkey=(.*?)&qt', wn_data)[0]
	# 		self.qt = re.findall('qt=(.*?)&', wn_data)[0]
	# 	except:
	# 		self.logger.info("点击页面失败 请重试")
	# 		self.callback_msg = "点击页面失败"
	# 		return self.query_from_price(count)
	# 	if '七彩阳光' in self.merchant:
	# 		self.SCR.set_quit()
	# 		self.logger.info("自己家的票 采啥啊(*`皿´*)")
	# 		self.callback_msg = "当前出票公司为我司"
	# 		return False
	# 	if self.twellkey and self.qt:
	# 		self.logger.info("获取TWELL QT 成功")
	# 		self.SCR.set_quit()
	# 		return True
	# 	self.logger.info("点击页面失败 ")
	# 	self.callback_msg = "点击页面失败 请重试"
	# 	return self.query_from_price(count)
	#
	# def query_from_passengers(self) -> bool:
	# 	"""获取填写乘客信息页面
	# 	:return:  bool
	# 	"""
	#
	# 	referer_url = f'https://flight.qunar.com/site/oneway_list_inter.htm?searchDepartureAirport={self.CPR.depCityName}&searchArrivalAirport={self.CPR.arrCityName}&searchDepartureTime={self.CPR.departureDate}&nextNDays=0&startSearch=true&fromCode={self.CPR.departureAircode}&toCode={self.CPR.arrivalAircode}&from=qunarindex&lowestPrice=null&favoriteKey=&showTotalPr=null&adultNum={self.CPR.adultCount}&childNum={self.CPR.childrenCount}&cabinClass='
	# 	self.UCR.url = "https://pangolin.flight.qunar.com/flightns/pangolin/booking"
	# 	self.UCR.param_data = (
	# 		('bk', self.twellkey),
	# 		('bksource', 'flight_type=_old&env=D&tag=qunar_low'),
	# 		('type', '1'),
	# 		('qt', self.qt),
	# 	)
	# 	self.UCR.header = self.BFR.format_as_same(self.init_header)
	# 	self.UCR.header.update({
	# 		'authority': 'pangolin.flight.qunar.com',
	# 		'pragma': 'no-cache',
	# 		'cache-control': 'no-cache',
	# 		'upgrade-insecure-requests': '1',
	# 		'sec-fetch-mode': 'navigate',
	# 		'sec-fetch-user': '?1',
	# 		'sec-fetch-site': 'none',
	# 		'referer': quote(referer_url)
	# 	})
	# 	if self.UCR.request_to_get():
	# 		return True
	# 	self.logger.info("获取乘客信息页面失败(*>﹏<*)【login】")
	# 	self.callback_msg = "获取乘客信息页面失败"
	# 	return False
	#
	# def query_from_pricetag(self) -> bool:
	# 	"""获取pricetag
	# 	:return: bool
	# 	"""
	# 	self.UCR.url = "https://pangolin.flight.qunar.com/flightns/pangolin/avdata"
	# 	self.UCR.param_data = (
	# 		('bk', self.twellkey),
	# 		('bksource', 'flight_type=_old&env=D&tag=direct_low'),
	# 		('type', '1'),
	# 		('qt', ''),
	# 		('av', 'true'),
	# 	)
	# 	self.UCR.header = self.BFR.format_as_same(self.init_header)
	# 	self.UCR.header.update({
	# 		'Referer': f'https://pangolin.flight.qunar.com/flightns/pangolin/booking?bk={self.twellkey}&bksource=flight_type%3D_old%26env%3DD%26tag%3Ddirect_low&type=1&qt={self.qt}',
	#
	# 	})
	#
	# 	if self.UCR.request_to_get():
	# 		data = self.BPR.parse_as_dict(self.UCR.page_source)
	# 		self.bookingTagKey = self.BPR.parse_as_path("$..bookingTagKey", data)[0]
	# 		return True
	# 	self.logger.info("获取bookingTagKey失败(*>﹏<*)【login】")
	# 	self.callback_msg = "获取bookingTagKey失败 请重试"
	# 	return False
	#
	# def query_from_token(self) -> bool:
	# 	"""获取token
	# 	:return:  bool
	# 	"""
	# 	self.UCR.url = "https://pangolin.flight.qunar.com/flightns/pangolin/createOrder"
	# 	self.UCR.param_data = None
	# 	self.UCR.header = self.BFR.format_as_same(self.init_header)
	# 	self.UCR.header.update({
	# 		'origin': 'https://pangolin.flight.qunar.com',
	# 		'referer': f'https://pangolin.flight.qunar.com/flightns/pangolin/booking?bk={self.twellkey}&bksource=flight_type%3D_old%26env%3DD%26tag%3D&type=1&qt={self.qt}',
	# 		'sec-fetch-site': 'same-origin',
	# 	})
	# 	data = {'bookingTagKey': self.bookingTagKey, 'productType': 100, 'source': 'web',
	# 	        'subOrderInfoMap': {'100': None, '999': {'@class': 'com.qunar.flight.adc.pojo.ADCSaveSubOrderInfo',
	# 	                                                 'records': [{'productKey': 'international_overseas_hotel',
	# 	                                                              'segments': [{'sequenceNum': 1,
	# 	                                                                            'flightNum': self.CPR.flightNum,
	# 	                                                                            'depAirportCode': self.CPR.departureAircode,
	# 	                                                                            'arrAirportCode': self.CPR.arrivalAircode,
	# 	                                                                            'carrier': None,
	# 	                                                                            'depDate': self.CPR.departureDate,
	# 	                                                                            'cabin': None,
	# 	                                                                            'arrDate': self.CPR.arrivalDate,
	# 	                                                                            'depTime': self.CPR.departureTime,
	# 	                                                                            'arrTime': self.CPR.arrivalTime,
	# 	                                                                            'flightType': self.CPR.segmentType}],
	# 	                                                              'passengers': self.CPR.card_list}]}},
	# 	        'packageType': 1, 'subOrderInfo': None, 'packageResult': None, 'parentalOrderNo': None,
	# 	        'passengerList': self.CPR.passenger_list,
	# 	        'contactInfo': {'name': self.CPR.contactsName, 'mobCountryCode': '86', 'phone': self.CPR.contactsMobile,
	# 	                        'email': self.CPR.contactsEmail}, 'subOrderInfoMap2': {'100': None, '999': {
	# 			'@class': 'com.qunar.flight.adc.pojo.ADCSaveSubOrderInfo', 'records': [
	# 				{'productKey': 'international_overseas_hotel', 'segments': [
	# 					{'sequenceNum': 1, 'flightNum': self.CPR.flightNum, 'depAirportCode': self.CPR.departureAircode,
	# 					 'arrAirportCode': self.CPR.arrivalAircode, 'carrier': None, 'depDate': self.CPR.departureDate,
	# 					 'cabin': None, 'arrDate': self.CPR.arrivalDate, 'depTime': self.CPR.departureTime,
	# 					 'arrTime': self.CPR.arrivalTime, 'flightType': 1}], 'passengers': self.CPR.card_list}]}},
	# 	        'dup': {'isCheckOrder': False,
	# 	                'param': {'allPrice': 1598, 'refer': 'submit', 'passengers': self.CPR.card_list,
	# 	                          'contact': self.CPR.contactsName, 'flightType': '1', 'flights': [
	# 			                {'dpt': self.CPR.departureAircode, 'arr': self.CPR.arrivalAircode,
	# 			                 'depDate': self.CPR.departureDate, 'dptTime': self.CPR.departureTime,
	# 			                 'arrDate': self.CPR.arrivalDate, 'arrTime': self.CPR.departureTime,
	# 			                 'flightNo': self.CPR.flightNum, 'cabin': 'S'}],
	# 	                          'contactMob': self.CPR.contactsMobile}}, 'remark': '', 'flightBook': 'F0'}
	# 	self.UCR.post_data = {
	# 		'body': json.dumps(data)
	# 	}
	#
	# 	if self.UCR.request_to_post():
	# 		if '您已预订相同行程的订单，订单号' in self.UCR.page_source:
	# 			self.logger.info("已有相同行程订单(*>﹏<*)")
	# 			self.callback_msg = "已有相同行程订单"
	# 			return False
	# 		if '证件号不能重复使用' in self.UCR.page_source:
	# 			self.logger.info("证件号不能重复使用(*>﹏<*)")
	# 			self.callback_msg = "证件号不能重复使用"
	# 			return False
	# 		data = self.BPR.parse_as_dict(self.UCR.page_source)
	# 		self.orderNo = self.BPR.parse_as_path("$..orderNo", data)[0]
	# 		self.token = self.BPR.parse_as_path("$..token", data)[0]
	# 		data = self.BPR.parse_as_dict(self.UCR.page_source)
	# 		return True
	#
	# 	self.logger.info("提交乘客信息错误(*>﹏<*)")
	# 	self.callback_msg = "提交乘客信息错误"
	# 	return False
	#
	# def post_token(self) -> bool:
	# 	"""post token
	# 	:return: bool
	# 	"""
	# 	self.UCR.url = f'https://order.flight.qunar.com/nts/order/pay/token_{self.token}_orderNo_{self.orderNo}_otaType_5_biz_interNTS_from_3wBookingPage'
	# 	self.UCR.param_data = None
	# 	self.UCR.header = self.BFR.format_as_same(self.init_header)
	# 	self.UCR.header.update({
	# 		'origin': 'https://pangolin.flight.qunar.com',
	# 		'referer': f'https://pangolin.flight.qunar.com/flightns/pangolin/booking?bk={self.twellkey}&bksource=flight_type%3D_old%26env%3DD%26tag%3D&type=1&qt={self.qt}',
	# 		'sec-fetch-site': 'same-origin',
	# 	})
	#
	# 	if self.UCR.request_to_get():
	# 		self.sign = self.BPR.parse_as_regex('name="sign" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.busiTypeId = self.BPR.parse_as_regex('"busiTypeId" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.tradeNo = self.BPR.parse_as_regex('name="tradeNo" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.checkCode = self.BPR.parse_as_regex('name="checkCode" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.orderDate = self.BPR.parse_as_regex('name="orderDate" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.merchantCode = self.BPR.parse_as_regex('name="merchantCode" value="(.*?)"', self.UCR.page_source)[0]
	# 		self.version = self.BPR.parse_as_regex('name="version" value="(.*?)"', self.UCR.page_source)[0]
	# 		return True
	#
	# 	self.logger.info("提交token错误(*>﹏<*)")
	# 	self.callback_msg = "提交token错误"
	# 	return False
	#
	# def get_order(self) -> bool:
	# 	"""提交订单
	# 	:return:  bool
	# 	"""
	#
	# 	self.UCR.url = 'https://pay.qunar.com/pc-cashier/cn/api/MultiCashierPay2g.do'
	# 	self.UCR.param_data = None
	# 	self.UCR.header = self.BFR.format_as_same(self.init_header)
	# 	self.UCR.header.update({
	# 		'Origin': 'https://order.flight.qunar.com',
	# 		'Referer': f'https://order.flight.qunar.com/nts/order/pay/token_{self.token}_orderNo_{self.orderNo}_otaType_5_biz_interNTS_from_3wBookingPage',
	#
	# 	})
	# 	self.UCR.post_data = {
	# 		'sign': self.sign,
	# 		'busiTypeId': self.busiTypeId,
	# 		'tradeNo': self.tradeNo,
	# 		'checkCode': self.checkCode,
	# 		'orderDate': self.orderDate,
	# 		'merchantCode': self.merchantCode,
	# 		'version': self.version
	# 	}
	# 	if self.UCR.request_to_post():
	# 		try:
	# 			self.occupyPrice = round(float(
	# 				self.BPR.parse_as_regex('<input name="orderAmount" value="(.*?)" type="hidden"/>',
	# 				                        self.UCR.page_source)[0]))
	# 		except:
	# 			self.post_token()
	# 			self.logger.info("提交订单错误(*>﹏<*)")
	# 			self.callback_msg = "提交订单错误 请重试"
	# 			return False
	# 		return True
	# 	self.logger.info("提交订单错误(*>﹏<*)")
	# 	self.callback_msg = "提交订单错误 请重试"
	# 	return False
	
	#

	def process_to_return(self) -> bool:
		"""Return process. 返回过程。
	
		Returns:
			bool
		"""
		self.callback_data["success"] = "true"
		self.callback_data['msg'] = "占舱成功"
		self.callback_data['totalPrice'] = self.total_price
		self.callback_data["merchant"] = ""
		self.callback_data['pnr'] = self.record
		self.logger.info(self.callback_data)
		return True

