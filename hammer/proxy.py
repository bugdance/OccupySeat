#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on Fri May 10 03:47:45 UTC+8:00 2019

written by pyleo.
"""
import sys
sys.path.append('..')                           # 导入环境当前目录
from apscheduler.schedulers.blocking import BlockingScheduler
import os
import requests


def check(count=0):
    try:
        if count < 2:
            data = os.popen("ipconfig", "r").readlines()
            have_ppp = 0
            ip_str = ""
            for line in data:
                if line.find("宽带连接") >= 0:
                    print(line)
                    have_ppp = 1
                if have_ppp and line.strip().startswith("IPv4 地址"):
                    ip_str = line.split(":")[1].strip()
                    break
            print(ip_str)
            print(have_ppp)
            if have_ppp:
                ip_str = f"http://{ip_str}:18081"
                response = requests.post("http://114.116.253.131:18081/proxy/qn/", json={"ip": ip_str}, timeout=5)
            else:
                os.system("rasdial 宽带连接 /disconnect")
                os.system("rasdial 宽带连接 057488826135 893865")
                return check(count+1)
        else:
            pass
    except Exception as ex:
        pass
        
        
scheduler = BlockingScheduler()
scheduler.add_job(check, 'interval', seconds=60, id='check')  # 每隔5秒执行一次
scheduler.start()



