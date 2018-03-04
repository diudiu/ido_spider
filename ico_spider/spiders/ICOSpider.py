# -*- coding: utf-8 -*-

import urlparse
import datetime
import pytz
import unicodedata
from scrapy.spider import Spider
import hashlib

from scrapy.selector import Selector
from scrapy import Request

from ico_spider.items import ICO, Financial, Resource
from ico_spider.spiders.BaseSpider import BaseSpider
from scrapy.conf import settings


class ICOSpider(BaseSpider):
    name = "ico"
    allowed_domains = ["icodrops.com", "icobench.com"]

    start_urls = []

    def __init__(self, db_name=settings['MONGODB_DB'], mode='0', *args, **kwargs):
        super(ICOSpider, self).__init__(*args, **kwargs)
        self.crawlerDb = self.local_client[db_name]
        if mode == '0':  # crawl icodrops.com
            self.start_urls.append("https://icodrops.com/category/active-ico/")
            # self.start_urls.append("https://icodrops.com/category/upcoming-ico/")
            # self.start_urls.append("https://icodrops.com/category/ended-ico/")

    def parse(self, response):

        sel = Selector(response)
        if 'icodrops.com' in response.url:
            urlsDiv = sel.xpath('//div[@id="ajaxc"]')
            if len(urlsDiv):
                icoList = urlsDiv[0].xpath('.//div[contains(@class, "ico-card")]')
                for icoItem in icoList:
                    path = icoItem.xpath('.//a[@rel="bookmark"]/@href')[0].extract()
                    print (path)
                    item = ICO()
                    item['mileStones'] = []
                    item['resources'] = []
                    item['social_links'] = []
                    item['image_urls'] = []
                    name = icoItem.xpath('.//div[@class="ico-main-info"]').xpath('.//a[@rel="bookmark"]/text()')[
                        0].extract()
                    item['name'] = name.strip()
                    category = icoItem.xpath('.//div[@class="ico-category-name"]/text()')[0].extract().strip()
                    item['categories'] = []
                    item['categories'].append(category)
                    item['source'] = 'icodrops'
                    # we need to recheck this logic
                    date = icoItem.xpath('.//div[@class="date"]/@data-date')[0].extract()
                    endDate = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                    timezone = pytz.timezone("America/Los_Angeles")
                    endDate_utc = timezone.localize(endDate).astimezone(pytz.UTC)
                    item['startTime'] = endDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
                    if 'active-ico' in response.url:
                        item['status'] = 'active'
                    elif 'upcoming-ico' in response.url:
                        item['status'] = 'upcoming'
                    elif 'ended-ico' in response.url:
                        item['status'] = 'ended'

                    yield Request(path, callback=self.parse_ico_drops_items, meta={'item': item})

        self.log('A response from %s just arrived!' % response.url)

    def parse_ico_drops_items(self, response):
        self.log('A response from %s just arrived!' % response.url)
        item = response.meta.get('item')
        sel = Selector(response)
        ico_details = sel.xpath('.//div[contains(@class, "ico-desk")]')
        if len(ico_details):
            for index, section in enumerate(ico_details):
                print (str(index) + " section")
                if index == 0:  # main info
                    icon = section.xpath('.//div[@class="ico-icon"]')
                    if len(icon):
                        img = icon[0].xpath('.//img/@data-src')[0].extract()
                        item['image_urls'].append(img)
                        hash_object = hashlib.sha1()
                        hash_object.update(img)
                        hex_dig = hash_object.hexdigest()
                        item['avatar'] = hex_dig + '.' + img.split('.')[-1]
                    mainInfo = section.xpath('.//div[@class="ico-icon"]')[0]
                else:
                    titleDiv = section.xpath('.//div[contains(@class, "title-h4")]/h4/text()')
                    if len(titleDiv):
                        title = titleDiv[0].extract()
                        print (title)
                        if 'token' in title.lower() and 'sale' in title.lower():  # financial section
                            financial_item = Financial()
                            item['financial'] = financial_item
                            li_element = section.xpath('.//li')
                            for li in li_element:
                                key = li.xpath('./span/text()')[0].extract()
                                value = li.xpath('text()')[0].extract()
                                value = unicodedata.normalize("NFKD", value)
                                print (key)
                                print (value)
                                if 'Ticker' in key:
                                    item['ticker'] = value
                                elif 'Token type' in key:
                                    financial_item['type'] = value
                                elif 'ICO Token Price' in key:
                                    financial_item['ICOPrice'] = value
                                elif 'Fundraising Goal' in key:
                                    financial_item['hardCap'] = value
                                elif 'Total Tokens' in key:
                                    financial_item['tokenNumber'] = value
                                elif 'Available' in key:
                                    financial_item['percentage_distributed_ico'] = value
                                elif 'Whitelist' in key:
                                    whiteList = Resource()
                                    whiteList['type'] = 'whitelist'
                                    whiteList['title'] = value
                                    links = li.xpath('.//a[@class="list__link"]/@href')
                                    if len(links):
                                        whiteList['link'] = links[0].extract()
                                    item['resources'].append(whiteList)
            print (item)

            self.crawlerDb.ICOs.update({'source': item['source'], 'ticker': item['ticker']}, dict(item), upsert=True)

            yield item
