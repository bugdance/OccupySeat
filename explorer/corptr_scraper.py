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
from booster.callback_formatter import CallBackFormatter
from booster.callin_parser import CallInParser
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser
from detector.corptr_simulator import CorpTRSimulator


class CorpTRScraper(RequestWorker):
    """TR采集器，TR网站流程交互。"""
    
    def __init__(self) -> None:
        RequestWorker.__init__(self)
        self.RCR = RequestCrawler()  # 请求爬行器。
        self.AFR = AESFormatter()  # AES格式器。
        self.BFR = BasicFormatter()  # 基础格式器。
        self.BPR = BasicParser()  # 基础解析器。
        self.CFR = CallBackFormatter()  # 回调格式器。
        self.CPR = CallInParser()  # 接入解析器。
        self.DFR = DateFormatter()  # 日期格式器。
        self.DPR = DomParser()  # 文档解析器。
        self.CSR = CorpTRSimulator()
        # # # 请求中用到的变量
        self.verify_token: str = ""  # 认证token
        self.tab_id: str = ""  # 认证tab id
        self.request_sequence: str = ""
        self.dCF_ticket: str = ""
        self.cookies = None
        self.ajax_header: str = ""  # 认证ajax header
        self.temp_source: str = ""  # 临时源数据
        self.hold_button: str = ""  # 占舱按钮
        self.key: str = ""
        # # # 返回中用到的变量
        self.total_price: float = 0.0  # 总价
        self.baggage_price: float = -1  # 行李总价
        self.record: str = ""  # 票号
        self.pnr_timeout: str = ""  # 票号超时时间
    
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
        self.CSR.logger = self.logger
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
        self.user_agent, self.init_header = self.RCR.build_to_header("none")
        # # # 主体流程。
        if self.process_to_login():
            if self.process_to_search():
                if self.process_to_query():
                    if self.process_to_service():
                        if self.process_to_passenger():
                            if self.process_to_payment():
                                if self.process_to_record():
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
    
    def set_cookies_acw_sc(self):
        arg1 = self.RCR.page_source[25:65]
        base = "3000176000856006061501533003690027800375"
        trans = ""
        res = ''
        try:
            list_1 = [0xf, 0x23, 0x1d, 0x18, 0x21, 0x10, 0x1, 0x26, 0xa, 0x9, 0x13, 0x1f, 0x28, 0x1b, 0x16,
                      0x17, 0x19, 0xd, 0x6, 0xb, 0x27, 0x12, 0x14, 0x8, 0xe, 0x15, 0x20, 0x1a, 0x2, 0x1e, 0x7,
                      0x4, 0x11, 0x5,
                      0x3, 0x1c, 0x22, 0x25, 0xc, 0x24]
            for i in range(len(list_1)):
                trans += arg1[list_1[i] - 1]
            for i in range(0, len(trans), 2):
                v1 = int(trans[i: i + 2], 16)
                v2 = int(base[i: i + 2], 16)
                res += "%02x" % (v1 ^ v2)
            self.RCR.set_to_cookies(
                                    cookie_list=[{"name": 'acw_sc_v2',
                                                  "value": res,
                                                  # 'domain': 'makeabooking.flyscoot.com',
                                                  # 'path': '/'
                                                  }]
                                    )
            return True
        except Exception as ex:
            self.callback_msg = f"设置 Cookie 失败 | {ex}"
            return False
    
    def process_to_verify(self, captcha_url: str = "", referer_url: str = "",
                          count: int = 0, max_count: int = 2) -> bool:
        """Verify process. 验证过程。

        Args:
            captcha_url
            referer_url
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 获取ajax header
            self.RCR.url = "https://makeabooking.flyscoot.com/tgrairwaysdstl.js"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "*/*",
                "Host": "makeabooking.flyscoot.com",
                "Referer": referer_url
            })
            if self.RCR.request_to_get():
                self.ajax_header, temp_list = self.BPR.parse_to_regex('ajax_header:"(.*?)",', self.RCR.page_source)
                if self.ajax_header:
                    # # # 获取challenge
                    self.RCR.url = "https://makeabooking.flyscoot.com/distil_r_captcha_challenge"
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "*/*",
                        "Host": "makeabooking.flyscoot.com",
                        "Origin": "https://makeabooking.flyscoot.com",
                        "Referer": referer_url,
                        "X-Distil-Ajax": self.ajax_header
                    })
                    self.RCR.post_data = None
                    if self.RCR.request_to_post():
                        challenge, temp_list = self.BPR.parse_to_regex("(.*?);", self.RCR.page_source)
                        if challenge:
                            # # # 获取mp3地址
                            self.RCR.url = "http://api-na.geetest.com/get.php"
                            self.RCR.param_data = (
                                ("gt", "0fdbade8a0fe41cba0ff758456d23dfa"), ("challenge", challenge),
                                ("type", "voice"), ("lang", "zh-cn"), ("callback", ""),
                            )
                            self.RCR.header = self.BFR.format_to_same(self.init_header)
                            self.RCR.header.update({
                                "Accept": "*/*",
                                "Host": "api-na.geetest.com",
                                "Referer": referer_url
                            })
                            if self.RCR.request_to_get():
                                get_json = self.RCR.page_source.strip("()")
                                get_json = self.BPR.parse_to_dict(get_json)
                                voice_path, temp_list = self.BPR.parse_to_path("$.data.new_voice_path", get_json)
                                if not voice_path:
                                    self.logger.info(f"认证音频地址错误(*>﹏<*)【{self.RCR.page_source}】")
                                    self.callback_msg = "认证音频地址错误"
                                    return self.process_to_verify(captcha_url, referer_url, count + 1, max_count)
                                else:
                                    # # # 获取mp3文件
                                    self.RCR.url = "http://static.geetest.com" + voice_path
                                    self.RCR.param_data = None
                                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                                    self.RCR.header.update({
                                        "Accept": "*/*",
                                        "Host": "static.geetest.com",
                                        "Referer": referer_url
                                    })
                                    if self.RCR.request_to_get("content"):
                                        # # # 识别语音
                                        voice_name = f"voice-{self.CPR.task_id}"
                                        result, temp_list = self.CSR.recognize_to_voice(voice_name, self.RCR.page_source)
                                        number, temp_list = self.BPR.parse_to_regex("\d+", result)
                                        if number:
                                            # # # 获取validate
                                            self.RCR.url = "http://api-na.geetest.com/ajax.php"
                                            self.RCR.param_data = (
                                                ("gt", "0fdbade8a0fe41cba0ff758456d23dfa"),
                                                ("challenge", challenge),
                                                ("a", number), ("lang", "zh-cn"), ("callback", "")
                                            )
                                            self.RCR.header = self.BFR.format_to_same(self.init_header)
                                            self.RCR.header.update({
                                                "Accept": "*/*",
                                                "Host": "api-na.geetest.com",
                                                "Referer": referer_url
                                            })
                                            if self.RCR.request_to_get():
                                                get_json = self.RCR.page_source.strip("()")
                                                get_json = self.BPR.parse_to_dict(get_json)
                                                validate, temp_list = self.BPR.parse_to_path("$.data.validate",
                                                                                             get_json)
                                                cap_url, temp_list = self.BPR.parse_to_regex(
                                                    "url=(.*)", captcha_url)
                                                self.logger.info(cap_url)
                                                if not validate or not cap_url:
                                                    self.logger.info(f"认证提交地址错误(*>﹏<*)【{captcha_url}】")
                                                    self.callback_msg = "认证提交地址错误"
                                                    return self.process_to_verify(captcha_url, referer_url, count + 1, max_count)
                                                else:
                                                    # # # 提交认证
                                                    self.RCR.url = "https://makeabooking.flyscoot.com" + cap_url
                                                    self.RCR.param_data = None
                                                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                                                    self.RCR.header.update({
                                                        "Accept": "*/*",
                                                        "Content-Type": "application/x-www-form-urlencoded",
                                                        "Host": "makeabooking.flyscoot.com",
                                                        "Origin": "https://makeabooking.flyscoot.com",
                                                        "Referer": referer_url,
                                                        "X-Distil-Ajax": self.ajax_header
                                                    })
                                                    self.RCR.post_data = [
                                                        ("dCF_ticket", ""), ("geetest_challenge", challenge),
                                                        ("geetest_validate", validate),
                                                        ("geetest_seccode", f"{validate}|jordan"),
                                                        ("isAjax", "1"),
                                                    ]
                                                    if self.RCR.request_to_post(status_code=204):
                                                        self.logger.info("语音识别认证成功(*^__^*)【verify】")
                                                        return True
            
            self.logger.info(f"认证第{count + 1}次超时或者错误(*>﹏<*)【verify】")
            self.callback_msg = f"认证第{count + 1}次超时或者错误"
            return self.process_to_verify(captcha_url, referer_url, count + 1, max_count)
    
    def process_to_login(self, count: int = 0, max_count: int = 1) -> bool:
        """Login process. 登录过程。

        Args:
        	count (int): 累计计数。
        	max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 解析登录首页
            self.RCR.url = "https://makeabooking.flyscoot.com/SkyAgent"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "makeabooking.flyscoot.com",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 获取token，tab id
                self.verify_token, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "input[name='__RequestVerificationToken']", self.RCR.page_source)
                self.tab_id, temp_list = self.BPR.parse_to_regex("id: '(.*?)'", self.RCR.page_source)
                if self.verify_token and self.tab_id:
                    # # # 解析登录后状态，判断是否成功
                    self.RCR.url = "https://makeabooking.flyscoot.com/SkyAgent"
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Host": "makeabooking.flyscoot.com",
                        "Origin": "https://makeabooking.flyscoot.com",
                        "Referer": "https://makeabooking.flyscoot.com/SkyAgent",
                        "Upgrade-Insecure-Requests": "1"
                    })
                    self.RCR.post_data = [
                        ("__RequestVerificationToken", self.verify_token),
                        ("agentLogin.Login", self.CPR.username), ("agentLogin.Password", self.CPR.password),
                        ("__tabid", self.tab_id)
                    ]
                    if self.RCR.request_to_post(status_code=302):
                        # # # 解析跳转
                        self.RCR.url = "https://makeabooking.flyscoot.com/SkyAgent/AgentBooking"
                        self.RCR.param_data = None
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Host": "makeabooking.flyscoot.com",
                            "Referer": "https://makeabooking.flyscoot.com/SkyAgent",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        if self.RCR.request_to_get():
                            # # # 判断是否错误
                            error_message, temp_list = self.DPR.parse_to_attributes(
                                "class", "css", "div.error-mess>div.bg-danger", self.RCR.page_source)
                            if error_message:
                                self.logger.info(f"账号或者密码错误(*>﹏<*)【{error_message}】")
                                self.callback_msg = "账号或者密码错误"
                                return False
                            else:
                                # # # 查询登录后名字
                                login_name, temp_list = self.DPR.parse_to_attributes(
                                    "text", "css", "div.total-booking__account span", self.RCR.page_source)
                                if not login_name:
                                    self.logger.info(f"匹配用户名字失败(*>﹏<*)【{login_name}】")
                                    self.callback_msg = "匹配用户名字失败"
                                    return self.process_to_login(count + 1, max_count)
                                else:
                                    # # # 查询登录后token和tab id
                                    self.verify_token, temp_list = self.DPR.parse_to_attributes(
                                        "value", "css",
                                        "form.form-booking.form-booking__return input[name='__RequestVerificationToken']",
                                        self.RCR.page_source)
                                    self.tab_id, temp_list = self.BPR.parse_to_regex("id: '(.*?)'", self.RCR.page_source)
                                    if self.verify_token and self.tab_id:
                                        self.logger.info("用户请求登录成功(*^__^*)【login】")
                                        return True
            
            self.logger.info(f"登录第{count + 1}次超时或者错误(*>﹏<*)【login】")
            self.callback_msg = f"登录第{count + 1}次超时或者错误"
            return self.process_to_login(count + 1, max_count)
    
    def process_to_search(self, count: int = 0, max_count: int = 1) -> bool:
        """Search process. 搜索过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = 'https://makeabooking.flyscoot.com/'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "makeabooking.flyscoot.com",
                "Origin": "https://makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/SkyAgent/AgentBooking",
                "Upgrade-Insecure-Requests": "1",
            })
            flight_date = self.DFR.format_to_transform(self.CPR.flight_date, "%Y-%m-%d")
            flight_date = flight_date.strftime("%m/%d/%Y")
            
            self.RCR.post_data = [
                ("__RequestVerificationToke", self.verify_token), ("revAvailabilitySearch.SearchInfo.Direction", "Oneway"),
                ("revAvailabilitySearch.SearchInfo.SearchStations[0].DepartureStationCode", self.CPR.departure_code),
                ("revAvailabilitySearch.SearchInfo.SearchStations[0].ArrivalStationCode", self.CPR.arrival_code),
                ("revAvailabilitySearch.SearchInfo.SearchStations[0].DepartureDate",
                 flight_date),
                ("revAvailabilitySearch.SearchInfo.SearchStations[1].DepartureDate", ""),
                ("revAvailabilitySearch.SearchInfo.AdultCount", self.CPR.adult_num),
                ("revAvailabilitySearch.SearchInfo.ChildrenCount", self.CPR.child_num),
                ("revAvailabilitySearch.SearchInfo.InfantCount", self.CPR.infant_num),
                ("revAvailabilitySearch.SearchInfo.PromoCode", self.CPR.promo),
                ("__tabid", self.tab_id)
            ]
            if self.RCR.request_to_post(status_code=302):
                # # #
                self.RCR.url = 'https://makeabooking.flyscoot.com/Book/Flight'
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Host": "makeabooking.flyscoot.com",
                    "Referer": "https://makeabooking.flyscoot.com/SkyAgent/AgentBooking",
                    "Upgrade-Insecure-Requests": "1",
                })
                if self.RCR.request_to_get():
                    
                    flight_table, temp_list = self.DPR.parse_to_attributes("id", "css", "#departure-results",
                                                                          self.RCR.page_source)
                    if not flight_table:
                        self.logger.info(f"查询不到航线信息(*>﹏<*)【{self.CPR.flight_num}】")
                        self.callback_msg = f"查询不到航线信息【{self.CPR.flight_num}】"
                        return False
                    else:
                        is_flight = 0  # 是否是匹配的航班
                        sell_keys, sell_list = self.DPR.parse_to_attributes(
                            "value", "css", "div[data-fare='fly'] input[id='revAvailabilitySelect_MarketKeys_0_']",
                            self.RCR.page_source)
                        if sell_list:
                            for i in sell_list:
                                base_segment = i.split("|")
                                if len(base_segment) >= 2:
                                    if "T1~" in base_segment[0]:
                                        self.logger.info(f"查询到坐席是特价(*>﹏<*)【{self.CPR.flight_num}】")
                                        self.callback_msg = "匹配到坐席T1舱,无法进行占位,请人工进行支付"
                                        return False
                                    base_flight = base_segment[1].split("^")
                                    flights = []
                                    for j in self.CPR.flight_num:
                                        carrier_code, temp_list = self.BPR.parse_to_regex("[a-zA-Z]+", j)
                                        flight_no, temp_list = self.BPR.parse_to_regex("\d+", j)
                                        flight_no = self.BFR.format_to_int(flight_no)
                                        if carrier_code and flight_no:
                                            flights.append(f"{carrier_code}{flight_no}")
                                    flight_num = []
                                    for j in base_flight:
                                        base_num = j.split("~ ")
                                        if len(base_num) >= 2:
                                            carrier_code = self.BPR.parse_to_clear(base_num[0])
                                            flight_no = self.BPR.parse_to_clear(base_num[1])
                                            flight_no, temp_list = self.BPR.parse_to_regex("\d+", flight_no)
                                            flight_no = self.BFR.format_to_int(flight_no)
                                            flight_num.append(f"{carrier_code}{flight_no}")
                                    if flight_num == flights:
                                        is_flight = 1
                                        self.key = i
                                        self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                        break
                        if not sell_list or not is_flight:
                            sell_keys, sell_list = self.DPR.parse_to_attributes(
                                "value", "css", "div[data-fare='flybag'] input["
                                              "id='revAvailabilitySelect_MarketKeys_0_']", self.RCR.page_source)
                            if sell_list:
                                for i in sell_list:
                                    base_segment = i.split("|")
                                    if len(base_segment) >= 2:
                                        base_flight = base_segment[1].split("^")
                                        flights = []
                                        for j in self.CPR.flight_num:
                                            carrier_code, temp_list = self.BPR.parse_to_regex("[a-zA-Z]+", j)
                                            flight_no, temp_list = self.BPR.parse_to_regex("\d+", j)
                                            flight_no = self.BFR.format_to_int(flight_no)
                                            if carrier_code and flight_no:
                                                flights.append(f"{carrier_code}{flight_no}")
                                        flight_num = []
                                        for j in base_flight:
                                            base_num = j.split("~ ")
                                            if len(base_num) >= 2:
                                                carrier_code = self.BPR.parse_to_clear(base_num[0])
                                                flight_no = self.BPR.parse_to_clear(base_num[1])
                                                flight_no, temp_list = self.BPR.parse_to_regex("\d+", flight_no)
                                                flight_no = self.BFR.format_to_int(flight_no)
                                                flight_num.append(f"{carrier_code}{flight_no}")
                                        if flight_num == flights:
                                            is_flight = 1
                                            self.key = i
                                            self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                            break
                            if not sell_list or not is_flight:
                                sell_keys, sell_list = self.DPR.parse_to_attributes(
                                    "value", "css",
                                    "div[data-fare='flybageat'] input[id='revAvailabilitySelect_MarketKeys_0_']", self.RCR.page_source)
                                if sell_list:
                                    for i in sell_list:
                                        base_segment = i.split("|")
                                        if len(base_segment) >= 2:
                                            base_flight = base_segment[1].split("^")
                                            flights = []
                                            for j in self.CPR.flight_num:
                                                carrier_code, temp_list = self.BPR.parse_to_regex("[a-zA-Z]+", j)
                                                flight_no, temp_list = self.BPR.parse_to_regex("\d+", j)
                                                flight_no = self.BFR.format_to_int(flight_no)
                                                if carrier_code and flight_no:
                                                    flights.append(f"{carrier_code}{flight_no}")
                                            flight_num = []
                                            for j in base_flight:
                                                base_num = j.split("~ ")
                                                if len(base_num) >= 2:
                                                    carrier_code = self.BPR.parse_to_clear(base_num[0])
                                                    flight_no = self.BPR.parse_to_clear(base_num[1])
                                                    flight_no, temp_list = self.BPR.parse_to_regex("\d+", flight_no)
                                                    flight_no = self.BFR.format_to_int(flight_no)
                                                    flight_num.append(f"{carrier_code}{flight_no}")
                                            if flight_num == flights:
                                                is_flight = 1
                                                self.key = i
                                                self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                                break
                                if not sell_list or not is_flight:
                                    sell_keys, sell_list = self.DPR.parse_to_attributes(
                                        "value", "css",
                                        "div[data-fare='biz'] input[id='revAvailabilitySelect_MarketKeys_0_']", self.RCR.page_source)
                                    if sell_list:
                                        for i in sell_list:
                                            base_segment = i.split("|")
                                            if len(base_segment) >= 2:
                                                base_flight = base_segment[1].split("^")
                                                flights = []
                                                for j in self.CPR.flight_num:
                                                    carrier_code, temp_list = self.BPR.parse_to_regex("[a-zA-Z]+", j)
                                                    flight_no, temp_list = self.BPR.parse_to_regex("\d+", j)
                                                    flight_no = self.BFR.format_to_int(flight_no)
                                                    if carrier_code and flight_no:
                                                        flights.append(f"{carrier_code}{flight_no}")
                                                flight_num = []
                                                for j in base_flight:
                                                    base_num = j.split("~ ")
                                                    if len(base_num) >= 2:
                                                        carrier_code = self.BPR.parse_to_clear(base_num[0])
                                                        flight_no = self.BPR.parse_to_clear(base_num[1])
                                                        flight_no, temp_list = self.BPR.parse_to_regex("\d+", flight_no)
                                                        flight_no = self.BFR.format_to_int(flight_no)
                                                        flight_num.append(f"{carrier_code}{flight_no}")
                                                if flight_num == flights:
                                                    is_flight = 1
                                                    self.key = i
                                                    self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                                    break
                        # # # 查询航线结果
                        if not is_flight:
                            self.logger.info(f"匹配不到航班信息(*>﹏<*)【{self.CPR.flight_num}】")
                            self.callback_msg = f"匹配不到航班信息【{self.CPR.flight_num}】"
                            return False
                        if not sell_list:
                            self.logger.info(f"匹配不到坐席信息(*>﹏<*)【{sell_list}】")
                            self.callback_msg = f"匹配不到坐席信息【{self.CPR.flight_num}】"
                            return False
                        self.RCR.url = 'https://makeabooking.flyscoot.com/BookApi/Summary'
                        self.RCR.param_data = None
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Accept": "text/plain, */*; q=0.01",
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "Host": "makeabooking.flyscoot.com",
                            "Origin": "https://makeabooking.flyscoot.com",
                            "Referer": "https://makeabooking.flyscoot.com/Book/Flight",
                            # "X-Distil-Ajax": self.ajax_header,
                            "X-Requested-With": "XMLHttpRequest"
                        })
                        self.RCR.post_data = [
                            ("revBookingSummary.MarketSellKeys[0]", self.key), ("__tabid", self.tab_id),
                            ("__RequestVerificationToken", self.verify_token),
                        ]
                        if self.RCR.request_to_post():
                            price, temp_list = self.DPR.parse_to_attributes(
                                "data-price-title", "css", "header[data-price-title]", self.RCR.page_source)
                            if price:
                                p, temp_list = self.BPR.parse_to_regex("\d.*", price)
                                c, temp_list = self.BPR.parse_to_regex("(.*?)\d", price)
                                if p and c:
                                    self.CPR.currency = c
                                    self.total_price = self.BFR.format_to_float(2, p)
                                    self.logger.info(f"匹配价格信息成功(*^__^*)【{self.CPR.currency}】【{self.total_price}】")
                                    return True
            
            self.logger.info(f"查询超时或者错误(*>﹏<*)【query】")
            self.callback_msg = f"查询超时或者错误"
            return False
    
    def process_to_query(self, count: int = 0, max_count: int = 1) -> bool:
        """Query process. 查询过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = 'https://makeabooking.flyscoot.com/Book/Flight'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "makeabooking.flyscoot.com",
                "Origin": "https://makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/Book/Flight",
                "Upgrade-Insecure-Requests": "1"
            })
            self.RCR.post_data = [
                ("__RequestVerificationToken", self.verify_token), ("revAvailabilitySelect.init", ""),
                ("revAvailabilitySelect.MarketKeys[0]", self.key), ("__tabid", self.tab_id),
                ("__scoot_page_info", '{"interactionCount":{"click":4,"scroll":7},"inputCount":22,"hasRetainContactDetail":""}'),
            ]
            if self.RCR.request_to_post(status_code=302):
                self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Passengers'
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Host": "makeabooking.flyscoot.com",
                    "Origin": "https://makeabooking.flyscoot.com",
                    "Referer": "https://makeabooking.flyscoot.com/Book/Flight",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    # # # 查询验证标签
                    content_url, temp_list = self.DPR.parse_to_attributes("content", "css", "meta[http-equiv=refresh]",
                                                                          self.RCR.page_source)
                    action_url, temp_list = self.DPR.parse_to_attributes("action", "css", "#distilCaptchaForm",
                                                                         self.RCR.page_source)
                    if content_url or action_url:
                        verify_url = "https://makeabooking.flyscoot.com/BookFlight/Passengers"
                        if content_url:
                            captcha_url = content_url
                        else:
                            captcha_url = action_url
                        if self.process_to_verify(captcha_url, verify_url):
                            return self.process_to_query(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("查询详情不走验证(*^__^*)【detail】")
                        return True
                        # # # 查询登录后token和tab id
                        # self.verify_token, temp_list = self.DPR.parse_as_attributes(
                        #     "css", "value",
                        #     "form[action='/BookFlight/Passengers'] input[name='__RequestVerificationToken']",
                        #     self.RCR.page_source)
                        # self.tab_id, temp_list = self.BPR.parse_to_regex("id: '(.*?)'", self.RCR.page_source)
                        # if self.verify_token and self.tab_id:
                        #     return True
            
            self.logger.info(f"查询第{count + 1}次超时或者错误(*>﹏<*)【detail】")
            self.callback_msg = f"查询第{count + 1}次超时或者错误"
            return self.process_to_query(count + 1, max_count)
    
    def process_to_service(self, count: int = 0, max_count: int = 1) -> bool:
        """Service process. 辅营过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 请求行李页面
            self.RCR.url = "https://makeabooking.flyscoot.com/SsrApi/Create"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": "makeabooking.flyscoot.com",
                "Origin": "https://makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/BookFlight/Passengers",
                # "X-Distil-Ajax": self.ajax_header,
                "X-Requested-With": "XMLHttpRequest"
            })
            # # # 拼接每个成人具体的参数
            for n, v in enumerate(self.CPR.adult_list):
                weight = v.get('baggage')
                kilogram = 0
                if weight:
                    for w in weight:
                        kilogram += self.BFR.format_to_int(w.get('weight'))
                    self.RCR.post_data = [
                        ("revSsr.SelectedSsrs", f"{self.CPR.departure_code}|{self.CPR.arrival_code}|{n}|BG{kilogram}"),
                        ("__tabid", self.tab_id), ("__RequestVerificationToken", self.verify_token),
                    ]
                    if not self.RCR.request_to_post("data", "json"):
                        self.logger.info(f"行李超时或者错误(*>﹏<*)【{weight}】")
                        self.callback_msg = f"行李第{count + 1}次超时或者错误"
                        return self.process_to_service(count + 1, max_count)
            # # # 拼接每个儿童具体的参数
            if self.CPR.child_num:
                for n, v in enumerate(self.CPR.child_list):
                    n += self.CPR.adult_num
                    weight = v.get('baggage')
                    kilogram = 0
                    if weight:
                        for w in weight:
                            kilogram += self.BFR.format_to_int(w.get('weight'))
                        self.RCR.post_data = [
                            ("revSsr.SelectedSsrs", f"{self.CPR.departure_code}|{self.CPR.arrival_code}|{n}|BG{kilogram}"),
                            ("__tabid", self.tab_id), ("__RequestVerificationToken", self.verify_token),
                        ]
                        if not self.RCR.request_to_post("data", "json"):
                            self.logger.info(f"行李超时或者错误(*>﹏<*)【{weight}】")
                            self.callback_msg = f"行李第{count + 1}次超时或者错误"
                            return self.process_to_service(count + 1, max_count)
            return True
    
    def process_to_passenger(self, count: int = 0, max_count: int = 1) -> bool:
        """Passenger process. 乘客过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 解析乘客页面
            self.RCR.url = "https://makeabooking.flyscoot.com/BookFlight/Passengers"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "makeabooking.flyscoot.com",
                "Origin": "https://makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/BookFlight/Passengers",
                "Upgrade-Insecure-Requests": "1"
            })
            self.RCR.post_data = [
                ("__RequestVerificationToken", self.verify_token), ("__tabid", self.tab_id),
                ("__scoot_page_info", '{"interactionCount":{"scroll":10,"click":18,"keyup":6},"inputCount":27,"hasRetainContactDetail":""}'),
            ]
            # # # 拼接每个成人具体的参数
            for n, v in enumerate(self.CPR.adult_list):
                sex = "MR"
                if v.get("gender") == "F":
                    sex = "MDM"
                elif v.get("gender") == "M":
                    sex = "MR"
                birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y-%m-%d")
                
                self.RCR.post_data.extend([
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Title", sex),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].First", v.get("first_name")),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Last", v.get("last_name")),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].DayOfBirth", birthday.day),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].MonthOfBirth", birthday.month),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].YearOfBirth", birthday.year),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Nationality", v.get("nationality")),
                    (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].IsEupx", "False"),
                ])
            # # # 拼接每个儿童具体的参数
            if self.CPR.child_num:
                for n, v in enumerate(self.CPR.child_list):
                    n += self.CPR.adult_num
                    sex = "MSTR"
                    if v.get("gender") == "F":
                        sex = "MISS"
                    elif v.get("gender") == "M":
                        sex = "MSTR"
                    birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y-%m-%d")
                    
                    self.RCR.post_data.extend([
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Title", sex),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].First", v.get("first_name")),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Last", v.get("last_name")),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].DayOfBirth", birthday.day),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].MonthOfBirth", birthday.month),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].YearOfBirth", birthday.year),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].Nationality", v.get("nationality")),
                        (f"revPassengersInput.PassengerInfantModels.PassengersInfo[{n}].IsEupx", "False"),
                    ])
            if self.RCR.request_to_post(status_code=302):
                # # #
                self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Seats'
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Host": "makeabooking.flyscoot.com",
                    "Referer": "https://makeabooking.flyscoot.com/BookFlight/Passengers",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    # # # 查询验证标签
                    content_url, temp_list = self.DPR.parse_to_attributes("content", "css", "meta[http-equiv=refresh]",
                                                                          self.RCR.page_source)
                    action_url, temp_list = self.DPR.parse_to_attributes("action", "css", "#distilCaptchaForm",
                                                                         self.RCR.page_source)
                    if content_url or action_url:
                        verify_url = "https://makeabooking.flyscoot.com/BookFlight/Seats"
                        if content_url:
                            captcha_url = content_url
                        else:
                            captcha_url = action_url
                        if self.process_to_verify(captcha_url, verify_url):
                            return self.process_to_passenger(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("查询乘客不走验证(*^__^*)【passenger】")
                        return True
            
            self.logger.info(f"乘客第{count + 1}次超时或者错误(*>﹏<*)【passenger】")
            self.callback_msg = f"乘客第{count + 1}次超时或者错误"
            return self.process_to_passenger(count + 1, max_count)
    
    def process_to_payment(self, count: int = 0, max_count: int = 1) -> bool:
        """Payment process. 支付过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Payment'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/BookFlight/Seats",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                print(self.RCR.page_source)
                captcha, temp_list = self.DPR.parse_to_attributes("id", "css", "#nocaptcha", self.RCR.page_source)
                if captcha:
                    self.logger.info("查询支付滑块出现(*>﹏<*)【payment】")
                    self.callback_msg = "查询支付滑块出现，请先人工站位"
                    return False
                self.hold_button, temp_list = self.DPR.parse_to_attributes(
                    "fee", "css", "a[aria-controls='HoldPayment'][data-method='HOLD']", self.RCR.page_source)
                if not self.hold_button:
                    self.logger.info("查询不到占舱按钮(*>﹏<*)【payment】")
                    self.callback_msg = "查询不到占舱按钮"
                    return self.process_to_payment(count + 1, max_count)
                else:
                    self.logger.info("匹配占舱按钮成功(*^__^*)【payment】")

                    baggage, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", "a[title='行李额'] span[class='price']", self.RCR.page_source)
                    baggage_price = 0
                    if baggage:
                        p, temp_list = self.BPR.parse_to_regex("\d.*", baggage)
                        baggage_price = self.BFR.format_to_float(2, p)
                        self.baggage_price = baggage_price
                    else:
                        self.baggage_price = -1

                    self.total_price += baggage_price
                    self.total_price = self.BFR.format_to_cut(2, self.total_price)
                    self.logger.info(f"匹配价格信息成功(*^__^*)【{self.CPR.currency}】【{self.total_price}】")
                    return True

            self.logger.info(f"支付第{count + 1}次超时或者错误(*>﹏<*)【payment】")
            self.callback_msg = f"支付第{count + 1}次超时或者错误"
            return self.process_to_payment(count + 1, max_count)
    
    def process_to_record(self, count: int = 0, max_count: int = 1) -> bool:
        """Record process. 订单过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 查询航线数据
            
            self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Payment'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "makeabooking.flyscoot.com",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://makeabooking.flyscoot.com",
                "Referer": "https://makeabooking.flyscoot.com/BookFlight/Payment",
                "Upgrade-Insecure-Requests": "1"
            })
            self.RCR.post_data = [
                ("__RequestVerificationToken", self.verify_token), ("revContactInput.ContactViewModel.Name.Title", "MR"),
                ("revContactInput.ContactViewModel.Name.First", self.CPR.contact_first),
                ("revContactInput.ContactViewModel.Name.Last", self.CPR.contact_last),
                ("revContactInput.WorkPhone.Code", "+86"), ("revContactInput.WorkPhone.Number", self.CPR.contact_mobile),
                ("revContactInput.OtherPhone.Code", "+86"), ("revContactInput.OtherPhone.Number", self.CPR.contact_mobile),
                ("revContactInput.ContactViewModel.EmailAddress", self.CPR.contact_email),
                ("revContactInput.IsEUBC", "False"),
                ("revContactInput.ContactViewModel.AddressLine1", "Room 1702, qingyun contemporary building, haidian"),
                ("revContactInput.ContactViewModel.City", "BEIJING"), ("revContactInput.ContactViewModel.CountryCode", "CN"),
                ("revContactInput.ContactViewModel.ProvinceState", "BJ"), ("revContactInput.ContactViewModel.PostalCode", "100000"),
                ("revContactInput.RetainDetails", "false"), ("init", ""), ("AllowedCardBinNumbers", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.CreditCardNumber]", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.AccountNumberId]", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.ExpirationMonth]", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.ExpirationYear]", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.HolderName]", ""),
                ("paymentFactoryInput.PaymentFields[ExternalPaymentInputViewModel.VerificationCode]", ""),
                ("init", ""),
                ("PaymentFields[AgencyPaymentInputViewModel.QuotedAmount]", self.total_price),
                ("paymentFactoryInput.PaymentFields[GooglePayViewModel.Signature]", ""),
                ("paymentFactoryInput.PaymentFields[GooglePayViewModel.CardType]", ""),
                ("paymentFactoryInput.SelectedPaymentMethodCode", "HOLD"), ("paymentFactoryInput.ccFee", self.hold_button),
                ("paymentFactoryInput.TabId", ""), ("acceptTermCheckbox", "on"), ("__tabid", self.tab_id),
            ]
            if self.RCR.request_to_post(status_code=302):
                captcha, temp_list = self.DPR.parse_to_attributes("id", "css", "#nocaptcha", self.RCR.page_source)
                if captcha:
                    self.logger.info("查询订单滑块出现(*>﹏<*)【record】")
                    self.callback_msg = "查询订单滑块出现，请先人工站位"
                    return False
                
                self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Commit'
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Host": "makeabooking.flyscoot.com",
                    "Referer": "https://makeabooking.flyscoot.com/BookFlight/Payment",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get(status_code=302):
                    # # # 查询验证标签
                    content_url, temp_list = self.DPR.parse_to_attributes("content", "css", "meta[http-equiv=refresh]",
                                                                          self.RCR.page_source)
                    action_url, temp_list = self.DPR.parse_to_attributes("action", "css", "#distilCaptchaForm",
                                                                         self.RCR.page_source)
                    if content_url or action_url:
                        verify_url = "https://makeabooking.flyscoot.com/BookFlight/Commit"
                        if content_url:
                            captcha_url = content_url
                        else:
                            captcha_url = action_url
                        if self.process_to_verify(captcha_url, verify_url):
                            return self.process_to_record(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("查询订单不走验证(*^__^*)【record】")
                        
                        self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/PostCommit'
                        self.RCR.param_data = None
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Host": "makeabooking.flyscoot.com",
                            "Referer": "https://makeabooking.flyscoot.com/BookFlight/Payment",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        if self.RCR.request_to_get(status_code=302):
                            self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Wait'
                            self.RCR.param_data = None
                            self.RCR.header = self.BFR.format_to_same(self.init_header)
                            self.RCR.header.update({
                                "Host": "makeabooking.flyscoot.com",
                                "Referer": "https://makeabooking.flyscoot.com/BookFlight/Payment",
                                "Upgrade-Insecure-Requests": "1"
                            })
                            if self.RCR.request_to_get():
                                self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Wait'
                                self.RCR.param_data = None
                                self.RCR.header = self.BFR.format_to_same(self.init_header)
                                self.RCR.header.update({
                                    "Host": "makeabooking.flyscoot.com",
                                    "Referer": "https://makeabooking.flyscoot.com/BookFlight/Wait",
                                    "Upgrade-Insecure-Requests": "1"
                                })
                                if self.RCR.request_to_get(status_code=302):
                                    self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/PreConfirmation'
                                    self.RCR.param_data = None
                                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                                    self.RCR.header.update({
                                        "Host": "makeabooking.flyscoot.com",
                                        "Referer": "https://makeabooking.flyscoot.com/BookFlight/Wait",
                                        "Upgrade-Insecure-Requests": "1"
                                    })
                                    if self.RCR.request_to_get(status_code=302):
                                        
                                        self.RCR.url = 'https://makeabooking.flyscoot.com/BookFlight/Confirmation'
                                        self.RCR.param_data = None
                                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                                        self.RCR.header.update({
                                            "Host": "makeabooking.flyscoot.com",
                                            "Referer": "https://makeabooking.flyscoot.com/BookFlight/Wait",
                                            "Upgrade-Insecure-Requests": "1"
                                        })
                                        if self.RCR.request_to_get():
                                            
                                            self.record, temp_list = self.DPR.parse_to_attributes(
                                                "text", "css", "ul.booking-ref div.text-1", self.RCR.page_source)
                                            if self.record:
                                                last = self.DFR.format_to_now(custom_days=1)
                                                self.pnr_timeout = last.strftime("%Y-%m-%d %H:%M:%S")
                                                self.logger.info(f"匹配订单编号成功(*^__^*)【{self.record}】")
                                                return True
                                            else:
                                                self.logger.info("查询不到订单编号(*>﹏<*)【record】")
                                                self.callback_msg = "查询不到订单编号"
                                                return self.process_to_record(count + 1, max_count)
            
            self.logger.info(f"订单第{count + 1}次超时或者错误(*>﹏<*)【record】")
            self.callback_msg = f"订单第{count + 1}次超时或者错误"
            return self.process_to_record(count + 1, max_count)
    
    def process_to_return(self) -> bool:
        """Return process. 返回过程。

        Returns:
            bool
        """
        self.callback_data["success"] = "true"
        self.callback_data['msg'] = "占舱成功"
        self.callback_data["occupyCabinId"] = self.CPR.task_id
        self.callback_data['totalPrice'] = self.total_price
        self.callback_data["currency"] = self.CPR.currency
        self.callback_data['pnrCode'] = self.record
        self.callback_data["pnrTimeout"] = self.pnr_timeout
        self.callback_data['orderSrc'] = self.CPR.return_order
        self.callback_data["carrierAccount"] = ""
        self.callback_data['carrierAccountAgent'] = self.CPR.username
        self.callback_data["baggagePrice"] = self.baggage_price
        self.callback_data['passengerBaggages'] = self.CPR.return_baggage
        self.logger.info(self.callback_data)
        return True
    
