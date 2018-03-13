# -*- coding: utf-8 -*-

from pymongo import MongoClient
from scrapy.conf import settings
from datetime import datetime


def singleton(cls):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


class MongoBase(object):
    def __init__(self, collection):
        self.collection_name = collection
        host = settings["MONGODB_SERVER"]
        port = int(settings["MONGODB_PORT"])
        db = settings["MONGODB_DB"]
        username = settings["MONGODB_USER"]
        password = settings["MONGODB_PASSWORD"]
        self.connection = MongoClient(host=host, port=port)
        self.db = self.connection[db]
        if username and password:
            self.db.authenticate(username, password)
        self.collection = self.db[self.collection_name]

    def __del__(self):
        self.connection.close()

    def insert_one(self, data):
        data.update({'create_time': datetime.now()})
        return self.collection.insert_one(data)

    def update_one(self, query=None, data=None, **kwargs):
        if self.collection.find(query).count() == 0:
            res = self.insert_one(data)
        else:
            keys = data.keys()
            if '_id' in keys:
                del data['_id']
            data.update({'update_time': datetime.now()})
            res = self.collection.update_one(query, {'$set': data}, **kwargs)
        return res

    def find_one(self, query=None):
        if query is None:
            query = {}
        return self.collection.find_one(query)
