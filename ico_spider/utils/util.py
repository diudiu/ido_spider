import pytz
import hashlib
import json
from datetime import datetime, date


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


def compare_ico(old, new):
    return cmp(old, new)
