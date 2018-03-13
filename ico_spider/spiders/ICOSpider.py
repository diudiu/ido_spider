# -*- coding: utf-8 -*-

import datetime
import re
import unicodedata

import pytz
from ..utils import util
from ..utils.mongo_handler import MongoBase
from scrapy.selector import Selector
from ..utils.push_data import PushData
from ..items import ICO, Financial, Resource, Rating, ShortReview, Social
from ..spiders.BaseSpider import BaseSpider


class ICOSpider(BaseSpider):
    name = "ico"
    allowed_domains = ["icodrops.com", "icobench.com"]

    start_urls = []

    def __init__(self, mode='0', *args, **kwargs):
        super(ICOSpider, self).__init__(*args, **kwargs)
        if mode == '0':  # crawl icodrops.com
            self.start_urls.append("https://icodrops.com/category/active-ico/")
            self.start_urls.append("https://icodrops.com/category/upcoming-ico/")
            self.start_urls.append("https://icodrops.com/category/ended-ico/")

    def start_requests(self):
        self.get_cookies()
        for i, url in enumerate(self.start_urls):
            yield self.request(url, self.parse, None)

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
                    item['file_urls'] = []
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
                    # 在这里爬开始结束时间的原因是这里的时间稍微准确点（倒计时或者含有小时级别时间的数据）,如果这里爬不到才去details page
                    self._parse_ico_list_page_start_end_time(icoItem, item)
                    # yield self.request(url, self.parse)
                    yield self.request(path, self.parse_ico_drops_items, item)

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
                        hex_dig = util.hex_hash(img)
                        item['avatar'] = hex_dig + '.' + img.split('.')[-1]
                    description = \
                        section.xpath('normalize-space(.//div[@class="ico-description"]/text())')[0].extract()[
                            0].strip()
                    item['description'] = description
                    if item['status'] is not 'upcoming':
                        currentAmountCollected = \
                            section.xpath('.//div[contains(@class,"money-goal")]/text()').extract()[0].strip()
                        financial_item['amountCollected'] = currentAmountCollected

                    # 解析 media 图片， 如果media是图片就保存在resource里，否则用另一个spider下载
                    self._parse_medio_img(response, item)

                    # 解析 websit and whitepaper
                    self._parse_website_and_whitepaper(section, item)

                    self._parse_social_links(section, item)

                else:
                    titleDiv = section.xpath('.//div[contains(@class, "title-h4")]/h4/text()')
                    if len(titleDiv):
                        title = titleDiv[0].extract()
                        if 'token' in title.lower() and 'sale' in title.lower():  # financial section

                            self._parse_details_page_start_end_time(section, item)
                            self._parse_financial(section, item)

                        if 'our rating' in title.lower():  # our rating section
                            self._parse_rating(sel, item)

                        if 'short review' in title.lower():  # short review sections
                            self._parse_short_review(sel, item)

                        if 'additional links' in title.lower():  # additional links section
                            self._parse_additional_links(sel, item)

                        if 'screenshots' in title.lower():  # screenshots section
                            self._parse_screenshots(sel, item)
            # 判断是否更新，并推送数据
            collection = MongoBase("ICOs")
            old = collection.find_one({'source': item['source'], 'ticker': item['ticker']})
            old.pop('_id', None)
            old.pop('create_time', None)
            old.pop('update_time', None)
            new = dict(item)
            if self.compare_ico(old, new):
                collection.update_one({'source': item['source'], 'ticker': item['ticker']}, new, upsert=True)
                pd = PushData()
                pd.push_to_server(item)

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
        sr['other'] = []
        short_reviews = response.xpath(".//div[@class='col-12 info-analysis-list']/li")
        for short_review in short_reviews:
            key = short_review.xpath("./span/text()")[0].extract().strip()[:-1]
            value = short_review.xpath("./text()")[0].extract().strip()
            if 'exchanges' in key.lower():
                sr['exchanges'] = value
            elif 'number of team members' in key.lower():
                sr['teamNumber'] = value
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
            elif 'social activity level' in key.lower():
                sr['socialActivity'] = value
            elif 'role of token' in key.lower():
                sr['roleOfToken'] = value
            else:
                sr['other'].append(key)     # 其他未定义字段暂时放到other里，以便以后定位

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
        ico_screenshots = response.xpath('//div[contains(@class, "col-6 col-md-3")]')
        for ico_screenshot in ico_screenshots:
            screenshots = Resource()
            img = ico_screenshot.xpath(".//img/@src")[0].extract()
            item['image_urls'].append(img)
            hex_dig = util.hex_hash(img)
            screenshots['link'] = hex_dig + '.' + img.split('.')[-1]
            try:
                key = ico_screenshot.xpath(".//div[contains(@class, 'screenshot-title')]/text()").extract()[0]
            except IndexError:
                key = None

            screenshots['title'] = key
            screenshots['type'] = 'screenshots'
            item['resources'].append(screenshots)

    def _parse_medio_img(self, response, item):
        try:
            img = response.xpath("//div[@class='ico-media']/div/img/@src")[0].extract()
            item['image_urls'].append(img)
            media = Resource()
            hex_dig = util.hex_hash(img)
            media['link'] = hex_dig + '.' + img.split('.')[-1]
            media['type'] = 'image'
            media['title'] = 'media'
            item['resources'].append(media)
        except IndexError:
            pass

    def _parse_financial(self, section, item):
        li_element = section.xpath('.//li')
        financial_item = item['financial']
        for li in li_element:
            key = li.xpath('./span/text()')[0].extract()
            value = li.xpath('text()')[0].extract()
            value = unicodedata.normalize("NFKD", value)
            key = unicodedata.normalize("NFKD", key)
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
            elif "participate" in key.lower():
                financial_item['can_not_participate'] = map(unicode.strip, value.split(','))
            elif 'KYC' in key:
                financial_item['kycInfo'] = value
            elif 'max' in key.lower() and 'min' in key.lower() and 'cap' in key.lower():
                financial_item['minPersonalCap'] = value.split('/')[1].strip()
                financial_item['maxPersonalCap'] = value.split('/')[1].strip()

    def _parse_details_page_start_end_time(self, section, item):
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

    def _parse_ico_list_page_start_end_time(self, icoItem, item):
        timezone = pytz.timezone("America/Los_Angeles")
        mydatetime = datetime.datetime.now()
        if item['status'] == 'active':
            date = icoItem.xpath('.//div[@class="date"]/@data-date')[0].extract()
            item['endTime'] = util.parseDateStringToUTC(date, "%Y-%m-%d %H:%M:%S")  # date有可能是非日期型字符串
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

    def _parse_website_and_whitepaper(self, section, item):
        button_keys = section.xpath(".//div[contains(@class, 'ico-right-col')]/a/div/text()")
        button_values = section.xpath(".//div[contains(@class, 'ico-right-col')]/a/@href")
        button_keys = [button_key.extract().strip().lower() for button_key in button_keys]
        button_values = [button_val.extract().strip().lower() for button_val in button_values]
        for key, value in dict(zip(button_keys, button_values)).items():
            btn = Resource()
            if key == 'whitepaper' and value.split('.')[-1].lower() in ['pdf', 'doc', 'docx']:
                item['file_urls'].append(value)
                value = util.hex_hash(value) + '.' + value.split('.')[-1].lower()
            btn['type'] = key
            btn['title'] = key
            btn['link'] = value
            item['resources'].append(btn)

    def _parse_social_links(self, section, item):
        soc_links = section.xpath('.//div[@class="soc_links"]/a/@href').extract()
        for link in soc_links:
            social_network = Social()
            if 'facebook' in link or 'fb.me' in link:
                social_network['network'] = 'facebook'
            elif 'github.com' in link:
                social_network['network'] = 'github'
            elif 'twitter' in link or '//t.co' in link:
                social_network['network'] = 'twitter'
            elif 't.me' in link or 'telegram' in link:
                social_network['network'] = 'telegram'
            elif 'bitcointalk.org' in link:
                social_network['network'] = 'bitcointalk'
            elif 'youtube' in link:
                social_network['network'] = 'youtube'
            elif 'slack.' in link:
                social_network['network'] = 'slack'
            elif 'medium.com' in link:
                social_network['network'] = 'medium'
            elif 'reddit.com' in link:
                social_network['network'] = 'reddit'
            else:
                print ('not wellknown ' + link)

            # Only add this network if it is wellknown
            if 'network' in social_network:
                social_network['link'] = link
                item['social_links'].append(social_network)

    def compare_ico(self, old, new):
        return cmp(old, new)
