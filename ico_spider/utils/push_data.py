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
               "categoryEn": item.get("categories", None)[0],
               "descriptionEn": item.get("description", None),
               "messageEn": item.get("message", None),
               "countryEn": item.get("country", None),
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
                "tokenEn": item["financial"].get("token", None),
                "platformEn": item["financial"].get("platform", None),
                "typeEn": item["financial"].get("type", None),
                "coinsAcceptedEn": item["financial"].get("coins_accepted", None),
                "percentageDistributedIcoEn": item["financial"].get("percentage_distributed_ico", None),
                "softCapEn": item["financial"].get("softCap", None),
                "hardCapEn": item["financial"].get("hardCap", None),
                "amountCollectedEn": item["financial"].get("amountCollected", None),
                "percentageCollectedEn": item["financial"].get("percentageCollected", None),
                "tokenNumberEn": item["financial"].get("tokenNumber", None),
                "minPersonalCapEn": item["financial"].get("minPersonalCap", None),
                "maxPersonalCapEn": item["financial"].get("maxPersonalCap", None),
                "bonusInfoEn": item["financial"].get("bonusInfo", None),
                "bountyInfoEn": item["financial"].get("bountyInfo", None),
                "kycInfoEn": item["financial"].get("kycInfo", None),
                "preIcoPriceEn": item["financial"].get("preIcoPrice", None),
                "preSaleAmountEn": item["financial"].get("preSaleAmount", None),
                "tokenIssuePolicyEn": item["financial"].get("tokenIssuePolicy", None),
                "icoPriceEn": item["financial"].get("icoPrice", None),
                "currentPriceEn": item["financial"].get("currentPrice", None),
            }
            # financial.update({"tokenNumber": string_to_int(financial["tokenNumber"])})
            financial.update({"preIcoPriceEn": string_to_int(financial["preIcoPriceEn"])})
            self.data.update({"financial": financial})

        if self._check_key_exsit(item, 'rating'):
            rating = {
                "teamScoreEn": item["rating"].get("teamScore", None),
                "visionScoreEn": item["rating"].get("visionScore", None),
                "prodScoreEn": item["rating"].get("prodScore", None),
                "riskLevelEn": item["rating"].get("riskLevel", None),
                "hypoLevelEn": item["rating"].get("hypoLevel", None),
                "roiScoreEn": item["rating"].get("roiScore", None),
                "totalScore": item["rating"].get("totalScore", None),
                "commenterEn": item["rating"].get("commenter", None),
                "commentEn": item["rating"].get("comment", None),
            }
            self.data.update({"rating": rating})

        if self._check_key_exsit(item, 'shortreview'):
            shortReview = {
                "exchagnesEn": item["shortreview"].get("exchagnes", None),
                "teamNumberEn": item["shortreview"].get("teamNumber", None),
                "teamFromEn": item["shortreview"].get("teamFrom", None),
                "prototypeEn": item["shortreview"].get("prototype", None),
                "unsoldTokensEn": item["shortreview"].get("unsoldTokens", None),
                "companyEn": item["shortreview"].get("company", None),
                "activeFromEn": item["shortreview"].get("activeFrom", None),
                "socialActivityEn": item["shortreview"].get("socialActivity", None),
                "roleOfToken": item["shortreview"].get("roleOfToken", None),
                # "otherEn": item["shortreview"].get("other", None),
            }
            self.data.update({"shortReview": shortReview})

        if self._check_key_exsit(item, 'social_links'):
            socials = item['social_links']
            self.data.update({"socials": socials})

        if self._check_key_exsit(item, 'resources'):
            resources = item["resources"]
            for res in resources:
                res['titleEn'] = res.pop('title', None)
            self.data.update({"resources": resources})

        headers = {'Content-type': 'application/json', 'Accept': '*/*'}
        json_data = json.dumps(self.data, default=str)
        try:
            self.log("start push data to server! data = {}".format(json_data), logging.INFO)
            print json_data
            result = requests.post(self.url, data=json_data, headers=headers)
            if result.ok and result.json().get("code", None) == 0:
                msg = result.json().get("msg", None).encode('utf-8')
                self.log("push data to server successful! ico_name = {}, msg = {}".format(ico['name'], msg), logging.INFO)
            else:
                msg = result.json().get("msg", None).encode('utf-8')
                self.log("push data to server failure! ico_name = {}, msg = {}".format(ico['name'], msg), logging.INFO)

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
    items = collection.find().limit(1)
    for item in items:
        pd.push_to_server(item)
