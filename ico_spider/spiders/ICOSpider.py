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
import util
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
                    financial_item = Financial()
                    item['financial'] = financial_item
                    name = icoItem.xpath('.//div[@class="ico-main-info"]').xpath('.//a[@rel="bookmark"]/text()')[
                        0].extract()
                    item['name'] = name.strip()
                    category = icoItem.xpath('.//div[@class="categ_type"]/text()')[0].extract().strip()
                    percentageFinished = icoItem.xpath('.//span[@class="prec"]/text()')
                    if len(percentageFinished):
                        financial_item['percentageCollected'] = percentageFinished[0].extract().strip()
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
                        item['endTime'] = util.parseDateStringToUTC(date, "%Y-%m-%d %H:%M:%S")
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
                                if 'TBA' not in date:
                                    dateObj = util.parseDateStringToDateObj(date + ' ' + str(mydatetime.year),
                                                                            '%d %b %Y')
                                    if dateObj and dateObj < mydatetime:
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
                            utc_date = util.parseDateStringToUTC(date + ' ' + str(mydatetime.year), '%d %b %Y')
                            if utc_date and util.UTCDateStringToDateObj(utc_date) > mydatetime:
                                last_year = str(mydatetime.year - 1)
                                utc_date = util.parseDateStringToUTC(date + ' ' + last_year, '%d %b %Y')
                            item['endTime'] = utc_date
                    yield Request(path, callback=self.parse_ico_drops_items, meta={'item': item})

        self.log('A response from %s just arrived!' % response.url)

    def parse_ico_drops_items(self, response):
        self.log('A response from %s just arrived!' % response.url)
        item = response.meta.get('item')
        financial_item = item['financial']
        sel = Selector(response)
        important_note = sel.xpath('normalize-space(.//div[@class="important-note"]/text())')
        if len(important_note):
            item['message'] = important_note[0].extract()
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
                    description = \
                        section.xpath('normalize-space(.//div[@class="ico-description"]/text())')[0].extract()[
                            0].strip()
                    item['description'] = description
                    if item['status'] is not 'upcoming':
                        currentAmountCollected = \
                            section.xpath('.//div[contains(@class,"money-goal")]/text()').extract()[0].strip()
                        financial_item['amountCollected'] = currentAmountCollected
                else:
                    titleDiv = section.xpath('.//div[contains(@class, "title-h4")]/h4/text()')
                    if len(titleDiv):
                        title = titleDiv[0].extract()
                        if 'token' in title.lower() and 'sale' in title.lower():  # financial section
                            start_end_date = section.xpath(
                                'normalize-space(.//i[contains(@class,"fa-calendar")]/following-sibling::*[1])')[
                                0].extract()
                            if "PERIOD ISN'T SET" in start_end_date:
                                item['startTime'] = None
                                item['endTime'] = None
                            else:
                                start_end_date = start_end_date.split(u"\u2013")
                                if len(start_end_date) > 1:
                                    year = datetime.datetime.now().year
                                    startDate = util.parseDateStringToUTC(
                                        start_end_date[0].split(':')[-1].strip() + ' ' + str(year), '%d %b %Y')
                                    endDate = util.parseDateStringToUTC(start_end_date[1].strip() + ' ' + str(year),
                                                                        '%d %b %Y')
                                    print ('start-end ' + startDate + " - " + endDate)

                                    if not item.get('startTime', None):
                                        item['startTime'] = startDate
                                    if not item.get('endTime', None):
                                        item['endTime'] = endDate

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
            print (item)

            self.crawlerDb.ICOs.update({'source': item['source'], 'ticker': item['ticker']}, dict(item), upsert=True)

            yield item
