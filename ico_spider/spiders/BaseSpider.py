# -*- coding: utf-8 -*-

from scrapy.spider import Spider
import scrapy
from selenium import webdriver
from pymongo import MongoClient
from scrapy.utils.response import open_in_browser


class BaseSpider(Spider):
    local_client = MongoClient('127.0.0.1', 27017)
    # 目前我们只存本地，如果有需要可以存prod
