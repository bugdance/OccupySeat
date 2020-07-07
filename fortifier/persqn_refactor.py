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
"""The refactor is use for refactoring code."""
from booster.callback_formatter import CallBackFormatter
from booster.callin_parser import CallInParser


class CFRefactor(CallBackFormatter):
	"""重构格式器。"""
	
	@classmethod
	def format_to_async(cls) -> dict:
		"""Format to sync data. 格式化异步数据。

		Returns:
			dict
		"""
		async_data = {
			"success": "false",  # 返回状态。
			"msg": "占舱失败",  # 返回信息。
			"totalPrice": 0,  # 总价。
			"pnr": "",   # 票号。
			'merchant': ""  # 代理商
		}
		return async_data


class CPRefactor(CallInParser):
	"""重构解析器。"""
	
	def parse_to_interface(self, source_dict: dict = None) -> bool:
		"""Parsing interface parameters. 解析接口数据。

		Args:
			source_dict (dict): The source dict. 来源字典。

		Returns:
			bool
		"""
		if not source_dict or type(source_dict) is not dict:
			self.logger.info(f"解析接口参数有误(*>﹏<*)【{source_dict}】")
			return False
		# # # Parse the detail. 解析航班信息。
		self.task_id = source_dict.get('flightOrderId')
		# # # Parse the contact. 解析联系人信息。
		contact = source_dict.get('reverseSufficiencyContacts')
		if not self.parse_to_contact(contact):
			return False
		# # # Parse the flight number. 航班号单独解析。
		flight_num = source_dict.get('flightSegments')
		if not self.parse_to_flight(flight_num):
			return False
		# # # Parse the passengers. 乘客信息解析。
		passengers_list = source_dict.get('flightPassengers')
		if not self.parse_to_passenger(passengers_list):
			return False
		
		return True
	
	def parse_to_contact(self, contacts: dict = "") -> bool:
		"""Parse the flight number. 解析航班号。

		Args:
			contacts (str): Flight number. 航班号。

		Returns:
			bool
		"""
		if not contacts or type(contacts) is not dict:
			self.logger.info(f"解析联系参数有误(*>﹏<*)【{contacts}】")
			return False
		
		# # # Parse the contact. 解析联系人信息。
		full_name = contacts.get('contactsName')
		if not full_name or type(full_name) is not str:
			self.logger.info(f"解析联系参数有误(*>﹏<*)【{contacts}】")
			return False
		# name_list = full_name.split('/')
		# if len(name_list) < 2:
		# 	self.logger.info(f"解析联系参数有误(*>﹏<*)【{contacts}】")
		# 	return False
		self.contact_last = full_name  # 全称
		self.contact_first = ""
		self.contact_email = contacts.get('contactsEmail')
		self.contact_mobile = contacts.get('contactsMobile')
		return True
	
	def parse_to_flight(self, flight_segments: dict = "") -> bool:
		"""Parse the flight number. 解析航班号。

		Args:
			flight_segments (str): Flight number. 航班号。

		Returns:
			bool
		"""
		if not flight_segments or type(flight_segments) is not dict:
			self.logger.info(f"解析航班参数有误(*>﹏<*)【{flight_segments}】")
			return False

		self.departure_code = flight_segments.get('departureAircode')
		self.arrival_code = flight_segments.get('arrivalAircode')
		self.flight_date = flight_segments.get('departureDate')
		self.flight_num = flight_segments.get('flightNum')
		return True
	
	def parse_to_passenger(self, passengers_list: list = None) -> bool:
		"""Parse the passengers. 乘客信息解析。

		Args:
			passengers_list (list): The passengers list. 乘客列表。

		Returns:
			bool
		"""
		if not passengers_list or type(passengers_list) is not list:
			self.logger.info(f"解析乘客参数有误(*>﹏<*)【{passengers_list}】")
			return False
		
		for n, v in enumerate(passengers_list):
			full_name = v.get('passengerName')  # 姓名。
			age_type = v.get('passengerType')  # 乘客类型（0成人/1儿童/2婴儿）。
			gender = v.get('passengerSex')  # 性别（M/F）。
			birthday = v.get('passengerBirthday')  # 生日（19840727）。
			nationality = v.get('passengerNationality')  # 国籍（CN）。
			card_num = v.get('cardNum')  # 护照。
			card_expired = v.get('cardExpired')  # 护照时间（20840727）。
			card_place = v.get('cardIssuePlace')  # 护照签发地（CN）。
			baggage = v.get('baggage')  # 行李。
			# # # Check the data. 检查数据。
			if not full_name or not birthday or not gender or type(age_type) is not int:
				self.logger.info(f"解析乘客参数有误(*>﹏<*)【{n}】【{v}】")
				return False
			
			self.return_baggage.append({"passengerName": full_name, "baggage": baggage})
			
			name_list = full_name.split('/')
			if len(name_list) < 2:
				self.logger.info(f"解析乘客姓名有误(*>﹏<*)【{n}】【{full_name}】")
				return False
			# # # Compose onto the data. 组合数据。
			list_data = {
				"last_name": name_list[0], "first_name": name_list[1], "gender": gender,
				"birthday": birthday, "nationality": nationality, "card_num": card_num,
				"card_expired": card_expired, "card_place": card_place, "baggage": baggage
			}
			if age_type == 0:
				self.adult_list.append(list_data)
			elif age_type == 1:
				self.child_list.append(list_data)
			elif age_type == 2:
				self.infant_list.append(list_data)
		
		self.adult_num = len(self.adult_list)
		self.child_num = len(self.child_list)
		self.infant_num = len(self.infant_list)
		if not self.adult_num:
			self.logger.info(f"解析乘客成人有误(*>﹏<*)【{passengers_list}】")
			return False
		
		return True
	
	