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
"""The formatter is use for format structure data."""


class CallBackFormatter:
    """回调格式器，返回的数据格式。"""
    
    def __init__(self):
        self.logger: any = None  # 日志记录器。
    
    @classmethod
    def format_to_sync(cls) -> dict:
        """Format to sync data. 格式化同步数据。

        Returns:
            dict
        """
        sync_data = {
            "success": "false",  # 返回状态。
            "msg": "占舱失败",  # 返回信息。
            "occupyCabinId": 0,  # 任务编号。
            "totalPrice": "",  # 总价。
            "currency": "",  # 货币类型。
            "pnrCode": "",  # 票号。
            "pnrTimeout": "",  # 票号超时时间。
            "orderSrc": 1,  # 是否是企业类型。
            "carrierAccount": "",  # 个人账号。
            "carrierAccountAgent": "",  # 企业账号。
            "farePrice": "",  # 总票面价。
            "fareTax": "",  # 总税价。
            "adultPrice": "",  # 成人单人票面价。
            "adultTax": "",  # 成人单人税价。
            "childPrice": "",  # 儿童单人票面价。
            "childTax": "",  # 儿童单人税价。
            "fromSegments": [],
            "fareBaggagePrice": -1,  # 行李总价。
            "passengerBaggages": []  # 行李参数。
        }
        return sync_data
    
    @classmethod
    def format_to_async(cls) -> dict:
        """Format to sync data. 格式化异步数据。

        Returns:
            dict
        """
        async_data = {
            "success": "false",  # 返回状态。
            "msg": "占舱失败",  # 返回信息。
            "occupyCabinId": 0,  # 任务编号。
            "totalPrice": "",  # 总价。
            "currency": "",  # 货币类型。
            "pnrCode": "",  # 票号。
            "pnrTimeout": "",  # 票号超时时间。
            "orderSrc": 1,  # 是否是企业类型。
            "carrierAccount": "",  # 个人账号。
            "carrierAccountAgent": "",  # 企业账号。
            "baggagePrice": -1,  # 行李总价。
            "passengerBaggages": [],  # 行李参数。
        }
        return async_data

