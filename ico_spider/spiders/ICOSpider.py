# -*- coding: utf-8 -*-

import urlparse

from scrapy.spider import Spider

from scrapy.selector import Selector

from crawler.items import ICO
from crawler.spiders.BaseSpider import BaseSpider
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
        """
        The lines below is a spider contract. For more info see:
        http://doc.scrapy.org/en/latest/topics/contracts.html

        @url http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/
        @scrapes name
        """
        sel = Selector(response)
        item = ICO()
        self.log('A response from %s just arrived!' % response.url)
        # org_id = urlparse.urlparse(response.url).path.lstrip('/').split('/')[1].split('-')[-1]
        # item['id'] = org_id
        # item['source'] = 'sherdog'
        # item['name'] = sel.xpath('.//h2[@itemprop="name"]/text()').extract()[0]
        # item['combineId'] = 'ICO_sherdog' + org_id
        # self.crawlerDb.ICOs.update({'combineId': item['combineId']}, dict(item), upsert=True)

        yield item
