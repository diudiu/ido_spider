# -*- coding: utf-8 -*-

import urlparse
import datetime
import pytz
import unicodedata
from scrapy.spider import Spider
import hashlib
import re
from scrapy.selector import Selector
from scrapy import Request

from ico_spider.items import ICO, Financial, Resource, Rating, ShortReview
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
            self.start_urls.append("https://icodrops.com/category/upcoming-ico/")
            self.start_urls.append("https://icodrops.com/category/ended-ico/")

    def parse(self, response):

        sel = Selector(response)
        if 'icodrops.com' in response.url:
            urlsDiv = sel.xpath('//div[@id="ajaxc"]')
            if len(urlsDiv):
                icoList = urlsDiv[0].xpath('.//div[contains(@class, "ico-card")]')
                for icoItem in icoList:
                    path = icoItem.xpath('.//a[@rel="bookmark"]/@href')[0].extract()
                    item = ICO()
                    item['mileStones'] = []
                    item['resources'] = []
                    item['social_links'] = []
                    item['image_urls'] = []
                    name = icoItem.xpath('.//div[@class="ico-main-info"]').xpath('.//a[@rel="bookmark"]/text()')[
                        0].extract()
                    item['name'] = name.strip()
                    category = icoItem.xpath('.//div[@class="categ_type"]/text()')[0].extract().strip()
                    item['categories'] = []
                    item['categories'].append(category)
                    item['source'] = 'icodrops'

                    if 'active-ico' in response.url:
                        item['status'] = 'active'
                    elif 'upcoming-ico' in response.url:
                        item['status'] = 'upcoming'
                    elif 'ended-ico' in response.url:
                        item['status'] = 'ended'
                    # we need to recheck this logic
                    # 在这里爬开始结束时间的原因是这里的时间稍微准确点
                    timezone = pytz.timezone("America/Los_Angeles")
                    mydatetime = datetime.datetime.now()
                    if item['status'] == 'active':
                        date = icoItem.xpath('.//div[@class="date"]/@data-date')[0].extract()
                        endDate = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                        endDate_utc = timezone.localize(endDate).astimezone(pytz.UTC)
                        item['endTime'] = endDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
                    elif item['status'] == 'upcoming':
                        date = icoItem.xpath('.//div[@class="date"]/text()')[0].extract().strip()
                        if date and "TBA" not in date:
                            # date could be 'in 30h' or '14 March'
                            startDate = None
                            if date.startswith('in'):
                                diff = re.findall(r'\d+', date)[0]
                                if date.endswith('h'):
                                    startDate = mydatetime + datetime.timedelta(hours=int(diff))
                                elif date.endswith('m') or date.endswith('min'):
                                    startDate = mydatetime + datetime.timedelta(minutes=int(diff))
                            else:
                                if 'TBA' in date:
                                    dateObj = datetime.datetime.strptime(date + ' ' + str(mydatetime.year), '%d %b %Y')
                                    if dateObj < mydatetime:
                                        next_year = str(mydatetime.year + 1)
                                        dateObj = datetime.datetime.strptime(date + ' ' + next_year, '%d %b %Y')
                                    startDate = dateObj
                                else:
                                    startDate = None

                            if startDate:
                                startDate_utc = timezone.localize(startDate).astimezone(pytz.UTC)
                                item['startTime'] = startDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
                    elif item['status'] == 'ended':
                        date = icoItem.xpath('normalize-space(.//div[@class="date"])')[0].extract().split(':')[
                            -1].strip()
                        if date and "TBA" not in date:
                            # date is like '14 March'
                            dateObj = datetime.datetime.strptime(date + ' ' + str(mydatetime.year), '%d %b %Y')
                            if dateObj > mydatetime:
                                last_year = str(mydatetime.year - 1)
                                dateObj = datetime.datetime.strptime(date + ' ' + last_year, '%d %b %Y')

                            endDate_utc = timezone.localize(dateObj).astimezone(pytz.UTC)
                            item['endTime'] = endDate_utc.strftime("%Y-%m-%dT%H:%M:%S")
                    yield Request(path, callback=self.parse_ico_drops_items, meta={'item': item})

        self.log('A response from %s just arrived!' % response.url)

    def parse_ico_drops_items(self, response):
        self.log('A response from %s just arrived!' % response.url)
        item = response.meta.get('item')
        sel = Selector(response)
        ico_details = sel.xpath('.//div[contains(@class, "ico-desk")]')
        if len(ico_details):
            for index, section in enumerate(ico_details):
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
                                    if "NO" not in value:
                                        whiteList['type'] = 'whitelist'
                                        whiteList['title'] = value
                                        links = li.xpath('.//a[@class="list__link"]/@href')
                                        if len(links):
                                            whiteList['link'] = links[0].extract()
                                        item['resources'].append(whiteList)
                                elif 'pre-sale' in key.lower() and 'sold' in key.lower():
                                    financial_item['preSaleAmount'] = value
                                elif 'token issue' in key.lower():
                                    financial_item['tokenIssuePolicy'] = value
                                elif 'bonus' in key.lower():
                                    financial_item['bonusInfo'] = value
                                elif 'KYC' in key:
                                    financial_item['kycInfo'] = value
                                elif 'max' in key.lower() and 'min' in key.lower() and 'cap' in key.lower():
                                    financial_item['minPersonalCap'] = value.split('/')[1].strip()
                                    financial_item['maxPersonalCap'] = value.split('/')[1].strip()

                        if 'our rating' in title.lower():        # our rating section
                            self._parse_rating(sel, item)

                        if 'short review' in title.lower():      # short review sections
                            self._parse_short_review(sel, item)

                        if 'additional links' in title.lower():  # additional links section
                            self._parse_additional_links(sel, item)

                        if 'screenshots' in title.lower():  # screenshots section
                            self._parse_screenshots(sel, item)

            print (item)

            self.crawlerDb.ICOs.update({'source': item['source'], 'ticker': item['ticker']}, dict(item), upsert=True)

            yield item

    def _parse_rating(self, response, item):
        rating = Rating()
        rating_field = response.xpath(".//div[contains(@class, 'rating-field')]")
        rating_items = rating_field.xpath(".//div[contains(@class, 'rating-box')]")
        for rating_item in rating_items:
            key = rating_item.xpath(".//p/text()")[0].extract().strip()
            value = rating_item.xpath(".//p/text()")[-1].extract().strip()
            if 'hype rate' in key.lower():
                rating['hypoLevel'] = value
            elif 'risk rate' in key.lower():
                rating['riskLevel'] = value
            elif 'roi rate' in key.lower():
                rating['ROIScore'] = value
            elif 'ICO Dr' in key:
                rating['totalScore'] = value
        item['rating'] = rating

    def _parse_short_review(self, response, item):
        sr = ShortReview()
        short_reviews = response.xpath(".//div[@class='col-12 info-analysis-list']/li")
        for short_review in short_reviews:
            key = short_review.xpath("./span/text()")[0].extract().strip()[:-1]
            value = short_review.xpath("./text()")[0].extract().strip()
            if 'exchanges' in key.lower():
                sr['exchagnes'] = value
            elif 'number of team members' in key.lower():
                sr['teamNum'] = value
            elif 'team from' in key.lower():
                sr['teamFrom'] = value
            elif 'prototype' in key.lower():
                sr['prototype'] = value
            elif 'unsold Tokens' in key.lower():
                sr['unsoldTokens'] = value
            elif 'registered company' in key.lower():
                sr['company'] = value
            elif 'ico active from' in key.lower():
                sr['activeFrom'] = value

        item['shortreview'] = sr

    def _parse_additional_links(self, response, item):
        keys = response.xpath(".//div[@class='col-12']/li/a/text()").extract()
        links = response.xpath(".//div[@class='col-12']/li/a/@href").extract()
        keys = [key.strip() for key in keys]
        links = [link.strip() for link in links]
        for key, link in dict(zip(keys, links)).items():
            addit = Resource()
            addit['type'] = 'additional'
            addit['title'] = key
            addit['link'] = link
            item['resources'].append(addit)

    def _parse_screenshots(self, response, item):
        ico_screenshots = response.xpath('//div[contains(@class, "col-6")]')
        for ico_screenshot in ico_screenshots:
            screenshots = Resource()
            img = ico_screenshot.xpath(".//img/@src")[0].extract()
            item['image_urls'].append(img)
            hex_dig = self.hex_hash(img)
            screenshots['link'] = hex_dig + '.' + img.split('.')[-1]

            key = ico_screenshot.xpath("./div[contains(@class, 'screenshot-title')]/text()").extract()[0]
            screenshots['title'] = key
            screenshots['type'] = 'screenshots'
            item['resources'].append(screenshots)

    def hex_hash(self, data):
        hash_object = hashlib.sha1()
        hash_object.update(data)
        hex_dig = hash_object.hexdigest()
        return hex_dig
