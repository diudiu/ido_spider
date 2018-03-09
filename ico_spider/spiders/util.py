import pytz
import hashlib
import json
import requests
import logging
from datetime import datetime, date
from scrapy.conf import settings
from mongo_handler import MongoBase
logger = logging.getLogger(__name__)

def hex_hash(data):
    hash_object = hashlib.sha1()
    hash_object.update(data.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig

# convert date string in format like 3 March 2017, '%d %b %Y' from pacific time to UTC
# example (parseDateStringToUTC('3 Mar 2014','%d %b %Y'))


def parseDateStringToUTC(date, formater):
    try:
        timezone = pytz.timezone("America/Los_Angeles")
        dateObj = datetime.strptime(date, formater)
        endDate_utc = timezone.localize(dateObj).astimezone(pytz.UTC)
        return endDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError as error:
        print ('error parsing ' + date, error)
        return None


def UTCDateStringToDateObj(date):
    try:
        return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    except ValueError as error:
        print ('error parsing ' + date, error)
        return None


def parseDateStringToDateObj(date, formatter):
    try:
        return datetime.strptime(date, formatter)
    except ValueError as error:
        print ('error parsing ' + date, error)
        return None


def _check_key_exsit(item, key):
    try:
        item[key]
        return True
    except KeyError:
        return None


def string_to_int(value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = value.replace(",", "")
        value = int(value)
    return value


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def string_to_datetime(value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = value.replace("T", " ")
        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value


def push_to_server(item):
    server = settings['SERVER_ADDR']
    data = dict()
    data["requestId"] = 1

    ico = {"source": item.get("source", None),
           "ticker": item.get("ticker", None),
           "name": item.get("name", None),
           "category": item.get("category", None),
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
    data.update(ico)

    if _check_key_exsit(item, 'financial'):
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
        data.update({"financial": financial})

    if _check_key_exsit(item, 'rating'):
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
        data.update({"rating": rating})

    if _check_key_exsit(item, 'shortreview'):
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
        data.update({"shortreview": shortreview})

    if _check_key_exsit(item, 'social_links'):
        social = item['social_links']
        data.update({"social": social})

    if _check_key_exsit(item, 'resource'):
        resource = item["resource"]
        data.update({"resource": resource})

    headers = {'Content-type': 'application/json', 'Accept': '*/*'}
    json_data = json.dumps(data, default=str)
    # print json_data
    # log.msg("*" * 30, level=log.INFO)
    # server = 'http://192.168.1.27:8080/push/ico'
    result = requests.post(server, data=json_data, headers=headers)

    if result.ok and result.json().get("code", None) == 0:
        # print result.json().get("code"), ico["name"]
        logging.info("push data to server successful! ico_name = {}".format(ico['name']))
    else:
        msg = result.json().get("msg", None)
        print "Error-------->", result.json().get("code"), msg, ico["name"], "\n"
        # logging.info("push data to server failure! msg = {}".format(msg), encoding='utf8')

if __name__ == '__main__':
    collection = MongoBase("ICOs")
    items = collection.find()
    for i in range(100):
        for item in items:
            push_to_server(item)

