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
from collector.corpsl_mirror import CorpSLMirror
from detector.corpsl_simulator import CorpSLSimulator


class CorpSLScraper(RequestWorker):
    """SL采集器，SL网站流程交互，企业账号不支持并发。"""
    
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
        self.CMR = CorpSLMirror()  # SL镜像器。
        self.CSR = CorpSLSimulator()  # SL模拟器。
        # # # 过程中重要的参数。
        self.temp_source: str = ""                  # 临时源数据
        self.temp_source2: str = ""
        self.captcha_num: str = ""                  # 打码数字
        self.login_target: str = ""                 # 登录t
        self.user_hdn: str = ""                     # 登录user hdn
        self.query_string: str = ""                 # 查询字符串
        self.hold_button: str = "49"                # 占舱按钮
        # # # 返回中用到的变量。
        self.single_price: float = 0.0              # 单价
        self.total_price: float = 0.0               # 总价
        self.fare_price: float = 0.0                # 票面价
        self.fare_tax: float = 0.0                  # 税
        self.baggage_price: float = -1              # 行李总价
        self.record: str = ""                       # 票号
        self.pnr_timeout: str = ""                  # 票号超时时间
    
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
        self.CMR.logger = self.logger
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
        self.user_agent, self.init_header = self.RCR.build_to_header("Chrome")
        self.RCR.timeout = 40
        # # # 主体流程。
        if self.process_to_verify(max_count=self.retry_count):
            if self.process_to_search(max_count=self.retry_count):
                if self.process_to_query(max_count=self.retry_count):
                    if self.process_to_passenger(max_count=self.retry_count):
                        if self.process_to_service(max_count=self.retry_count):
                            if self.process_to_payment(max_count=self.retry_count):
                                if self.process_to_record(max_count=self.retry_count):
                                    self.process_to_return()
                                    self.process_to_logout(max_count=self.retry_count)
                                    self.logger.removeHandler(self.handler)
                                    return self.callback_data
        # # # 错误返回。
        self.callback_data["occupyCabinId"] = self.CPR.task_id
        self.callback_data['msg'] = self.callback_msg
        # self.callback_data['msg'] = "解决问题中，请手工站位。"
        self.callback_data["carrierAccount"] = ""
        self.callback_data['carrierAccountAgent'] = self.CPR.username
        self.logger.info(self.callback_data)
        self.process_to_logout(max_count=self.retry_count)
        self.logger.removeHandler(self.handler)
        return self.callback_data

    def process_to_verify(self, count: int = 0, max_count: int = 3) -> bool:
        """Verify process. 验证过程。

        Args:
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            # # # 爬取登录首页
            self.RCR.url = "https://agent.lionairthai.com/b2badmin/login.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 解析首页获取打码地址，并保存首页源代码
                self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                captcha, temp_list = self.DPR.parse_to_attributes(
                    "src", "css", "#ucAgentLogin_rdCapImage_CaptchaImageUP", self.RCR.page_source)
                if captcha:
                    # # # 爬取打码图片
                    self.RCR.url = captcha.replace("..", "https://agent.lionairthai.com")
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                        "Host": "agent.lionairthai.com",
                        "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx"
                    })
                    if self.RCR.request_to_get("content"):
                        captcha_page = self.BFR.format_to_same(self.RCR.page_source)
                        # # # 先进行接口打码
                        self.RCR.url = "http://45.81.129.1:33333/captcha/sl/"
                        self.RCR.param_data = None
                        self.RCR.header = None
                        self.RCR.post_data = {"img": self.RCR.page_source}
                        if self.RCR.request_to_post("files", "json"):
                            self.captcha_num = self.RCR.page_source.get('result')
                        else:
                            # # # 失败则进行自定义打码
                            code_string = self.CSR.recognize_to_captcha("img/cap.jpg", captcha_page)
                            code_regex, code_list = self.BPR.parse_to_regex("\d+", code_string)
                            if code_list:
                                code_all = ""
                                for i in code_list:
                                    code_all += i
                                self.captcha_num = code_all
                        # # # 判断打码准确性
                        if len(self.captcha_num) != 6:
                            self.logger.info(f"打码认证数字失败(*>﹏<*)【{self.captcha_num}】")
                            self.callback_msg = f"认证第{count + 1}次超时或者错误"
                            return self.process_to_verify(count + 1, max_count)
                        else:
                            # # # 判断是否需要重新打码
                            self.logger.info(f"打码图片数字成功(*^__^*)【{self.captcha_num}】")
                            if self.process_to_login():
                                return True
                            else:
                                if "enter a valid verification code" not in self.callback_msg:
                                    return False
                                else:
                                    self.logger.info(f"打码认证返回无效(*>﹏<*)【{self.captcha_num}】")
                                    self.callback_msg = f"认证第{count + 1}次超时或者错误"
                                    return self.process_to_verify(count + 1, max_count)
                                
            self.logger.info(f"认证第{count + 1}次超时或者错误(*>﹏<*)【verify】")
            self.callback_msg = f"认证第{count + 1}次超时或者错误"
            return self.process_to_verify(count + 1, max_count)

    def process_to_login(self, count: int = 0, max_count: int = 2) -> bool:
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
            self.RCR.url = "https://agent.lionairthai.com/b2badmin/login.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": "agent.lionairthai.com",
                "Origin": "https://agent.lionairthai.com",
                "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx",
                "X-MicrosoftAjax": "Delta=true",
                "X-Requested-With": "XMLHttpRequest"
            })
            # # # 拼接请求参数
            login_rad, temp_list = self.BPR.parse_to_regex('%3b%3bSystem.Web.Extensions.*?"', self.temp_source)
            login_rad = login_rad.strip('"')
            self.user_hdn, temp_list = self.DPR.parse_to_attributes(
                "value", "css", "#hdnCustomerUserID", self.temp_source)
            password = self.AFR.decrypt_into_aes(self.AFR.encrypt_into_sha1(self.AFR.password_key), self.CPR.password)
            param_batch = [
                ("ucAgentLogin$RadScrMgr", False, "ucAgentLogin$UpdatePanel1|ucAgentLogin$btnLogin"),
                ("__LASTFOCUS", True, "#__LASTFOCUS"), ("ucAgentLogin_RadScrMgr_TSM", False, login_rad),
                ("__EVENTTARGET", True, "#__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"), ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                ("__EVENTVALIDATION", True, "#__EVENTVALIDATION"), ("hdnCustomerUserID", False, self.user_hdn),
                ("hdnLangCode", True, "#hdnLangCode"),
                ("ucAgentLogin$hdfCustomerUserID", True, "#ucAgentLogin_hdfCustomerUserID"),
                ("ucAgentLogin$txtUserName", False, self.CPR.username),
                ("ucAgentLogin$txtPassword", False, password),
                ("ucAgentLogin$rdCapImage$CaptchaTextBox", False, self.captcha_num),
                ("ucAgentLogin_rdCapImage_ClientState", True, "#ucAgentLogin_rdCapImage_ClientState"),
                ("ucAgentLogin$cssversion", True, "#ucAgentLogin_cssversion"), ("__ASYNCPOST", False, "true"),
                ("ucAgentLogin$btnLogin", True, "#ucAgentLogin_btnLogin"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            if self.RCR.request_to_post():
                # # # 解析登录后状态，判断是否成功
                error_message, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "#ucAgentLogin_lblMessage", self.RCR.page_source)
                if error_message:
                    if "already in Use" in error_message:
                        self.logger.info(f"账户已被他人占用(*>﹏<*)【{error_message}】")
                        self.callback_msg = "账户已被他人占用"
                        return False
                    else:
                        self.logger.info(f"用户请求登录失败(*>﹏<*)【{error_message}】")
                        self.callback_msg = f"用户请求登录失败【{error_message}】"
                        return False
                else:
                    # # # 获取用户访问状态t=id
                    b2b_admin, temp_list = self.BPR.parse_to_regex("B2BAdmin.*?\\|", self.RCR.page_source)
                    login_target, temp_list = self.BPR.parse_to_regex("%3d.*", b2b_admin)
                    if not login_target or len(login_target) <= 4:
                        self.logger.info("匹配用户状态失败(*>﹏<*)【login】")
                        self.callback_msg = "匹配用户状态失败"
                        return self.process_to_login(count + 1, max_count)
                    else:
                        self.login_target = login_target[3:-1]
                        # # # 爬取登录后控制面板页
                        self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                        self.RCR.param_data = (("t", self.login_target),)
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            # "Host": "agent.lionairthai.com",
                            "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        if self.RCR.request_to_get(is_redirect=True):
                            self.temp_source2 = self.BFR.format_to_same(self.RCR.page_source)
                            self.logger.info("用户请求登录成功(*^__^*)【login】")
                            return True

            self.logger.info(f"登录第{count + 1}次超时或者错误(*>﹏<*)【login】")
            self.callback_msg = f"登录第{count + 1}次超时或者错误"
            return self.process_to_login(count + 1, max_count)

    def process_to_logout(self, count: int = 0, max_count: int = 2) -> bool:
        """Logout process. 退出过程。

        Args:
        	count (int): 累计计数。
        	max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.logger.info("(*^__^*)(*^__^*)用户退出程序开始(*^__^*)(*^__^*)")
            # # # 解析登录，认证
            if not self.process_to_verify():
                return False
            else:
                # # # 解析退出页面
                self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                self.RCR.param_data = (("t", self.login_target),)
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}"
                })
                # # # 拼接参数，解析退出
                logout_rad, temp_list = self.BPR.parse_to_regex('%3b%3bSystem.Web.Extensions.*?"', self.temp_source2)
                logout_rad = logout_rad.strip('"')
                param_batch = [
                    ("RadScriptManager1_TSM", False, logout_rad),
                    ("__EVENTTARGET", False, "ctl00$btnLogout"),
                    ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                    ("__VIEWSTATE", True, "#__VIEWSTATE"),
                    ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                    ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                    ("ctl00$bodycontent$txtSearch", False, ""),
                    ("ctl00$bodycontent$hdnphSearch", False, "Search+Here..."),
                    ("ctl00$bodycontent$hdnPopupShown", False, "True"),
                ]
                # # # 拼接每个页面具体的参数id
                mnu_id, mnu_list = self.DPR.parse_to_attributes(
                    "id", "css", "input[id*=lstmenudisplay_mnuId]", self.temp_source2)
                if mnu_list:
                    for i in range(len(mnu_list)):
                        param_batch.extend([
                            (f"ctl00$lstmenudisplay$ctrl{i}$mnuId", True, f"#lstmenudisplay_mnuId_{i}"),
                            (f"ctl00$lstmenudisplay$ctrl{i}$hdfPageName", True, f"#lstmenudisplay_hdfPageName_{i}"),
                        ])
                self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source2)
                if self.RCR.request_to_post(status_code=302):
                    # # # 爬取退出后页面确认状态
                    self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                    self.RCR.param_data = (("t", self.login_target),)
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Host": "agent.lionairthai.com",
                        "Origin": "https://agent.lionairthai.com",
                        "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}"
                    })
                    if self.RCR.request_to_get(status_code=302):
                        self.logger.info("用户退出请求成功(*^__^*)【logout】")
                        return True
    
            self.logger.info(f"退出第{count + 1}次超时或者错误(*>﹏<*)【logout】")
            self.callback_msg = f"退出第{count + 1}次超时或者错误"
            return self.process_to_logout(count + 1, max_count)

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
            # # # # 爬取登录后查询页
            flight_date = self.DFR.format_to_transform(self.CPR.flight_date, "%Y%m%d")
            query_string = (
                ("t", self.login_target), ("aid", self.user_hdn), ("culture", "en-GB"), ("b2b", "0"),
                ("sid", ""), ("culture1", "en-GB"), ("Jtype", "1"), ("depCity", self.CPR.departure_code),
                ("arrCity", self.CPR.arrival_code),
                ("depDate", f"{flight_date.day}/{flight_date.month}/{flight_date.year}"),
                ("adult1", self.CPR.adult_num), ("child1", self.CPR.child_num), ("infant1", self.CPR.infant_num),
                ("currency", "THB"), ("promotioncode", self.CPR.promo),
            )
            # # # 转义查询url
            self.query_string = self.BPR.parse_to_url(query_string)
            # # # 爬取查询重定向页
            self.RCR.url = "https://agent.lionairthai.com/default.aspx"
            self.RCR.param_data = query_string
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/FlightSearch.aspx?t={self.login_target}",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 爬取查询后页面
                self.RCR.url = "https://agent.lionairthai.com/SL/Flight.aspx"
                self.RCR.param_data = query_string
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Host": "agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/default.aspx?{self.query_string}",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    # # # 保存临时页面
                    self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                    return True
                    
            self.logger.info(f"查询第{count + 1}次超时或者错误(*>﹏<*)【query】")
            self.callback_msg = f"查询第{count + 1}次超时或者错误"
            return self.process_to_search(count + 1, max_count)

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
            # # # 查询航线数据
            self.RCR.url = "https://agent.lionairthai.com/SL/Flight.aspx/GetFlightSearch"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json; charset=UTF-8",
                "Host": "agent.lionairthai.com",
                "Origin": "https://agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/Flight.aspx?{self.query_string}"
            })
            self.RCR.post_data = {"t": self.login_target}
            if self.RCR.request_to_post("json", "json"):
                all_data = self.RCR.page_source.get('d')
                if not all_data:
                    self.logger.info(f"查询不到航线信息(*>﹏<*)【{self.RCR.page_source}】")
                    self.callback_msg = f"查询不到航线信息【{self.RCR.page_source}】"
                    return False
                # # # 解析接口航班号。
                interface_carrier = self.CPR.flight_num[:2]
                interface_no = self.CPR.flight_num[2:]
                interface_no = self.BFR.format_to_int(interface_no)
                # # # 匹配航班
                base_data = None
                is_flight = False
                for i in all_data:
                    segment_num = i.get('SegmentInformation')
                    if not segment_num or len(segment_num) != self.CPR.segment_num:
                        continue
                    source_carrier, temp_list = self.BPR.parse_to_path('$.[0].MACode', segment_num)
                    source_no, temp_list = self.BPR.parse_to_path('$.[0].FlightNo', segment_num)
                    if source_carrier and source_no:
                        source_carrier = self.BPR.parse_to_clear(source_carrier)
                        source_no = self.BPR.parse_to_clear(source_no)
                        source_no = self.BFR.format_to_int(source_no)
                    # # # 匹配航班号。
                    if interface_carrier == source_carrier and interface_no == source_no:
                        is_flight = True
                        base_data = i
                        self.logger.info(f"匹配航班信息成功(*^__^*)【{self.CPR.flight_num}】")
                        break
                  
                if not is_flight:
                    self.logger.info(f"匹配不到航班信息(*>﹏<*)【{self.CPR.flight_num}】")
                    self.callback_msg = f"匹配不到航班信息【{self.CPR.flight_num}】"
                    return False
                # # # 获取各种参数
                is_actual = base_data.get('IsActualData')
                if is_actual:
                    is_actual = 1
                else:
                    is_actual = 0
                OBAF_Index = base_data.get('AFIndex')
                OB_Index = base_data.get('FlightIndex')
                
                OB_Class, temp_list = self.BPR.parse_to_path("$.PromoFlight.outBoundFlights[0].Segments[0].ClassCode", base_data)
                self.single_price, temp_list = self.BPR.parse_to_path("$.PromoFlight.priceInfo.PkgAmt", base_data)
                self.CPR.currency, temp_list = self.BPR.parse_to_path("$.PromoFlight.CurrencyCode", base_data)
                self.total_price, temp_list = self.BPR.parse_to_path("$.PromoFlight.priceInfo.TotalPrice", base_data)
                self.fare_price, temp_list = self.BPR.parse_to_path("$.PromoFlight.priceInfo.BaseFarePrice", base_data)
                self.fare_tax, temp_list = self.BPR.parse_to_path("$.PromoFlight.priceInfo.TotalTax", base_data)
                if not OB_Class:
                    OB_Class, temp_list = self.BPR.parse_to_path("$.EconomyFlight.outBoundFlights[0].Segments[0].ClassCode", base_data)
                    self.single_price, temp_list = self.BPR.parse_to_path("$.EconomyFlight.priceInfo.PkgAmt", base_data)
                    self.CPR.currency, temp_list = self.BPR.parse_to_path("$.EconomyFlight.CurrencyCode", base_data)
                    self.total_price, temp_list = self.BPR.parse_to_path("$.EconomyFlight.priceInfo.TotalPrice", base_data)
                    self.fare_price, temp_list = self.BPR.parse_to_path("$.EconomyFlight.priceInfo.BaseFarePrice", base_data)
                    self.fare_tax, temp_list = self.BPR.parse_to_path("$.EconomyFlight.priceInfo.TotalTax", base_data)
                    if not OB_Class:
                        OB_Class, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.outBoundFlights[0].Segments[0].ClassCode", base_data)
                        self.single_price, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.priceInfo.PkgAmt", base_data)
                        self.CPR.currency, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.CurrencyCode", base_data)
                        self.total_price, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.priceInfo.TotalPrice", base_data)
                        self.fare_price, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.priceInfo.BaseFarePrice", base_data)
                        self.fare_tax, temp_list = self.BPR.parse_to_path("$.PremiumEconomyFlight.priceInfo.TotalTax", base_data)
                        if not OB_Class:
                            self.logger.info(f"匹配不到坐席信息(*>﹏<*)【{base_data}】")
                            self.callback_msg = f"匹配不到坐席信息【{self.CPR.flight_num}】"
                            return False

                self.single_price = self.BFR.format_to_cut(2, self.single_price)
                self.total_price = self.BFR.format_to_cut(2, self.total_price)
                self.fare_price = self.BFR.format_to_cut(2, self.fare_price)
                self.fare_tax = self.BFR.format_to_cut(2, self.fare_tax)
                self.logger.info(f"匹配价格信息成功(*^__^*)【{self.CPR.currency}】【{self.total_price}】")
                # # # 请求过程
                self.RCR.url = 'https://agent.lionairthai.com/SL/Flight.aspx/GetPackageSummary'
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Content-Type": "application/json; charset=UTF-8",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/SL/Flight.aspx?{self.query_string}",
                    "X-Requested-With": "XMLHttpRequest"
                })
                # # # 拼接参数
                IBAF_Index, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "#hfIBAFIndex", self.temp_source)
                IB_Class, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "#hfIBClass", self.temp_source)
                IB_Index, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "#hfIBIndex", self.temp_source)
                IB_Category, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "#hfIBCategory", self.temp_source)
                Insurance_Status, temp_list = self.DPR.parse_to_attributes(
                    "value", "css", "#hfInsuranceStatus", self.temp_source)
                post_string = f'{{"OBIndex": "{OB_Index}", "OBClass": "{OB_Class}", "OBAFIndex": "{OBAF_Index}", ' \
                    f'"IBIndex": "{IBAF_Index}", "IBClass": "{IB_Class}", "IBAFIndex": "{IB_Index}", ' \
                    f'"InsuranceStatus": "{Insurance_Status}", "IBCategory": "{IB_Category}", ' \
                    f'"OBCategory": "OB", "IsInsSelectCall":false}}'
                self.RCR.post_data = {'Req': post_string, 't': self.login_target}
                if self.RCR.request_to_post("json", "json"):
                    # # # 请求查询
                    self.RCR.url = "https://agent.lionairthai.com/SL/Flight.aspx"
                    flight_date = self.DFR.format_to_transform(self.CPR.flight_date, "%Y%m%d")
                    self.RCR.param_data = (
                        ("t", self.login_target), ("aid", self.user_hdn), ("culture", "en-GB"), ("b2b", "0"),
                        ("sid", ""), ("culture1", "en-GB"), ("Jtype", "1"), ("depCity", self.CPR.departure_code),
                        ("arrCity", self.CPR.arrival_code),
                        ("depDate", f"{flight_date.day}/{flight_date.month}/{flight_date.year}"),
                        ("adult1", self.CPR.adult_num), ("child1", self.CPR.child_num), ("infant1", self.CPR.infant_num),
                        ("currency", "THB"), ("promotioncode", self.CPR.promo),
                    )
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Host": "agent.lionairthai.com",
                        "Origin": "https://agent.lionairthai.com",
                        "Referer": f"https://agent.lionairthai.com/SL/Flight.aspx?{self.query_string}",
                        "Upgrade-Insecure-Requests": "1"
                    })
    
                    param_batch = [
                        ("__EVENTTARGET", False, "FlightSelected"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                        ("__VSTATE", True, "#__VSTATE"), ("__VIEWSTATE", True, "#__VIEWSTATE"),
                        ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"), ("__EVENTVALIDATION", True, "#__EVENTVALIDATION"),
                        ("hfOBAFIndex", False, OBAF_Index), ("hfIBAFIndex", False, IBAF_Index), ("hfOBClass", False, OB_Class),
                        ("hfIBClass", False, IB_Class), ("hfOBIndex", False, OB_Index), ("hfIBIndex", False, IB_Index),
                        ("hfOBCategory", False, "OB"), ("hfIBCategory", False, IB_Category),
                        ("hfIsFlightSelected", True, "#hfIsFlightSelected"), ("hfIncuConfMsg", True, "#hfIncuConfMsg"),
                        ("hfIsSubmitted", True, "#hfIsSubmitted"), ("hfIsClear", True, "#hfIsClear"),
                        ("hdfFromBookingPage", True, "#hdfFromBookingPage"),
                        ("hdnSelectedFlightValue", True, "#hdnSelectedFlightValue"),
                        ("hdnIsAcceptMultiSearch", True, "#hdnIsAcceptMultiSearch"),
                        ("IsFlightConfirmed", True, "#IsFlightConfirmed"), ("isT", True, "#isT"),
                        ("hdnIsfbtB2B", True, "#hdnIsfbtB2B"), ("hdnFBT", True, "#hdnFBT"),
                        ("hfIsActualData", False, is_actual), ("hdnNoVisaErrMsg", True, "#hdnNoVisaErrMsg"),
                        ("hdnDepCities", True, "#hdnDepCities"), ("hdnArrCities", True, "#hdnArrCities"),
                        ("hdnFlightResults", True, "#hdnFlightResults"), ("hdnActualFlightRes", True, "#hdnActualFlightRes"),
                        ("hdnCUlanguage", True, "#hdnCUlanguage"), ("hfCustomerID", True, "#hfCustomerID"),
                        ("hfLanguageCode", True, "#hfLanguageCode"), ("hdnONDayText", True, "#hdnONDayText"),
                        ("hdnONDaysText", True, "#hdnONDaysText"), ("hdnBasePath", True, "#hdnBasePath"),
                        ("hfInsuranceStatus", False, Insurance_Status), ("hdnSearchActivityId", True, "#hdnSearchActivityId"),
                        ("hfDepartureDay", True, "#hfDepartureDay"), ("hfArrivalDay", True, "#hfArrivalDay"),
                        ("hdnIsGoogleCaptchaEnabled", False, "TRUE"), ("rdCapImage$CaptchaTextBox", False, ""),
                        ("rdCapImage_ClientState", False, ""),
                        ("ucSessiontimeOut$hdnShowSession", True, "#ucSessiontimeOut_hdnShowSession"),
                        ("ucSessiontimeOut$hdnSessionout", True, "#ucSessiontimeOut_hdnSessionout"),
                        ("ucSessiontimeOut$hdnshowpopup", True, "#ucSessiontimeOut_hdnshowpopup"),
                        ("ucSessiontimeOut$hdnCUID", True, "#ucSessiontimeOut_hdnCUID"),
                        ("hfIsConfirmRouteChargePopup", True, "#hfIsConfirmRouteChargePopup"),
                        ("ucMiniSearch$hfSlider", True, "#ucMiniSearch_hfSlider"), ("aid", True, "#aid"),
                        ("df", True, "#df"), ("culture", True, "#culture"), ("afid", True, "#afid"),
                        ("b2b", True, "#b2b"), ("St", True, "#St"), ("roomcount", True, "#roomcount"),
                        ("councode", True, "#councode"),
                        ("ucMiniSearch$hdnDepList", True, "#ucMiniSearch_hdnDepList"),
                        ("ucMiniSearch$hdnDesList", True, "#ucMiniSearch_hdnDesList"),
                        ("ucMiniSearch$hfJourneyType", True, "#ucMiniSearch_hfJourneyType"),
                        ("ucMiniSearch$hdnJType", True, "#ucMiniSearch_hdnJType"),
                        ("ucMiniSearch$hfMissingSelection", True, "#ucMiniSearch_hfMissingSelection"),
                        ("ucMiniSearch$hdnMaxPax", True, "#ucMiniSearch_hdnMaxPax"),
                        ("ucMiniSearch$hdnMaxAdult", True, "#ucMiniSearch_hdnMaxAdult"),
                        ("ucMiniSearch$hdnIncludeInfant", True, "#ucMiniSearch_hdnIncludeInfant"),
                        ("ucMiniSearch$hdnFBType", True, "#ucMiniSearch_hdnFBType"),
                        ("ucMiniSearch$hdnMinPax", True, "#ucMiniSearch_hdnMinPax"),
                        ("ucMiniSearch$hdnMinGBDays", True, "#ucMiniSearch_hdnMinGBDays"),
                        ("ucMiniSearch$hdnMaxGBDays", True, "#ucMiniSearch_hdnMaxGBDays"),
                        ("ucMiniSearch$hdnMinFVDays", True, "#ucMiniSearch_hdnMinFVDays"),
                        ("ucMiniSearch$hdnExcludeInfantText", True, "#ucMiniSearch_hdnExcludeInfantText"),
                        ("ucMiniSearch$hdnDateFormat", True, "#ucMiniSearch_hdnDateFormat"),
                        ("ucMiniSearch$hdnDepMinDate", True, "#ucMiniSearch_hdnDepMinDate"),
                        ("ucMiniSearch$hdnRetMinDate", True, "#ucMiniSearch_hdnRetMinDate"),
                        ("ucMiniSearch$hdnDepMaxDate", True, "#ucMiniSearch_hdnDepMaxDate"),
                        ("ucMiniSearch$hdnRetMaxDate", True, "#ucMiniSearch_hdnRetMaxDate"),
                        ("ucMiniSearch$hdnDepDate", True, "#ucMiniSearch_hdnDepDate"),
                        ("ucMiniSearch$hdnretDate", True, "#ucMiniSearch_hdnretDate"),
                        ("ucMiniSearch$hdnltPaxError", True, "#ucMiniSearch_hdnltPaxError"),
                        ("ucMiniSearch$hdnltMaxPaxError", True, "#ucMiniSearch_hdnltMaxPaxError"),
                        ("ucMiniSearch$hdnltErrPassengers", True, "#ucMiniSearch_hdnltErrPassengers"),
                        ("ucMiniSearch$hdnPromoType", True, "#ucMiniSearch_hdnPromoType"),
                        ("ucMiniSearch$hdnIsTimeoutSearch", True, "#ucMiniSearch_hdnIsTimeoutSearch"),
                        ("ucMiniSearch$hdnIsChildLessThanAdult", True, "#ucMiniSearch_hdnIsChildLessThanAdult"),
                        ("ucMiniSearch$hdnltAdultChildMisMatchError", True, "#ucMiniSearch_hdnltAdultChildMisMatchError"),
                        ("ucMiniSearch$hdnltAdultChildInfantMisMatchError", True, "#ucMiniSearch_hdnltAdultChildInfantMisMatchError"),
                        ("ucMiniSearch$hdnCustomerUserId", True, "#ucMiniSearch_hdnCustomerUserId"),
                        ("ucMiniSearch$rdoJourneyType", False, 1),
                        ("ucMiniSearch$depCity", False, self.CPR.departure_code),
                        ("ucMiniSearch$arrCity", False, self.CPR.arrival_code),
                        ("ucMiniSearch$hfdepCity", False, self.CPR.departure_code),
                        ("ucMiniSearch$hfdepCityName", True, "#ucMiniSearch_hfdepCityName"),
                        ("ucMiniSearch$hfarrCity", False, self.CPR.arrival_code),
                        ("ucMiniSearch$hfarrCityName", True, "#ucMiniSearch_hfarrCityName"),
                        ("ucMiniSearch$hdnSelectCity", True, "#ucMiniSearch_hdnSelectCity"),
                        ("ucMiniSearch$hdnIsMini", True, "#ucMiniSearch_hdnIsMini"),
                        ("ucMiniSearch$dpd1", True, "#ucMiniSearch_dpd1"),
                        ("ucMiniSearch$ddlClass", False, 0),
                        ("ucMiniSearch$ddlDirectFlight", False, 1),
                        ("ucMiniSearch$ddlAdult", False, self.CPR.adult_num),
                        ("ucMiniSearch$ddlChild", False, self.CPR.child_num),
                        ("ucMiniSearch$ddlInfant", False, self.CPR.infant_num),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnSelectCity", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnSelectCity"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdntabID", False, self.login_target),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnDepCities", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnDepCities"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnArrCities", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnArrCities"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnDepcity", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnDepcity"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnArrCity", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnArrCity"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnDepDate", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnDepDate"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnLoading", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnLoading"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity1", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity1"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity2", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity2"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity3", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity3"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity4", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity4"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity5", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity5"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepcity6", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepcity6"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity1", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity1"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity2", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity2"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity3", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity3"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity4", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity4"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity5", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity5"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnarrcity6", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnarrcity6"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate1", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate1"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate2", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate2"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate3", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate3"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate4", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate4"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate5", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate5"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdndepdate6", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdndepdate6"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnAdultCount", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnAdultCount"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnChildCount", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnChildCount"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnInfantCount", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnInfantCount"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnCabinClass", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnCabinClass"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnSetRecentModifySearchLegCnt",
                         True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnSetRecentModifySearchLegCnt"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnMaxPaxTotCount", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnMaxPaxTotCount"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnMaxAdult", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnMaxAdult"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnMaxPax", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnMaxPax"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnIncludeInfant", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnIncludeInfant"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdninputtingSamecity",
                         True, "#ucMiniSearch_ucMLAirlineModifySrch_hdninputtingSamecity"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$hdnFillAllDetails", True, "#ucMiniSearch_ucMLAirlineModifySrch_hdnFillAllDetails"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep1", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep1"),
                        ("depCity", False, 0), ("arrCity", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep2", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep2"),
                        ("depCity", False, 0), ("arrCity", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep3", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep3"),
                        ("depCity", False, 0), ("arrCity", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep4", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep4"),
                        ("depCity", False, 0), ("arrCity", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep5", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep5"),
                        ("depCity", False, 0), ("arrCity", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$dpflightDep6", True, "#ucMiniSearch_ucMLAirlineModifySrch_dpflightDep6"),
                        ("ucMiniSearch$ucMLAirlineModifySrch$ddlAdult1", False, 1),
                        ("ucMiniSearch$ucMLAirlineModifySrch$ddlChild1", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$ddlInfant1", False, 0),
                        ("ucMiniSearch$ucMLAirlineModifySrch$ddlCabinClass", False, 1),
                    ]
                    self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
                    if self.RCR.request_to_post(status_code=302):
                        return True
                            
            self.logger.info(f"查询第{count + 1}次超时或者错误(*>﹏<*)【detail】")
            self.callback_msg = f"查询第{count + 1}次超时或者错误"
            return self.process_to_query(count + 1, max_count)

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
            self.RCR.url = "https://agent.lionairthai.com/SL/Passenger.aspx"
            self.RCR.param_data = (("t", self.login_target),)
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/Flight.aspx?{self.query_string}",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 拼接参数
                self.RCR.url = "https://agent.lionairthai.com/SL/Passenger.aspx"
                self.RCR.param_data = (("t", self.login_target),)
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/SL/Passenger.aspx?t={self.login_target}",
                    "X-MicrosoftAjax": "Delta=true",
                    "X-Requested-With": "XMLHttpRequest",
                })
                
                param_batch = [
                    ("ucPassenger1$ScriptManager1", False, "updateWrapper|btnConfirmPassenger"),
                    ("__EVENTTARGET", True, "__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                    ("__LASTFOCUS", True, "#__LASTFOCUS"), ("__VIEWSTATE", True, "#__VIEWSTATE"),
                    ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"), ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                    ("hdnPaxCount", True, "#hdnPaxCount"), ("hdnIsStudent", True, "#hdnIsStudent"),
                    ("hdnStudentFName", True, "#hdnStudentFName"), ("hdnStudentLName", True, "#hdnStudentLName"),
                    ("hdnIsStudentSlected", True, "#hdnIsStudentSlected"), ("hfCustomerID", True, "#hfCustomerID"),
                    ("hfLanguageCode", True, "#hfLanguageCode"), ("hdnCUlanguage", True, "#hdnCUlanguage"),
                    ("hdnBasePath", True, "#hdnBasePath"), ("hdnIsPassengerPage", True, "#hdnIsPassengerPage"),
                    ("hfInsuranceCurrStatus", True, "#hfInsuranceCurrStatus"), ("hfInsuranceInitStatus", True, "#hfInsuranceInitStatus"),
                    ("hfInsuranceInitValue", True, "#hfInsuranceInitValue"), ("hfInsuranceStatus", True, "#hfInsuranceStatus"),
                ]
                # # # 拼接每个成人具体的参数
                for n, v in enumerate(self.CPR.adult_list):
                    sex = "Mr."
                    if v.get("gender") == "F":
                        sex = "Ms."
                    elif v.get("gender") == "M":
                        sex = "Mr."
    
                    birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y%m%d")
                    nationality = self.CMR.select_to_nationality(v.get("nationality"))
                    
                    param_batch.extend([
                        (f"ucPassenger1$lstPassenger$ctrl{n}$hdfPassengers", False, n),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$hdfPassengerTitle",
                         True, f"#ucPassenger1_lstPassenger_hdfPassengerTitle_{n}"),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$TITLE$ddlTitle", False, sex),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$TITLE$hdnv", False, n),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$FIRSTNAME$txtFName", False, v.get("first_name")),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$FIRSTNAME$hdnv", False, n),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$LASTNAME$txtLName", False, v.get("last_name")),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$LASTNAME$hdnv", False, n),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnPaxType",
                         True, f"#ucPassenger1_lstPassenger_DATEOFBIRTH_{n}_hdnPaxType_{n}"),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnPrevAge", False, ""),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnIsMainPax",
                         True, f"#ucPassenger1_lstPassenger_DATEOFBIRTH_{n}_hdnIsMainPax_{n}"),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlDay", False, birthday.day),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlMonth", False, birthday.month),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlYear", False, birthday.year),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$NATIONALITY$hdnPaxIndex", False, n),
                        (f"ucPassenger1$lstPassenger$ctrl{n}$NATIONALITY$ddlNationality", False, nationality),
                    ])
                    
                    is_passport, temp_list = self.DPR.parse_to_attributes(
                        "id", "css", f"#ucPassenger1_lstPassenger_PASSPORTNO_{n}_txtPassNo_{n}", self.RCR.page_source)
                    if is_passport:
                        card_time = self.DFR.format_to_transform(v.get("card_expired"), "%Y%m%d")
                        param_batch.extend([
                            (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTNO$txtPassNo", False, v.get("card_num")),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTEXPIRYDATE$ddlPassDay",
                             False, card_time.day),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTEXPIRYDATE$ddlPassMonth",
                             False, card_time.month),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTEXPIRYDATE$ddlPassYear",
                             False, card_time.year),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTISSUECOUNTRY$ddlPassCountry",
                             False, v.get("card_place")),
                        ])
                # # # 拼接每个儿童具体的参数
                if self.CPR.child_num:
                    for n, v in enumerate(self.CPR.child_list):
                        n += self.CPR.adult_num
                        sex = "Mstr."
                        if v.get("gender") == "F":
                            sex = "Miss."
                        elif v.get("gender") == "M":
                            sex = "Mstr."
    
                        birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y%m%d")
    
                        param_batch.extend([
                            (f"ucPassenger1$lstPassenger$ctrl{n}$hdfPassengers", False, n),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$hdfPassengerTitle",
                             True, f"#ucPassenger1_lstPassenger_hdfPassengerTitle_{n}"),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$TITLE$ddlTitle", False, sex),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$TITLE$hdnv", False, n),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$FIRSTNAME$txtFName", False, v.get("first_name")),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$FIRSTNAME$hdnv", False, n),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$LASTNAME$txtLName", False, v.get("last_name")),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$LASTNAME$hdnv", False, n),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnPaxType",
                             True, f"#ucPassenger1_lstPassenger_DATEOFBIRTH_{n}_hdnPaxType_{n}"),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnPrevAge", False, ""),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$hdnIsMainPax",
                             True, f"#ucPassenger1_lstPassenger_DATEOFBIRTH_{n}_hdnIsMainPax_{n}"),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlDay", False, birthday.day),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlMonth", False, birthday.month),
                            (f"ucPassenger1$lstPassenger$ctrl{n}$DATEOFBIRTH$ddlYear", False, birthday.year),
                        ])
                        
                        is_passport, temp_list = self.DPR.parse_to_attributes(
                            "id", "css", f"#ucPassenger1_lstPassenger_PASSPORTNO_{n}_txtPassNo_{n}",
                            self.RCR.page_source)
                        if is_passport:
                            param_batch.extend([
                                (f"ucPassenger1$lstPassenger$ctrl{n}$PASSPORTNO$txtPassNo", False, v.get("card_num"))
                            ])
                param_batch.extend([
                    ("hdnIsGoogleCaptchaEnabled", True, "#hdnIsGoogleCaptchaEnabled"),
                    ("rdCapImage$CaptchaTextBox", True, "#rdCapImage_CaptchaTextBox"),
                    ("rdCapImage_ClientState", True, "#rdCapImage_ClientState"),
                    ("ucSessiontimeOut$hdnShowSession", True, "#ucSessiontimeOut_hdnShowSession"),
                    ("ucSessiontimeOut$hdnSessionout", True, "#ucSessiontimeOut_hdnSessionout"),
                    ("ucSessiontimeOut$hdnshowpopup", True, "#ucSessiontimeOut_hdnshowpopup"),
                    ("ucSessiontimeOut$hdnCUID", True, "#ucSessiontimeOut_hdnCUID"),
                    ("ucPackageSummary$htOptAddOnCurrency", True, "#ucPackageSummary_htOptAddOnCurrency"),
                    ("ucPackageSummary$lvDepFlightSegments$ctrl0$hdnLegIndex", True, "#ucPackageSummary_lvDepFlightSegments_hdnLegIndex_0"),
                    ("ucPackageSummary$hfOptSummaryBaseFare", False, self.fare_price),
                    ("ucPackageSummary$hfOptSummaryTax", False, self.fare_tax),
                    ("ucPackageSummary$hfOptSummaryLionFastPrice", True, "#ucPackageSummary_hfOptSummaryLionFastPrice"),
                    ("ucPackageSummary$hfOptSummarySmsPrice", True, "#ucPackageSummary_hfOptSummarySmsPrice"),
                    ("ucPackageSummary$hfOptSummaryComfyKitPrice", True, "#ucPackageSummary_hfOptSummaryComfyKitPrice"),
                    ("ucPackageSummary$hfOptSummarySOBPrice", True, "#ucPackageSummary_hfOptSummarySOBPrice"),
                    ("ucPackageSummary$hfOptSummaryTravelSIMPrice", True, "#ucPackageSummary_hfOptSummaryTravelSIMPrice"),
                    ("ucPackageSummary$hfOptSummaryTotalPrice", False, self.total_price),
                    ("hfIsCheckInsNotAvailPopup", True, "#hfIsCheckInsNotAvailPopup"),
                    ("txtFEmail", True, "#txtFEmail"), ("__ASYNCPOST", False, "true"),
                    ("btnConfirmPassenger", True, "#btnConfirmPassenger"),
                ])
                self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.page_source)
                if self.RCR.request_to_post():
                    return True
                
            self.logger.info(f"乘客第{count + 1}次超时或者错误(*>﹏<*)【passenger】")
            self.callback_msg = f"乘客第{count + 1}次超时或者错误"
            return self.process_to_passenger(count + 1, max_count)
        
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
            self.RCR.url = "https://agent.lionairthai.com/SL/OptionalAddOns.aspx"
            self.RCR.param_data = (("t", self.login_target),)
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/Passenger.aspx?t={self.login_target}",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 拼接参数
                self.RCR.url = "https://agent.lionairthai.com/SL/OptionalAddOns.aspx"
                self.RCR.param_data = (("t", self.login_target),)
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/SL/OptionalAddOns.aspx?t={self.login_target}",
                    "Upgrade-Insecure-Requests": "1"
                })
                
                param_batch = [
                    ("__EVENTTARGET", True, "__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                    ("__VIEWSTATE", True, "#__VIEWSTATE"), ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                    ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                    ("hdnCurrency", False, self.CPR.currency), ("hdnRoundingDecimal", True, "#hdnRoundingDecimal"),
                    ("htTotalSeatPrice", True, "#htTotalSeatPrice"), ("hfTotalMealPrice", True, "#hfTotalMealPrice"),
                    ("hfTotalBaggagePrice", True, "#hfTotalBaggagePrice"), ("hdnMealsAvailable", True, "#hdnMealsAvailable"),
                    ("hdnBaggageAvailable", True, "#hdnBaggageAvailable"), ("hdnLoungeAvailable", True, "#hdnLoungeAvailable"),
                    ("hdnExistingSeatPrice", True, "#hdnExistingSeatPrice"), ("hdnExistingMealPrice", True, "#hdnExistingMealPrice"),
                    ("hfCustomerID", True, "#hfCustomerID"), ("hfLanguageCode", True, "#hfLanguageCode"),
                    ("hfInsuranceCurrStatus", True, "#hfInsuranceCurrStatus"), ("hfInsuranceInitStatus", True, "#hfInsuranceInitStatus"),
                    ("hfInsuranceInitValue", True, "#hfInsuranceInitValue"), ("hdnInsurancePaxInfo", True, "#hdnInsurancePaxInfo"),
                    ("hnB2BCompanyId", True, "#hnB2BCompanyId"), ("hdnIsLionFastAvail", True, "#hdnIsLionFastAvail"),
                    ("hdnCUlanguage", True, "#hdnCUlanguage"), ("hdnIsInfantAdultBlockEnabled", True, "#hdnIsInfantAdultBlockEnabled"),
                    ("hdnIsContinueBagg", True, "#hdnIsContinueBagg"), ("hdnFreeBagg", True, "#hdnFreeBagg"),
                    ("hdnIsOBPremiumEconomy", True, "#hdnIsOBPremiumEconomy"), ("hdnIsIBPremiumEconomy", True, "#hdnIsIBPremiumEconomy"),
                    ("hdnOBBaggageAvail", True, "#hdnOBBaggageAvail"), ("hdnIBBaggageAvail", True, "#hdnIBBaggageAvail"),
                   
                ]
                
                baggage_sell = ""
                baggage_params = []
                baggage_price, baggage_list = self.DPR.parse_to_attributes(
                    "text", "css",
                    "#lvPaxBaggages_ucPaxExcessBaggage_0_lvPaxExcessOBBaggages_0_ucOBBaggageInformation_0_0PaxddlOBBaggages0_0_0 option",
                    self.RCR.page_source)
                baggage_price = {}
                baggage_sum = 0
                if not baggage_list:
                    self.logger.info("查询不到行李列表(*>﹏<*)【service】")
                else:
                    for i in baggage_list:
                        if "+" in i:
                            kilogram, temp_list = self.BPR.parse_to_regex("(\d+)Kg", i)
                            single_price, temp_list = self.BPR.parse_to_regex("\((.*) [A-Z]+\)", i)
                            baggage_price[kilogram] = single_price
                # # # 拼接每个成人具体的参数
                for n, v in enumerate(self.CPR.adult_list):
                    weight = v.get('baggage')
                    kilogram = 0
                    if weight:
                        for w in weight:
                            kilogram += self.BFR.format_to_int(w.get('weight'))
                            
                        k = f"{kilogram}"
                        if k not in baggage_price.keys():
                            self.logger.info(f"查询不到行李价格(*>﹏<*)【{kilogram}】")
                            self.callback_msg = f"查询不到行李价格(*>﹏<*)【{kilogram}】"
                            return self.process_to_service(count + 1, max_count)
                        else:
                            p = baggage_price.get(k)
                            p = self.BFR.format_to_float(2, p)
                            baggage_sum += p
    
                        baggage_sell += f"{n}^ADULT${n}~{kilogram},{kilogram}*"

                    baggage_params.extend([
                        (f"lvPaxBaggages$ctrl{n}$ucPaxExcessBaggage$hfBaggagePaxIndex", False, ""),
                        (f"lvPaxBaggages$ctrl{n}$ucPaxExcessBaggage$_{n}hfPaxOBSelBaggages", False, ""),
                        (f"lvPaxBaggages$ctrl{n}$ucPaxExcessBaggage$_{n}hfPaxIBSelBaggages", False, ""),
                        (f"lvPaxBaggages$ctrl{n}$ucPaxExcessBaggage$lvPaxExcessOBBaggages$ctrl0"
                         f"$ucOBBaggageInformation${n}PaxddlOBBaggages0_0", False, kilogram),
                    ])
                # # # 拼接每个儿童具体的参数
                if self.CPR.child_num:
                    for n, v in enumerate(self.CPR.child_list):
                        i = n + self.CPR.adult_num
    
                        weight = v.get('baggage')
                        kilogram = 0
                        if weight:
                            for w in weight:
                                kilogram += self.BFR.format_to_int(w.get('weight'))
    
                            k = f"{kilogram}"
                            if k not in baggage_price.keys():
                                self.logger.info(f"查询不到行李价格(*>﹏<*)【{kilogram}】")
                                self.callback_msg = f"查询不到行李价格(*>﹏<*)【{kilogram}】"
                                return self.process_to_service(count + 1, max_count)
                            else:
                                p = baggage_price.get(k)
                                p = self.BFR.format_to_float(2, p)
                                baggage_sum += p
                                
                            baggage_sell += f"{n}^CHILD${n}~{kilogram},{kilogram}*"

                        baggage_params.extend([
                            (f"lvPaxBaggages$ctrl{i}$ucPaxExcessBaggage$hfBaggagePaxIndex", False, ""),
                            (f"lvPaxBaggages$ctrl{i}$ucPaxExcessBaggage$_{i}hfPaxOBSelBaggages", False, ""),
                            (f"lvPaxBaggages$ctrl{i}$ucPaxExcessBaggage$_{i}hfPaxIBSelBaggages", False, ""),
                            (f"lvPaxBaggages$ctrl{i}$ucPaxExcessBaggage$lvPaxExcessOBBaggages$ctrl0"
                             f"$ucOBBaggageInformation${i}PaxddlOBBaggages0_0", False, kilogram),
                        ])
    
                baggage_sell = baggage_sell.strip("*")
                param_batch.extend([("hfOBSelBaggages", False, baggage_sell), ("hfIBSelBaggages", True, "#hfIBSelBaggages"), ])
                param_batch.extend(baggage_params)
                param_batch.extend([
                    ("hdnMaxPaxCount", False, self.CPR.adult_num + self.CPR.child_num + self.CPR.infant_num),
                    ("hdnIsOutBoundAirbusFlight", False, 0), ("hdnIsInBoundAirbusFlight", False, 0),
                    ("hdnlstOutboundAirbusFlight", True, "#hdnlstOutboundAirbusFlight"),
                    ("hdnlstInboundAirbusFlight", True, "#hdnlstInboundAirbusFlight"),
                    ("btnProceedBooking", True, "#btnProceedBooking"),
                    ("ucSessiontimeOut$hdnShowSession", True, "#ucSessiontimeOut_hdnShowSession"),
                    ("ucSessiontimeOut$hdnSessionout", True, "#ucSessiontimeOut_hdnSessionout"),
                    ("ucSessiontimeOut$hdnshowpopup", True, "#ucSessiontimeOut_hdnshowpopup"),
                    ("ucSessiontimeOut$hdnCUID", True, "#ucSessiontimeOut_hdnCUID"),
                    ("ucPackageSummary$htOptAddOnCurrency", True, "#ucPackageSummary_htOptAddOnCurrency"),
                    ("ucPackageSummary$lvDepFlightSegments$ctrl0$hdnLegIndex", False, 0),
                    ("ucPackageSummary$hfOptSummaryBaseFare", False, self.fare_price),
                    ("ucPackageSummary$hfOptSummaryTax", False, self.fare_tax),
                    ("ucPackageSummary$hfOptSummaryLionFastPrice", False, ""),
                    ("ucPackageSummary$hfOptSummaryIsBagSelected", False, ""),
                    ("ucPackageSummary$hfOptSummaryComfyKitPrice", False, ""),
                    ("ucPackageSummary$hfOptSummaryTravelSIMPrice", False, ""),
                    # ("ucPackageSummary$hfOptSummaryBRBPrice", False, ""),
                    ("ucPackageSummary$hfOptSummarySmsPrice", False, ""),
                    ("ucPackageSummary$hfOptSummaryTotalPrice", False, self.total_price),
                ])
                # baggagepanel, temp_list = self.DPR.parse_to_attributes(
                #     "id", "css", "#divBaggageInformation", self.RCR.page_source)
                if baggage_sum:
                    baggage_sum = self.BFR.format_to_cut(2, baggage_sum)
                    param_batch.extend([("ucPackageSummary$hfOptSummaryBaggagePrice",
                                         False, baggage_sum), ])
                    self.baggage_price = self.BFR.format_to_float(2, baggage_sum)
                else:
                    self.baggage_price = -1

                    
                mealspanel, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#divMealInformation", self.RCR.page_source)
                if mealspanel:
                    param_batch.extend([
                        ("ucPackageSummary$hfOptSummaryMealPrice", False, "0.00"),
                        ("ucPackageSummary$hfOptSummarySOBPrice", False, ""),
                    ])
                seatpanel, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#divSeatInformation", self.RCR.page_source)
                if seatpanel:
                    param_batch.extend([("ucPackageSummary$hfOptSummarySeatPrice", False, "0.00"), ])
                
                self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.page_source)
                if self.RCR.request_to_post(status_code=302):
                    return True
                
            self.logger.info(f"行李第{count + 1}次超时或者错误(*>﹏<*)【service】")
            self.callback_msg = f"行李第{count + 1}次超时或者错误"
            return self.process_to_service(count + 1, max_count)

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
            self.RCR.url = "https://agent.lionairthai.com/SL/FlightBooking.aspx"
            self.RCR.param_data = (("t", self.login_target),)
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/OptionalAddOns.aspx?t={self.login_target}",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                self.temp_source2 = self.BFR.format_to_same(self.RCR.page_source)
                hold_string, hold_list = self.DPR.parse_to_attributes(
                    "text", "css", "label[for=rdolstPaymentType_0]", self.RCR.page_source)
                self.hold_button, hold_list = self.DPR.parse_to_attributes(
                    "value", "css", "#rdolstPaymentType_0", self.RCR.page_source)
                if not hold_string or not self.hold_button or "Hold" not in hold_string or self.hold_button != "49":
                    self.logger.info(f"查询不到占舱按钮(*>﹏<*)【{hold_string}】")
                    self.callback_msg = "查询不到占舱按钮"
                    return self.process_to_payment(count + 1, max_count)
                else:
                    self.logger.info("匹配占舱按钮成功(*^__^*)【payment】")
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
            self.RCR.url = "https://agent.lionairthai.com/SL/FlightBooking.aspx"
            self.RCR.param_data = (("t", self.login_target),)
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "agent.lionairthai.com",
                "Origin": "https://agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/SL/FlightBooking.aspx?t={self.login_target}",
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", True, "#__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__LASTFOCUS", True, "#__LASTFOCUS"), ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"), ("hdnDeptDate", True, "#hdnDeptDate"),
                ("hdnPaxCount", True, "#hdnPaxCount"), ("hfCustomerUserUrl", True, "#hfCustomerUserUrl"),
                ("hdnIsStudent", True, "#hdnIsStudent"), ("hdnStudentFName", True, "#hdnStudentFName"),
                ("hdnStudentLName", True, "#hdnStudentLName"), ("hdnIsStudentSlected", True, "#hdnIsStudentSlected"),
                ("hdnIsNationalityPostBackRequired", True, "#hdnIsNationalityPostBackRequired"),
                ("hdnIsChangeAccepted", True, "#hdnIsChangeAccepted"), ("hdnIsPaxLogin", True, "#hdnIsPaxLogin"),
                ("hdnCUlanguage", True, "#hdnCUlanguage"), ("hdnCUId", True, "#hdnCUId"),
                ("hdnSelectedPaymentId", False, self.hold_button), ("hdnAddonExists", True, "#hdnAddonExists"),
                ("hdnAddonAvialble", False, "0"), ("hdnNoInsurance", True, "#hdnNoInsurance"),
                ("txtVoucherCode", True, "#txtVoucherCode"), ("rdolstPaymentType", False, self.hold_button),
                ("ucPersonalDetails1$ddlTitle", False, "Mr."), ("ucPersonalDetails1$txtFName", False, self.CPR.contact_first),
                ("ucPersonalDetails1$txtLName", False, self.CPR.contact_last),
                ("ucPersonalDetails1$txtAdd1", False, "Beijinghaidianqu"),
                ("ucPersonalDetails1$txtCity", False, "Beijing"),
                ("ucPersonalDetails1$ddlCountry", False, "China"),
                ("ucPersonalDetails1$txtPostCode", False, "100000"),
                ("ucPersonalDetails1$txtContactNo", False, "86" + self.CPR.contact_mobile),
                ("ucPersonalDetails1$ddlCountryCode", False, "86"),
                ("ucPersonalDetails1$txtMobileNo", False, self.CPR.contact_mobile),
                ("ucPersonalDetails1$txtEmail", False, self.CPR.contact_email),
                ("ucPersonalDetails1$txtConformEmail", False, self.CPR.contact_email),
                ("dangerousgoods", False, "on"), ("chkRules", False, "on"), ("btnBooking", True, "#btnBooking"),
                ("ucSessiontimeOut$hdnShowSession", True, "#ucSessiontimeOut_hdnShowSession"),
                ("ucSessiontimeOut$hdnSessionout", True, "#ucSessiontimeOut_hdnSessionout"),
                ("ucSessiontimeOut$hdnshowpopup", True, "#ucSessiontimeOut_hdnshowpopup"),
                ("ucSessiontimeOut$hdnCUID", True, "#ucSessiontimeOut_hdnCUID"),
                ("hfPaxDetails", True, "#hfPaxDetails"), ("hfpaxlistPerTour", True, "#hfpaxlistPerTour"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source2)
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查询错误按钮
                error, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "#lblErrorMessge", self.RCR.page_source)
                error_clear = self.BPR.parse_to_separate(error)
                if error_clear:
                    self.logger.info(f"提交支付信息报错(*>﹏<*)【{error_clear}】")
                    self.callback_msg = f"提交支付信息报错【{error_clear}】"
                    return False
                error, temp_list = self.DPR.parse_to_attributes("text", "css", "#divErrorMsg", self.RCR.page_source)
                error_clear = self.BPR.parse_to_separate(error)
                if error_clear:
                    if "System detected there is another booking" in error_clear:
                        booking_id, temp_list = self.BPR.parse_to_regex("Booking ID :(.*)Status", error_clear)
                        self.logger.info(f"系统之前占过位置(*>﹏<*)【{booking_id}】")
                        self.callback_msg = f"系统之前占过位置，票号可能是【{booking_id}】"
                        return False
                    else:
                        self.logger.info(f"提交支付信息报错(*>﹏<*)【{error_clear}】")
                        self.callback_msg = f"提交支付信息报错【{error_clear}】"
                        return False
                else:
                    
                    # # # # 提取价格和pnr
                    self.total_price = self.BFR.format_to_float(2, self.total_price)
                    if self.baggage_price != -1:
                        self.total_price += self.baggage_price

                    nta_price, temp_list = self.BPR.parse_to_regex("'NTA = CNY(.*?)'", self.RCR.page_source)
                    nta_price = self.BFR.format_to_float(2, nta_price)
                    
                    record_url, url_list = self.DPR.parse_to_attributes(
                        "value", "css", "#hdnCrmUrl", self.RCR.page_source)
                    self.record, temp_list = self.BPR.parse_to_regex("PNR%3D(.*)", record_url)
                    if not self.record:
                        self.record, temp_list = self.BPR.parse_to_regex("PNR=(.*)", record_url)
                    self.record = self.BPR.parse_to_clear(self.record)
                    # # # 提取超时时间
                    dead_line, dead_list = self.DPR.parse_to_attributes(
                        "text", "css", "#divTicketingDeadLine span", self.RCR.page_source)
                    dead_time = self.BPR.parse_to_clear(dead_line)
                    
                    if self.record:
                        time_format = self.DFR.format_to_transform(dead_time, '%d%B,%Y,%H:%M')
                        self.pnr_timeout = time_format.strftime("%Y-%m-%d %H:%M:%S")
                        self.logger.info(f"匹配订单编号成功(*^__^*)【{self.record}】【{nta_price}】")
                        if nta_price:
                            self.total_price = nta_price
                        return True
                    else:
                        self.record, temp_list = self.DPR.parse_to_attributes(
                            "text", "css", "#divReservationInfo h4.rel-pos", self.RCR.page_source)
                        self.record = self.BPR.parse_to_clear(self.record)
                        self.logger.info(f"查询不到订单编号(*>﹏<*)【{self.record}】")
                        self.callback_msg = "账户可能已经站位，需要人工核对姓名去查找PNR"
                        return False

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

