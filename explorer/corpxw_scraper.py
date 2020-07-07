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
from detector.corpxw_simulator import CorpXWSimulator


class CorpXWScraper(RequestWorker):
    """XW采集器，XW网站流程交互。"""
    
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
        self.CSR = CorpXWSimulator()
        # # # 请求中用到的变量
        self.key: str = ""  # 查询sell key
        self.ajax_header: str = ""  # 认证ajax header
        self.temp_source: str = ""      # 临时源数据
        self.hold_button: str = ""  # 占舱按钮
        # # # 返回中用到的变量
        self.total_price: float = 0.0   # 总价
        self.total_fare: float = 0.0    # 总票面价
        self.total_tax: float = 0.0     # 总税价
        self.baggage_price: float = -1  # 行李总价
        self.record: str = ""           # 票号
        self.pnr_timeout: str = ""      # 票号超时时间
        self.single_fare: float = 0.0   # 单人票面价
        self.single_tax: float = 0.0    # 单人税价
        self.segments = []              # 航段信息

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
        self.callback_data = self.CFR.format_to_sync()
        # # # 解析接口参数。
        if not self.CPR.parse_to_interface(source_dict):
            self.callback_data['msg'] = "请通知技术检查接口数据参数。"
            return self.callback_data
        self.logger.info(source_dict)
        # # # 启动爬虫，建立header。
        self.RCR.set_to_session()
        self.RCR.set_to_proxy(enable_proxy, address)
        self.user_agent, self.init_header = self.RCR.build_to_header("None")
        self.RCR.timeout = 10
        # # # 主体流程。
        if self.process_to_login(max_count=self.retry_count):
            if self.process_to_search(max_count=self.retry_count):
                if self.process_to_query(max_count=self.retry_count):
                    if self.process_to_passenger(max_count=self.retry_count):
                        if self.process_to_service(max_count=self.retry_count):
                            if self.process_to_payment(max_count=self.retry_count):
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
    
    def process_to_ajax(self, js_url: str = "", referer_url: str = ""):
        """
        
        Args:
            js_url:

        Returns:

        """
        # # # 获取challenge
        self.RCR.url = "https://book.nokscoot.com" + js_url
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "*/*",
            "Host": "book.nokscoot.com",
            "Referer": referer_url,
        })
        self.RCR.post_data = None
        if self.RCR.request_to_get():
            self.ajax_header, temp_list = self.BPR.parse_to_regex('ajax_header:"(.*?)",', self.RCR.page_source)
            url, temp_list = self.BPR.parse_to_regex('path:"(.*?)",', self.RCR.page_source)
            if self.ajax_header:
                # # # 获取challenge
                self.RCR.url = "https://book.nokscoot.com" + url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Content-Type": "text/plain;charset=UTF-8",
                    "Host": "book.nokscoot.com",
                    "Origin": "https://book.nokscoot.com",
                    "Referer": referer_url,
                    "X-Distil-Ajax": self.ajax_header
                })
                
                o = self.CSR.recognize_to_identify()
                ua = self.BPR.parse_to_clear(self.user_agent)
                
                data = '{"proof":"%s","cookies":1,"setTimeout":0,"setInterval":0,' \
                       '"appName":"Netscape","platform":"Win32","syslang":"zh-CN","userlang":"zh-CN","cpu":"",' \
                       '"productSub":"20030107","plugins":{"0":"ChromePDFPlugin","1":"ChromePDFViewer","2":' \
                       '"NativeClient"},"mimeTypes":{"0":"application/pdf","1":' \
                       '"PortableDocumentFormatapplication/x-google-chrome-pdf","2":' \
                       '"NativeClientExecutableapplication/x-nacl","3":' \
                       '"PortableNativeClientExecutableapplication/x-pnacl"},"screen":{"width":1920,"height":1080,' \
                       '"colorDepth":24},"fonts":{"0":"Calibri","1":"Cambria","2":"Times","3":"Constantia","4":' \
                       '"LucidaBright","5":"Georgia","6":"SegoeUI","7":"Candara","8":"TrebuchetMS","9":"Verdana",' \
                       '"10":"Consolas","11":"LucidaConsole","12":"LucidaSansTypewriter","13":"CourierNew","14":' \
                       '"Courier"},"fp2":{"userAgent":' \
                       '"%s","language":"zh-CN","screen":{"width":1920,"height":1080,"availHeight":1040,' \
                       '"availWidth":1920,"pixelDepth":24,"innerWidth":1259,"innerHeight":803,"outerWidth":1275,' \
                       '"outerHeight":891,"devicePixelRatio":1},"timezone":8,"indexedDb":true,"addBehavior":false,' \
                       '"openDatabase":true,"cpuClass":"unknown","platform":"Win32","doNotTrack":"unknown","plugins":' \
                       '"ChromePDFPlugin::PortableDocumentFormat::application/x-google-chrome-pdf~pdf;' \
                       'ChromePDFViewer::::application/pdf~pdf;NativeClient::::application/x-nacl~,' \
                       'application/x-pnacl~","canvas":{"winding":"yes","towebp":true,"blending":true,"img":' \
                       '"bee56b0a4dcf5bc3040ee3f938f6efd48ad5fd68"},"webGL":{"img":' \
                       '"bd6549c125f67b18985a8c509803f4b883ff810c","extensions":"ANGLE_instanced_arrays;' \
                       'EXT_blend_minmax;EXT_color_buffer_half_float;EXT_disjoint_timer_query;EXT_float_blend;' \
                       'EXT_frag_depth;EXT_shader_texture_lod;EXT_texture_filter_anisotropic;' \
                       'WEBKIT_EXT_texture_filter_anisotropic;EXT_sRGB;KHR_parallel_shader_compile;' \
                       'OES_element_index_uint;OES_standard_derivatives;OES_texture_float;' \
                       'OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;' \
                       'OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_s3tc;' \
                       'WEBKIT_WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;' \
                       'WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;' \
                       'WEBKIT_WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;' \
                       'WEBKIT_WEBGL_lose_context","aliasedlinewidthrange":"[1,1]","aliasedpointsizerange":' \
                       '"[1,1024]","alphabits":8,"antialiasing":"yes","bluebits":8,"depthbits":24,"greenbits":8,' \
                       '"maxanisotropy":16,"maxcombinedtextureimageunits":32,"maxcubemaptexturesize":16384,' \
                       '"maxfragmentuniformvectors":1024,"maxrenderbuffersize":16384,"maxtextureimageunits":16,' \
                       '"maxtexturesize":16384,"maxvaryingvectors":30,"maxvertexattribs":16,' \
                       '"maxvertextextureimageunits":16,"maxvertexuniformvectors":4096,"maxviewportdims":' \
                       '"[32767,32767]","redbits":8,"renderer":"WebKitWebGL","shadinglanguageversion":' \
                       '"WebGLGLSLES1.0(OpenGLESGLSLES1.0Chromium)","stencilbits":0,"vendor":"WebKit","version":' \
                       '"WebGL1.0(OpenGLES2.0Chromium)","vertexshaderhighfloatprecision":23,' \
                       '"vertexshaderhighfloatprecisionrangeMin":127,"vertexshaderhighfloatprecisionrangeMax":127,' \
                       '"vertexshadermediumfloatprecision":23,"vertexshadermediumfloatprecisionrangeMin":127,' \
                       '"vertexshadermediumfloatprecisionrangeMax":127,"vertexshaderlowfloatprecision":23,' \
                       '"vertexshaderlowfloatprecisionrangeMin":127,"vertexshaderlowfloatprecisionrangeMax":127,' \
                       '"fragmentshaderhighfloatprecision":23,"fragmentshaderhighfloatprecisionrangeMin":127,' \
                       '"fragmentshaderhighfloatprecisionrangeMax":127,"fragmentshadermediumfloatprecision":23,' \
                       '"fragmentshadermediumfloatprecisionrangeMin":127,' \
                       '"fragmentshadermediumfloatprecisionrangeMax":127,"fragmentshaderlowfloatprecision":23,' \
                       '"fragmentshaderlowfloatprecisionrangeMin":127,"fragmentshaderlowfloatprecisionrangeMax":127,' \
                       '"vertexshaderhighintprecision":0,"vertexshaderhighintprecisionrangeMin":31,' \
                       '"vertexshaderhighintprecisionrangeMax":30,"vertexshadermediumintprecision":0,' \
                       '"vertexshadermediumintprecisionrangeMin":31,"vertexshadermediumintprecisionrangeMax":30,' \
                       '"vertexshaderlowintprecision":0,"vertexshaderlowintprecisionrangeMin":31,' \
                       '"vertexshaderlowintprecisionrangeMax":30,"fragmentshaderhighintprecision":0,' \
                       '"fragmentshaderhighintprecisionrangeMin":31,"fragmentshaderhighintprecisionrangeMax":30,' \
                       '"fragmentshadermediumintprecision":0,"fragmentshadermediumintprecisionrangeMin":31,' \
                       '"fragmentshadermediumintprecisionrangeMax":30,"fragmentshaderlowintprecision":0,' \
                       '"fragmentshaderlowintprecisionrangeMin":31,"fragmentshaderlowintprecisionrangeMax":30,' \
                       '"unmaskedvendor":"GoogleInc.","unmaskedrenderer":' \
                       '"ANGLE(Intel(R)HDGraphics630Direct3D11vs_5_0ps_5_0)"},"touch":{"maxTouchPoints":0,' \
                       '"touchEvent":false,"touchStart":false},"video":{"ogg":"probably","h264":"probably","webm":' \
                       '"probably"},"audio":{"ogg":"probably","mp3":"probably","wav":"probably","m4a":"maybe"},' \
                       '"vendor":"GoogleInc.","product":"Gecko","productSub":"20030107","browser":{"ie":false,' \
                       '"chrome":true,"webdriver":false},"window":{"historyLength":2,"hardwareConcurrency":8,' \
                       '"iframe":false,"battery":true},"location":{"protocol":"https:"},"fonts":"Calibri;' \
                       'Century;Haettenschweiler;Marlett;Pristina;SimHei","devices":{"count":3,"data":{"0":{' \
                       '"deviceId":"default","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":"audiooutput",' \
                       '"label":""},"1":{"deviceId":"communications","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":"audiooutput",' \
                       '"label":""},"2":{"deviceId":' \
                       '"2f2a091339475b73dadb679955354ff320b9aae108e009f7536f6cda8c761928","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":' \
                       '"audiooutput","label":""}}}}}' % (o, ua)
                
                self.RCR.post_data = [
                    ("p", data)
                ]
                if self.RCR.request_to_post():
                    return True
        return False
    
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
            self.RCR.set_to_cookies(False,
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
    
    def process_to_verify(self, captcha_url: str = "", referer_url: str = "", js_url: str = "",
                          count: int = 0, max_count: int = 2) -> bool:
        """Verify process. 验证过程。

        Args:
            captcha_url
            referer_url
            js_url
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            if self.process_to_ajax(js_url, referer_url):
                # # # 获取challenge
                self.RCR.url = "https://book.nokscoot.com/distil_r_captcha_challenge"
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Host": "book.nokscoot.com",
                    "Origin": "https://book.nokscoot.com",
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
                            ("gt", "f2ae6cadcf7886856696502e1d55e00c"), ("challenge", challenge),
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
                            voice_path, temp_list = self.BPR.parse_to_regex("/voice/zh/(.*).mp3", voice_path)
                            if not voice_path:
                                self.logger.info(f"认证音频地址错误(*>﹏<*)【{self.RCR.page_source}】")
                                self.callback_msg = "认证音频地址错误"
                                return self.process_to_verify(captcha_url, referer_url, js_url, count + 1, max_count)
                            else:
                                # # # 获取mp3文件
                                self.RCR.url = "http://114.55.207.125:50005/getcaptcha/geetest/" + voice_path
                                self.RCR.param_data = None
                                self.RCR.header = None
                                if self.RCR.request_to_get():
                                    # # 识别语音
                                    number, temp_list = self.BPR.parse_to_regex("\d+", self.RCR.page_source)
                                    if number:
                                        # # # 获取validate
                                        self.RCR.url = "http://api-na.geetest.com/ajax.php"
                                        self.RCR.param_data = (
                                            ("gt", "f2ae6cadcf7886856696502e1d55e00c"),
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
                                            validate, temp_list = self.BPR.parse_to_path("$.data.validate", get_json)
                                            if "url=" in captcha_url:
                                                cap_url, temp_list = self.BPR.parse_to_regex(
                                                    "url=(.*)", captcha_url)
                                            else:
                                                cap_url = captcha_url
                                            if not validate or not cap_url:
                                                self.logger.info(f"认证提交地址错误(*>﹏<*)【{self.RCR.page_source}】")
                                                self.callback_msg = "认证提交地址错误"
                                                return self.process_to_verify(
                                                    captcha_url, referer_url, js_url, count + 1, max_count)
                                            else:
                                                # # # 提交认证
                                                self.RCR.url = "https://book.nokscoot.com" + cap_url
                                                self.RCR.param_data = None
                                                self.RCR.header = self.BFR.format_to_same(self.init_header)
                                                self.RCR.header.update({
                                                    "Accept": "*/*",
                                                    "Content-Type": "application/x-www-form-urlencoded",
                                                    "Host": "book.nokscoot.com",
                                                    "Origin": "https://book.nokscoot.com",
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
            return self.process_to_verify(captcha_url, referer_url, js_url, count + 1, max_count)
    
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
            self.RCR.url = "https://book.nokscoot.com/AgentLogin.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "book.nokscoot.com",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_login(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/AgentLogin.aspx"):
                        return self.process_to_login(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/AgentLogin.aspx"):
                        return self.process_to_login(count + 1, max_count)
                
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/AgentLogin.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_login(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【login】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_login(count + 1, max_count)
                else:
                    self.logger.info("登录流程不走验证(*^__^*)【login】")
                    # # # 解析登录后状态，判断是否成功
                    self.RCR.url = "https://book.nokscoot.com/AgentLogin.aspx"
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Host": "book.nokscoot.com",
                        "Origin": "https://book.nokscoot.com",
                        "Referer": "https://book.nokscoot.com/AgentLogin.aspx",
                        "Upgrade-Insecure-Requests": "1"
                    })
                    password = self.AFR.decrypt_into_aes(
                        self.AFR.encrypt_into_sha1(self.AFR.password_key), self.CPR.password)
                    param_batch = [
                        ("__EVENTTARGET", False, "AgentLoginAgentLoginView$LinkButtonSubmit"),
                        ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                        ("__VIEWSTATE", True, "#__VIEWSTATE"),
                        ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                        ("pageToken", True, "input[name=pageToken]"),
                        ("AgentLogin.Email", False, self.CPR.username),
                        ("AgentLogin.Password", False, password),
                    ]
                    self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.page_source)
                    if self.RCR.request_to_post(status_code=302):
                        self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                        # # # 判断是否错误
                        error_message, temp_list = self.DPR.parse_to_attributes(
                            "id", "css", "#errorbox", self.RCR.page_source)
                        if error_message:
                            self.logger.info(f"账号或者密码错误(*>﹏<*)【{error_message}】")
                            self.callback_msg = "账号或者密码错误"
                            return False
                        else:
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
            self.RCR.url = 'https://book.nokscoot.com/Search.aspx'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/Search.aspx",
                "Upgrade-Insecure-Requests": "1",
            })
            flight_date = self.DFR.format_to_transform(self.CPR.flight_date, "%Y%m%d")
            month = flight_date.strftime("%m")
            day = flight_date.strftime("%d")
            
            param_batch = [
                ("__EVENTTARGET", False, "AvailabilitySearchInputSearchView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", False, "APJFr9lGRF6uci4AwkbmhyIqrK1j9PRXYfW1KeMDnuY="),
                ("pageToken", True, "input[name=pageToken]"),
                ("MemebrLoginInline.Logout", False, "1"),
                ("AvailabilitySearchInput.SearchStationDatesList[0].DepartureStationCode", False, self.CPR.departure_code),
                ("AvailabilitySearchInput.SearchStationDatesList[0].ArrivalStationCode", False, self.CPR.arrival_code),
                ("AvailabilitySearchInput.SearchStationDatesList[0].DepartureDate", False, f"{month}/{day}/{flight_date.year}"),
                ("AvailabilitySearchInput.SearchStationDatesList[1].DepartureStationCode", False, ""),
                ("AvailabilitySearchInput.SearchStationDatesList[1].ArrivalStationCode", False, ""),
                ("AvailabilitySearchInput.SearchStationDatesList[1].DepartureDate", False, ""),
                ("a", False, "on"),
                ("AvailabilitySearchInput.AdultsCount", False, self.CPR.adult_num),
                ("AvailabilitySearchInput.ChildsCount", False, self.CPR.child_num),
                ("AvailabilitySearchInput.InfantsCount", False, self.CPR.infant_num),
                ("AvailabilitySearchInput.PromoCode", False, self.CPR.promo)
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_search(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Search.aspx"):
                        return self.process_to_search(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Search.aspx"):
                        return self.process_to_search(count + 1, max_count)
                    
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/Search.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_search(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【query】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_search(count + 1, max_count)
                else:
                    self.logger.info("查询流程不走验证(*^__^*)【query】")
                    
                    self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                    error_message, temp_list = self.DPR.parse_to_attributes("text", "css", ".message_red",
                                                                           self.RCR.page_source)
                    if error_message:
                        self.logger.info(f"查询不到航线信息(*>﹏<*)【{self.CPR.flight_num}】")
                        self.callback_msg = f"查询不到航线信息【{error_message}】"
                        return False
                    # # # 解析接口航班号。
                    interface_carrier = self.CPR.flight_num[:2]
                    interface_no = self.CPR.flight_num[2:]
                    interface_no = self.BFR.format_to_int(interface_no)
                    # # # 匹配航班
                    is_flight = False
                    flight_id, flight_list = self.DPR.parse_to_attributes(
                        "class", "css", ".flight_datail_tb .flightdetails", self.RCR.page_source)
                    if flight_list:
                        for i in range(2, len(flight_list) + 2):
                            flight_number, temp_list = self.DPR.parse_to_attributes(
                                "text", "css", f"table.flight_datail_tb>tr:nth-child({i}) .popbg_middle th["
                                             f"align=left]", self.RCR.page_source)
                            flight_number = self.BPR.parse_to_clear(flight_number)
                            if flight_number and len(flight_number) > 2:
                                source_carrier = flight_number[:2]
                                source_no = flight_number[2:]
                                source_no = self.BFR.format_to_int(source_no)
                                # # # 匹配航班号。
                                if interface_carrier == source_carrier and interface_no == source_no:
                                    is_flight = True
                                    sell_key, temp_list = self.DPR.parse_to_attributes(
                                        "for", "css", f"table.flight_datail_tb>tr:nth-child({i}) .flight_action_value "
                                                    f".saver label",
                                        self.RCR.page_source)
                                    if sell_key:
                                        self.key = sell_key
                                        self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                    else:
                                        sell_key, temp_list = self.DPR.parse_to_attributes(
                                            "for", "css",
                                            f"table.flight_datail_tb>tr:nth-child({i}) .flight_action_value .flexi label",
                                            self.RCR.page_source)
                                        if sell_key:
                                            self.key = sell_key
                                            self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                        else:
                                            sell_key, temp_list = self.DPR.parse_to_attributes(
                                                "for", "css",
                                                f"table.flight_datail_tb>tr:nth-child({i}) .flight_action_value .premiun label",
                                                self.RCR.page_source)
                                            if sell_key:
                                                self.key = sell_key
                                                self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                            else:
                                                sell_key, temp_list = self.DPR.parse_to_attributes(
                                                    "for", "css",
                                                    f"table.flight_datail_tb>tr:nth-child({i}) .flight_action_value .business label",
                                                    self.RCR.page_source)
                                                if sell_key:
                                                    self.key = sell_key
                                                    self.logger.info(f"匹配航班信息成功(*^__^*)【{self.key}】")
                                                else:
                                                    self.logger.info(f"匹配不到坐席信息(*>﹏<*)【{self.CPR.flight_num}】")
                                                    self.callback_msg = f"匹配不到坐席信息【{self.CPR.flight_num}】"
                                                    return False
                                    break
                    
                    if not is_flight:
                        self.logger.info(f"匹配不到航班信息(*>﹏<*)【{self.CPR.flight_num}】")
                        self.callback_msg = f"匹配不到航班信息【{self.CPR.flight_num}】"
                        return False
    
                    base_segment = self.key.split("|")
                    if len(base_segment) > 1:
                        cabin, temp_list = self.BPR.parse_to_regex("~(.*?)~", base_segment[1])
                        base_segment, temp_list = self.BPR.parse_to_regex("~~(.*?)~~", base_segment[0])
                        base_segment = base_segment.split("~")
                        departureTime = self.DFR.format_to_transform(base_segment[1], "%m/%d/%Y %H:%M")
                        arriveTime = self.DFR.format_to_transform(base_segment[3], "%m/%d/%Y %H:%M")
                        self.segments = [{
                            "departureAirport": self.CPR.departure_code,
                            "arriveAirport": self.CPR.arrival_code,
                            "carrier": "XW",
                            "flightNumber": self.CPR.flight_num[0],
                            "departureTime": departureTime.strftime("%Y%m%d%H%M"),
                            "arriveTime": arriveTime.strftime("%Y%m%d%H%M"),
                            "cabin": cabin
                        }]
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
            self.RCR.url = 'https://book.nokscoot.com/Select.aspx'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/Select.aspx",
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", False, "AvailabilityInputSelectView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                ("pageToken", True, "input[name=pageToken]"),
                ("AvailabilitySearchInput.SearchStationDatesList[0].DepartureStationCode", False,
                 ""),
                ("AvailabilitySearchInput.SearchStationDatesList[0].ArrivalStationCode", False,
                 ""),
                ("AvailabilitySearchInput.SearchStationDatesList[0].DepartureDate", False,
                 ""),
                ("AvailabilitySearchInput.SearchStationDatesList[1].DepartureStationCode", False, ""),
                ("AvailabilitySearchInput.SearchStationDatesList[1].ArrivalStationCode", False, ""),
                ("AvailabilitySearchInput.SearchStationDatesList[1].DepartureDate", False, ""),
                ("options", False, "on"),
                ("AvailabilitySearchInput.AdultsCount", False, self.CPR.adult_num),
                ("AvailabilitySearchInput.ChildsCount", False, self.CPR.child_num),
                ("AvailabilitySearchInput.InfantsCount", False, self.CPR.infant_num),
                ("AvailabilitySearchInput.PromoCode", False, self.CPR.promo),
                ("inline_upgrade_0", False, "false"),
                ("sell_key_trip_0", False, self.key),
                ("MemebrLoginInline.Logout", False, "1"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_query(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Select.aspx"):
                        return self.process_to_query(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Select.aspx"):
                        return self.process_to_query(count + 1, max_count)
                    
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/Select.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_query(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【detail】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_query(count + 1, max_count)
                else:
                    self.logger.info("查询流程不走验证(*^__^*)【detail】")
        
                    self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                
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
            # # # 解析乘客页面
            self.RCR.url = "https://book.nokscoot.com/Passengers.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/Passengers.aspx",
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", False, "ControlGroupPassengersView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                ("pageToken", True, "input[name=pageToken]"),
                ("MemebrLoginInline.Logout", False, "1"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            
            # # # 拼接每个成人具体的参数
            for n, v in enumerate(self.CPR.adult_list):
                sex = "MR"
                if v.get("gender") == "F":
                    sex = "MDM"
                elif v.get("gender") == "M":
                    sex = "MR"
                birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y%m%d")
                month = birthday.strftime("%m")
                day = birthday.strftime("%d")
                
                weight = v.get('baggage')
                kilogram = 0
                if weight:
                    for w in weight:
                        kilogram += self.BFR.format_to_int(w.get('weight'))
                if kilogram:
                    # # # TR是BG
                    weight = f"BX{kilogram}"
                else:
                    weight = ""
                
                key = f"{n}_{self.CPR.departure_code}_{self.CPR.arrival_code}"
                self.RCR.post_data.extend([
                    (f"PassengerInput.PassengerInfos[{n}].Title", sex),
                    (f"PassengerInput.PassengerInfos[{n}].FirstName", v.get("first_name")),
                    (f"PassengerInput.PassengerInfos[{n}].LastName", v.get("last_name")),
                    (f"PassengerInput.PassengerInfos[{n}].DateOfBirth", f"{month}/{day}/{birthday.year}"),
                    ("interlineIndex", "0"),
                    (f"PassengersSsrInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersSsrInput.PassengerSsrs['{key}'].SsrCode", weight),
                    # (f"ComfortKitPassengersSsrInput.PassengerSsrs['{key}'].SsrCode:", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
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
                    birthday = self.DFR.format_to_transform(v.get("birthday"), "%Y%m%d")
                    month = birthday.strftime("%m")
                    day = birthday.strftime("%d")
                    
                    weight = v.get('baggage')
                    kilogram = 0
                    if weight:
                        for w in weight:
                            kilogram += self.BFR.format_to_int(w.get('weight'))
                    if kilogram:
                        weight = f"BX{kilogram}"
                    else:
                        weight = ""

                    key = f"{n}_{self.CPR.departure_code}_{self.CPR.arrival_code}"
                    self.RCR.post_data.extend([
                        (f"PassengerInput.PassengerInfos[{n}].Title", sex),
                        (f"PassengerInput.PassengerInfos[{n}].FirstName", v.get("first_name")),
                        (f"PassengerInput.PassengerInfos[{n}].LastName", v.get("last_name")),
                        (f"PassengerInput.PassengerInfos[{n}].DateOfBirth", f"{month}/{day}/{birthday.year}"),
                        ("interlineIndex", "0"),
                        (f"PassengersSsrInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersSsrInput.PassengerSsrs['{key}'].SsrCode", weight),
                        # (f"ComfortKitPassengersSsrInput.PassengerSsrs['{key}'].SsrCode:", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                        (f"PassengersMealInput.PassengerSsrs['{key}'].SsrCode", ""),
                    ])
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_passenger(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Passengers.aspx"):
                        return self.process_to_passenger(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Passengers.aspx"):
                        return self.process_to_passenger(count + 1, max_count)
                
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/Passengers.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_passenger(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【passenger】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_passenger(count + 1, max_count)
                else:
                    self.logger.info("乘客流程不走验证(*^__^*)【passenger】")
        
                    self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                
                    baggage, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", "[toggleelementname='baggageAddon']", self.RCR.page_source)
                    baggage = self.BFR.format_to_float(2, baggage)
                    if baggage:
                        self.baggage_price = baggage
                    else:
                        baggage = 0
                        self.baggage_price = -1
                        
                    fare_price, temp_list = self.DPR.parse_to_attributes(
                        "value", "xpath",
                        "//div[@class='breakdown_list'][1]//div[@class='breakdown_name' and contains(., 'Fare')]"
                        "/following-sibling::div[@class='breakdown_price']//span/text()", self.RCR.page_source)
                    self.single_fare = self.BFR.format_to_float(2, fare_price)
        
                    single_price, temp_list = self.DPR.parse_to_attributes("text", "css", ".ticket_per_price span",
                                                                           self.RCR.page_source)
                    single_price = self.BFR.format_to_float(2, single_price)
                    # # # 模拟变价
                    # single_price = single_price + 200
                    # single_price = self.BFR.format_as_float(2, single_price)
                    if single_price and fare_price:
                        self.single_tax = single_price - self.single_fare
                        self.single_tax = self.BFR.format_to_float(2, self.single_tax)
                        self.total_fare = (self.CPR.adult_num + self.CPR.child_num) * self.single_fare
                        
                    currency, temp_list = self.DPR.parse_to_attributes("text", "css", ".item_title.total div",
                                                                       self.RCR.page_source)
                    price, temp_list = self.DPR.parse_to_attributes("text", "css", ".item_title.total span",
                                                                    self.RCR.page_source)
                    if price and currency:
                        self.CPR.currency = self.BPR.parse_to_clear(currency)
                        self.total_price = self.BFR.format_to_float(2, price)
                        # # # 模拟变价
                        # self.total_price = self.total_price + (self.CPR.adult_num + self.CPR.child_num) * 200
                        # self.total_price = self.BFR.format_as_float(2, self.total_price)
                        
                        self.total_tax = self.total_price - self.total_fare - baggage
                        self.total_tax = self.BFR.format_to_float(2, self.total_tax)
                        self.logger.info(f"匹配价格信息成功(*^__^*)【{self.CPR.currency}】【{self.total_price}】【{self.single_fare}】")
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
            # # # 请求行李页面
            self.RCR.url = 'https://book.nokscoot.com/SeatMap.aspx'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/SeatMap.aspx",
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", False, "UnitMapInputSeatMapView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                ("pageToken", True, "input[name=pageToken]"),
                ("MemebrLoginInline.Logout", False, "1"),
                ("UnitMapInput.ActiveMapKey", False, ""),
                ("UnitMapInput.ClearAutoAssignedSeats", False, "false"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            # # # 拼接每个成人具体的参数
            for n, v in enumerate(self.CPR.adult_list):
                key = f"{n}_{self.CPR.departure_code}_{self.CPR.arrival_code}"
                self.RCR.post_data.extend([
                    (f"UnitMapInput.PassengerSeats['{key}'].UnitDesignator", "")
                ])
            # # # 拼接每个儿童具体的参数
            if self.CPR.child_num:
                for n, v in enumerate(self.CPR.child_list):
                    n += self.CPR.adult_num
                    key = f"{n}_{self.CPR.departure_code}_{self.CPR.arrival_code}"
                    self.RCR.post_data.extend([
                        (f"UnitMapInput.PassengerSeats['{key}'].UnitDesignator", "")
                    ])
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_service(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/SeatMap.aspx"):
                        return self.process_to_service(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/SeatMap.aspx"):
                        return self.process_to_service(count + 1, max_count)
                
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/SeatMap.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_service(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【service】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_service(count + 1, max_count)
                else:
                    self.logger.info("行李流程不走验证(*^__^*)【service】")
        
                    self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
                
                    self.hold_button, temp_list = self.DPR.parse_to_attributes(
                        "class", "css", ".hold_icon", self.RCR.page_source)
                    if self.hold_button:
                        self.logger.info("匹配占舱按钮成功(*^__^*)【service】")
                        return True
                    else:
                        self.logger.info(self.RCR.page_source)
                        self.logger.info("查询不到占舱按钮(*>﹏<*)【service】")
                        self.callback_msg = "查询不到占舱按钮"
                        return False
            
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
            self.RCR.url = 'https://book.nokscoot.com/Payment.aspx'
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/Payment.aspx",
                "Upgrade-Insecure-Requests": "1"
            })
            from datetime import datetime
            a = datetime.utcnow()
            b = a.strftime("%Y-%m-%dT%H:%M:%S")
            c = f"{b}{a.microsecond}Z"
            
            param_batch = [
                ("__EVENTTARGET", False, "PaymentInputPaymentView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                ("pageToken", True, "input[name=pageToken]"),
                ("MemebrLoginInline.Logout", False, "1"),
                ("PaymentInput.SelectedPaymentMethodCode", False, "HOLD"),
                ("ContactInput.BookingContactInfo.Title", False, "MR"),
                ("ContactInput.BookingContactInfo.FirstName", False, self.CPR.contact_first),
                ("ContactInput.BookingContactInfo.LastName", False, self.CPR.contact_last),
                ("ContactInput.BookingContactInfo.WorkPhoneCode", False, "+86"),
                ("ContactInput.BookingContactInfo.WorkPhone", False, self.CPR.contact_mobile),
                ("ContactInput.BookingContactInfo.HomePhoneCode", False, "+86"),
                ("ContactInput.BookingContactInfo.HomePhone", False, self.CPR.contact_mobile),
                ("ContactInput.BookingContactInfo.OtherPhoneCode", False, "+86"),
                ("ContactInput.BookingContactInfo.OtherPhone", False, self.CPR.contact_mobile),
                ("ContactInput.BookingContactInfo.EmailAddress", False, self.CPR.contact_email),
                ("ContactInput.BookingContactInfo.AddressLine1", False, "RM 1703, 17F, Qing Yun Dang Dai"),
                ("ContactInput.BookingContactInfo.AddressLine2", False, "BLD#9, Man Ting Fang Yuan, Qing Yun Li"),
                ("ContactInput.BookingContactInfo.City", False, "Beijing"),
                ("ContactInput.BookingContactInfo.CountryCode", False, "CN"),
                ("ContactInput.BookingContactInfo.ProvinceState", False, "BJ"),
                ("ContactInput.BookingContactInfo.PostalCode", False, "100000"),
                ("isFareLocked", False, "false"),
                ("shouldLock", False, "false"),
                ("pageName", False, "Payment"),
                ("bookingDate", False, c),
                ("FareLockSsrInput.NoLock", False, "false"),
                ("FareLockSsrInput.IsSubmittedByControl", False, "false"),
                ("FareLockSsrInput.IsLockedFromSelect", False, "false"),
                ("FareLockSsrInput.HoldPeriod", False, "120"),
                ("signal_pic", False, "false"),
                ("signal_pic", False, "false"),
                ("signal_pic", False, "false"),
                ("signal_pic", False, "false"),
                ("signal_pic", False, "false"),
                ("PaymentInput.CreditCardNumber", False, "必须填写"),
                ("PaymentInput.CreditCardExpMonth", False, ""),
                ("PaymentInput.CreditCardExpYear", False, ""),
                ("PaymentInput.CreditCardHolderName", False, "必须填写"),
                ("PaymentInput.CardVerificationNumber", False, "必须填写"),
                ("PaymentInput.DccOffered", False, "false"),
                ("PaymentInput.VoucherNumber", False, ""),
                ("PaymentInput.AgencyAmountToPay", False, self.total_price),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.temp_source)
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_payment(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Payment.aspx"):
                        return self.process_to_payment(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/Payment.aspx"):
                        return self.process_to_payment(count + 1, max_count)
                
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/Payment.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_payment(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【payment】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_payment(count + 1, max_count)
                else:
                    self.logger.info("支付流程不走验证(*^__^*)【payment】")
                
                
                    self.record, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", ".bkre_airline_number", self.RCR.page_source)
                    if self.record:
                        last = self.DFR.format_to_now(custom_days=1)
                        self.pnr_timeout = last.strftime("%Y-%m-%d %H:%M:%S")
                        self.logger.info(f"匹配订单编号成功(*^__^*)【{self.record}】")
                        return True
                    else:
                        self.logger.info("查询不到订单编号(*>﹏<*)【record】")
                        self.callback_msg = "查询不到订单编号"
                        return self.process_to_payment(count + 1, max_count)
            
            self.logger.info(f"支付第{count + 1}次超时或者错误(*>﹏<*)【payment】")
            self.callback_msg = f"支付第{count + 1}次超时或者错误"
            return self.process_to_payment(count + 1, max_count)
    
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
        self.callback_data['farePrice'] = self.total_fare
        self.callback_data['fareTax'] = self.total_tax
        self.callback_data['adultPrice'] = self.single_fare
        self.callback_data['adultTax'] = self.single_tax
        self.callback_data['childPrice'] = self.single_fare
        self.callback_data['childTax'] = self.single_tax
        self.callback_data['fromSegments'] = self.segments
        self.callback_data["fareBaggagePrice"] = self.baggage_price
        self.callback_data['passengerBaggages'] = self.CPR.return_baggage
        self.logger.info(self.callback_data)
        return True

