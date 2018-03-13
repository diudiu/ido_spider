# -*- coding: utf-8 -*-
#

import json
import requests
import logging
from datetime import datetime, date
from requests.exceptions import InvalidSchema
from mongo_handler import MongoBase
from scrapy.conf import settings


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


class PushData(object):
    def __init__(self):
        self.server = settings['SERVER_ADDR']
        self.data = dict()
        self.url = self.server + '/push/ico/'
        self.data["requestId"] = 1

    @property
    def logger(self):
        logger = logging.getLogger('pushdata')
        return logging.LoggerAdapter(logger, {'spider': self})

    def log(self, message, level=logging.DEBUG, **kw):
        self.logger.log(level, message, **kw)

    def push_to_server(self, item):
        ico = {"source": item.get("source", None),
               "ticker": item.get("ticker", None),
               "name": item.get("name", None),
               "category": item.get("categories", None)[0],
               "description": item.get("description", None),
               "message": item.get("message", None),
               "country": item.get("country", None),
               "avatar": item.get("avatar", None),
               "status": item.get("status", None),
               "startTime": item.get("startTime", None),
               "endTime": item.get("endTime", None),
               "updateTime": item.get("updateTime", None)
               }
        ico.update({"startTime": string_to_datetime(ico["startTime"])})
        ico.update({"endTime": string_to_datetime(ico["endTime"])})
        ico.update({"updateTime": string_to_datetime(ico["updateTime"])})

        # data.update({'ico': ico})
        self.data.update(ico)

        if self._check_key_exsit(item, 'financial'):
            financial = {
                "token": item["financial"].get("token", None),
                "platform": item["financial"].get("platform", None),
                "type": item["financial"].get("type", None),
                "coins_accepted": item["financial"].get("coins_accepted", None),
                "percentage_distributed_ico": item["financial"].get("percentage_distributed_ico", None),
                "softCap": item["financial"].get("softCap", None),
                "hardCap": item["financial"].get("hardCap", None),
                "amountCollected": item["financial"].get("amountCollected", None),
                "percentageCollected": item["financial"].get("percentageCollected", None),
                "tokenNumber": item["financial"].get("tokenNumber", None),
                "minPersonalCap": item["financial"].get("minPersonalCap", None),
                "maxPersonalCap": item["financial"].get("maxPersonalCap", None),
                "bonusInfo": item["financial"].get("bonusInfo", None),
                "bountyInfo": item["financial"].get("bountyInfo", None),
                "kycInfo": item["financial"].get("kycInfo", None),
                "preIcoPrice": item["financial"].get("preIcoPrice", None),
                "preSaleAmount": item["financial"].get("preSaleAmount", None),
                "tokenIssuePolicy": item["financial"].get("tokenIssuePolicy", None),
                "icoPrice": item["financial"].get("icoPrice", None),
                "currentPrice": item["financial"].get("currentPrice", None),
            }
            # financial.update({"tokenNumber": string_to_int(financial["tokenNumber"])})
            financial.update({"preIcoPrice": string_to_int(financial["preIcoPrice"])})
            self.data.update({"financial": financial})

        if self._check_key_exsit(item, 'rating'):
            rating = {
                "teamScore": item["rating"].get("teamScore", None),
                "visionScore": item["rating"].get("visionScore", None),
                "prodScore": item["rating"].get("prodScore", None),
                "riskLevel": item["rating"].get("riskLevel", None),
                "hypoLevel": item["rating"].get("hypoLevel", None),
                "roiScore": item["rating"].get("roiScore", None),
                "totalScore": item["rating"].get("totalScore", None),
                "commenter": item["rating"].get("commenter", None),
                "comment": item["rating"].get("comment", None),
            }
            self.data.update({"rating": rating})

        if self._check_key_exsit(item, 'shortreview'):
            shortreview = {
                "exchagnes": item["shortreview"].get("exchagnes", None),
                "teamNumber": item["shortreview"].get("teamNumber", None),
                "teamFrom": item["shortreview"].get("teamFrom", None),
                "prototype": item["shortreview"].get("prototype", None),
                "unsoldTokens": item["shortreview"].get("unsoldTokens", None),
                "company": item["shortreview"].get("company", None),
                "activeFrom": item["shortreview"].get("activeFrom", None),
                "socialActivity": item["shortreview"].get("socialActivity", None),
                "roleOfToken": item["shortreview"].get("roleOfToken", None),
                "other": item["shortreview"].get("other", None),
            }
            self.data.update({"shortreview": shortreview})

        if self._check_key_exsit(item, 'social_links'):
            social = item['social_links']
            self.data.update({"social": social})

        if self._check_key_exsit(item, 'resource'):
            resource = item["resource"]
            self.data.update({"resource": resource})

        headers = {'Content-type': 'application/json', 'Accept': '*/*'}
        json_data = json.dumps(self.data, default=str)
        try:
            self.log("start push data to server!", logging.INFO)
            result = requests.post(self.url, data=json_data, headers=headers)
            if result.ok and result.json().get("code", None) == 0:
                self.log("push data to server successful! ico_name = {}".format(ico['name']), logging.INFO)
            else:
                msg = result.json().get("code", None)
                self.log("push data to server failure! msg = {}".format(msg), logging.INFO)

        except InvalidSchema as e:
            print e

    def _check_key_exsit(self, item, key):

        return key in item.keys()


def string_to_int(value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = value.replace(",", "")
        value = int(value)
    return value


def string_to_datetime(value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = value.replace("T", " ")
        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value

if __name__ == '__main__':
    collection = MongoBase("ICOs")
    pd = PushData()
    items = collection.find()
    for item in items:
        pd.push_to_server(item)
