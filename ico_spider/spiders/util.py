import datetime
import pytz
import hashlib
import json
import requests
import logging
from datetime import datetime, date
from scrapy.conf import settings

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
        dateObj = datetime.datetime.strptime(date, formater)
        endDate_utc = timezone.localize(dateObj).astimezone(pytz.UTC)
        return endDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError as error:
        print ('error parsing ' + date, error)
        return None


def UTCDateStringToDateObj(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    except ValueError as error:
        print ('error parsing ' + date, error)
        return None


def parseDateStringToDateObj(date, formatter):
    try:
        return datetime.datetime.strptime(date, formatter)
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
    if isinstance(value, str):
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
    if isinstance(value, str):
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
        financial.update({"tokenNumber": string_to_int(financial["tokenNumber"])})
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
    print json_data
    # log.msg("*" * 30, level=log.INFO)
    server = 'http://192.168.1.27:8080/push/ico'
    result = requests.post(server, data=json_data, headers=headers)

    if result.ok and result.json().get("code", None) == 0:
        print result.json().get("code")
        logging.info("push data to server successful! ico_name = {}".format(ico['name']))
    else:
        msg = result.json().get("msg", None)
        logging.info("push data to server failure! msg = {}".format(msg), encoding='utf8')

if __name__ == '__main__':
    item = dict({
    "status" : "active",
    "mileStones" : [

    ],
    "financial" : {
        "ICOPrice" : " 1 GMR = 0.32 USD (0.00040 ETH)",
        "maxPersonalCap" : "TBA",
        "tokenIssuePolicy" : "from 1 February 2018 as each transaction is confirmed",
        "percentageCollected" : "6%",
        "minPersonalCap" : "TBA",
        "hardCap" : " 27,600,000 USD (35,000 ETH)",
        "bonusInfo" : "up to +20% Gimmer bonus (",
        "amountCollected" : "$1,617,835",
        "tokenNumber" : "110,000,000",
        "type" : "ERC20",
        "percentage_distributed_ico" : "90,9%"
    },
    "name" : "Gimmer",
    "social_links" : [
        {
            "link" : "https://www.facebook.com/gimmerbot/",
            "network" : "facebook"
        },
        {
            "link" : "https://www.reddit.com/user/GimmerBot/",
            "network" : "reddit"
        },
        {
            "link" : "https://github.com/GimmerBot",
            "network" : "github"
        },
        {
            "link" : "https://twitter.com/gimmerbot",
            "network" : "twitter"
        },
        {
            "link" : "https://t.me/gimmertoken",
            "network" : "telegram"
        },
        {
            "link" : "https://bitcointalk.org/index.php?topic=2299128",
            "network" : "bitcointalk"
        },
        {
            "link" : "https://www.youtube.com/channel/UCnu0BGGDX1MEFt__mGYkP4g",
            "network" : "youtube"
        }
    ],
    "image_urls" : [
        "https://icodrops.com/wp-content/uploads/2017/12/MldHC8Gu_400x400-150x150.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Token-distribution-300x114.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Bonuses-203x300.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Team-lead-300x155.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Advisors-300x222.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Roadmap1-300x237.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Roadmap2-300x237.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Roadmap3-300x225.jpg",
        "https://icodrops.com/wp-content/uploads/2017/12/Gimmer_Roadmap4-300x173.jpg"
    ],
    "avatar" : "ea91ec5fbc1aee1395e9c14ea2ea2daa19f03a92.jpg",
    "source" : "icodrops",
    "resources" : [
        {
            "link" : "https://token.gimmer.net/assets/docs/gimmer-wp-tech-en.pdf",
            "type" : "additional",
            "title" : "Technical Whitepaper"
        },
        {
            "link" : "https://bitcointalk.org/index.php?topic=2604585",
            "type" : "additional",
            "title" : "Bounty program"
        },
        {
            "link" : "https://token.gimmer.net/assets/docs/gimmer-op-en.pdf",
            "type" : "additional",
            "title" : "One Pages"
        },
        {
            "type" : "screenshots",
            "link" : "6cf297e2344fb0d4738f1b406f492bc54342d74d.jpg",
            "title" : "Gimmer Token distribution"
        },
        {
            "type" : "screenshots",
            "link" : "d72c9ffb174b18ca054e087f81bf8eacfe44f8b6.jpg",
            "title" : "Gimmer Bonuses"
        },
        {
            "type" : "screenshots",
            "link" : "5e46d390f95b223eb9b4bf7bab01183d376dfe01.jpg",
            "title" : "Gimmer Team lead"
        },
        {
            "type" : "screenshots",
            "link" : "480d9cb17f9abd0491c758f2c1b845042c46d294.jpg",
            "title" : "Gimmer Advisors"
        },
        {
            "type" : "screenshots",
            "link" : "74b985689e648c090145cd0387d5aff34ec10369.jpg",
            "title" : "Gimmer Roadmap"
        },
        {
            "type" : "screenshots",
            "link" : "161020ee0984b3b8b346b17d411a61bf7ce7e414.jpg",
            "title" : "Gimmer Roadmap2"
        },
        {
            "type" : "screenshots",
            "link" : "7389c5747bdaf94e35731ada1d490568b1dc0816.jpg",
            "title" : "Gimmer Roadmap3"
        },
        {
            "type" : "screenshots",
            "link" : "a69c362b6a93be075a356004630730fc9c9033e5.jpg",
            "title" : "Gimmer Roadmap4"
        }
    ],
    "shortreview" : {
        "prototype" : "Yes",
        "exchagnes" : "isn't tradable until the Token Sale has closed"
    },
    "startTime" : "2018-02-01T08:00:00",
    "message" : "Unfortunately, we have to close our token sale early (effective from 12:00 UTC 26 February), we will be back very soon!",
    "endTime" : "2018-03-31T07:00:00",
    "ticker" : "GMR",
    "categories" : [
        "Trading"
    ],
    "description" : "A"
})

    push_to_server(item)
    # t = "2018-02-15T08:00:00"
    # print string_to_datetime(t)



