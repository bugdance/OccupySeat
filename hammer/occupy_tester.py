#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Script test.

written by pyLeo.
"""
# # # Import current path.
import sys
sys.path.append('..')
# # # Analog interface.
import requests
import time
from explorer.corpsl_scraper import CorpSLScraper
from explorer.corptr_scraper import CorpTRScraper
from explorer.corpuo_scraper import CorpUOScraper
from explorer.corpxw_scraper import CorpXWScraper
from explorer.persqn_scraper import PersQNScraper



occupyCabinId = 5548
departureAirport = "NRT"
arriveAirport = "CTU"
departureTime = "20200201"
flightNumber = "XW101" # SL538
carrierAccount = "QCYG014"
carrierPassword = "1oQ6TxkZtwRE9CoILCa39w=="
carrierAccountAgent = "XACN-001"
carrierPasswordAgent = "1oQ6TxkZtwRE9CoILCa39w=="


post_data = {
    "occupyCabinId": occupyCabinId,
    "carrierCode": "VJ",
    "departureAirport": departureAirport,
    "arriveAirport": arriveAirport,
    "flightNumber": flightNumber,
    "departureTime": departureTime,
    "carrierAccount": carrierAccount,
    "carrierPassword": carrierPassword,
    "carrierAccountAgent": carrierAccountAgent,
    "carrierPasswordAgent": carrierPasswordAgent,
    "currency": "",
    "passenger": [
        {"name": "zhou/bapi",
         "type": 0,
         "gender": "M",
         "birthday": "19730126",
         "nationality": "CN",
         "cardNum": "E18269133",
         "cardExpired": "20240526",
         "cardIssuePlace": "CN",
         "cardType": "PP",
         "baggage": [
             {"number": 1, "weight": 30}
         ],
         },
        # {"name": "zhou/babo",
        #  "type": 0,
        #  "gender": "F",
        #  "birthday": "19750526",
        #  "nationality": "CN",
        #  "cardNum": "E18269332",
        #  "cardExpired": "20240526",
        #  "cardIssuePlace": "CN",
        #  "cardType": "PP",
        #  "baggage": [
        #      {"number": 1, "weight": 20}
        #  ],
        #  },
        # {"passengerName": "xxx/shaolong",
        #  "ageType": 1,
        #  "gender": "F",
        #  "birthday": "2012-05-26",
        #  "nationality": "CN",
        #  "cardNum": "E18269332",
        #  "cardExpired": "20240526",
        #  "cardIssuePlace": "CN",
        #  "cardType": "PP",
        #  "baggage": [
        #      # {"number": 1, "weight": 20}
        #  ],
        #  },
        # {"passengerName": "yyy/shaong",
        #  "ageType": 1,
        #  "gender": "M",
        #  "birthday": "2011-05-26",
        #  "nationality": "CN",
        #  "cardNum": "E18269332",
        #  "cardExpired": "20240526",
        #  "cardIssuePlace": "CN",
        #  "cardType": "PP",
        #  "baggage": [
        #      {"number": 1, "weight": 20}
        #  ],
        #  },

    ],
    "crawlerType": "2",
}


post_data = {'departureTime': '20200630', 'arriveAirport': 'HKG', 'departureAirport': 'NRT', 'crawlerType': '1', 'promotionCode': '', 'flightNumber': 'UO849', 'carrierPassword': '', 'occupyCabinId': 260790, 'carrierPasswordAgent': '37n2uUgHBSbKLz79CNhb1Q==', 'passenger': [{'birthday': '19801020', 'cardIssuePlace': 'CN', 'cardNum': 'G356788', 'gender': 'M', 'baggage': [], 'nationality': 'CN', 'cardExpired': '20290809', 'name': 'wang/jian', 'cardType': 'PP', 'type': 0}], 'carrierCode': 'UO', 'carrierAccountAgent': 'B2BPEKQC0001', 'currency': '', 'carrierAccount': ''}




def post_test():
    """

    Returns:

    """
    company = "sl"
    url = f"http://119.3.169.64:18083/occupy/{company}/"
    # url = f"http://114.116.253.131:18081/occupy/{company}/"
    response = requests.post(url=url, json=post_data)
    print(response.text)


if __name__ == '__main__':
    post_test()
    # while 1:
        #
    # process_dict = {
    #     "task_id": 1111, "log_path": "test.log", "source_dict": post_data,
    #     "enable_proxy": False, "address": "http://yunku:123@58.19.82.41:3138", "retry_count": 2
    # }
    #
    # airline_account = "corp"
    # airline_company = "sl"
    # create_var = locals()
    # scraper = create_var[airline_account.capitalize() + airline_company.upper() + "Scraper"]()
    # result = scraper.process_to_main(process_dict)
    
    #     time.sleep(600)

