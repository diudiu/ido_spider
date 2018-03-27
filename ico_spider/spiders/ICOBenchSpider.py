# -*- coding: utf-8 -*-
#
import re
from scrapy.spider import Spider, Request

from ..items import ICO, Financial, Resource, Rating, Social, Team, Member, MileStone
from ..utils.mongo_handler import MongoBase
from ..utils.push_data import PushData
from ..utils.util import hex_hash, compare_ico


class ICOBenchSpider(Spider):
    name = "icobench"
    allowed_domains = ["icobench.com"]
    domains = "https://icobench.com"

    def __init__(self, start=1, end=213, *args, **kwargs):
        super(ICOBenchSpider, self).__init__(*args, **kwargs)
        self.current_page = start
        self.max_page = end
        self.base_url = "https://icobench.com/icos?page={}"
        self.start_urls = [self.base_url.format(self.current_page)]

    def parse(self, response):
        self.log("正在解析第{}页".format(self.current_page))

        no_data = response.xpath(".//div[@class='ico_list']/div[@class='no_data']")
        if no_data or self.current_page > self.max_page:
            self.log("no data = {}".format(no_data))
            self.log("没有数据或超过指定页，爬虫退出！最大爬取页为:{}".format(self.max_page))
            return

        uris = response.xpath(".//div[@class='content']/a/@href").extract()
        for uri in uris:
            yield Request(self.domains + uri, self.parse_detail)

        self.current_page += 1
        yield Request(self.base_url.format(self.current_page), self.parse)

    def parse_detail(self, response):
        item = ICO()
        item['source'] = 'icobench'
        item['image_urls'] = []
        item['file_urls'] = []
        item['categories'] = []
        item['resources'] = []
        item['social_links'] = []
        item['mileStones'] = []

        # information
        self.parse_information(response, item)

        # rating
        self.parse_rating(response, item)

        # financial
        self.parse_financial(response, item)

        # social
        self.parse_social(response, item)

        # whitepaper
        self.parse_whitepaper(response, item)

        # team
        self.parse_team(response, item)

        # milestones
        self.parse_milestones(response, item)

        # 判断是否更新，并推送数据
        coll = 'icobench'
        collection = MongoBase(coll)
        old = collection.find_one({'source': item['source'], 'ticker': item['ticker']})
        if old:
            old.pop('_id', None)
            old.pop('create_time', None)
            old.pop('update_time', None)
        new = dict(item)
        if compare_ico(old, new):
            collection.update_one({'source': item['source'], 'ticker': item['ticker']}, new, upsert=True)
            pd = PushData(coll)
            # pd.push_data(item)

        # print item
        yield item

    def parse_information(self, response, item):
        ico_information = response.xpath(".//div[@class='ico_information']")
        image_url = ico_information.xpath(".//img/@src").extract()[0]
        item['image_urls'].append(self.domains + image_url)
        item['avatar'] = hex_hash(self.domains + image_url) + '.jpg'
        item["name"] = ico_information.xpath(".//div[contains(@class, 'name')]/h1/text()").extract()[0]
        item["description"] = ico_information.xpath(".//p/text()").extract()[0]
        item['categories'] = ico_information.xpath(".//div[@class='categories']/a/text()").extract()

    def parse_rating(self, response, item):
        rating = Rating()
        rating_block = response.xpath(".//div[@itemprop='aggregateRating']")
        keys = rating_block.xpath(".//div[@class='distribution']/div/label/text()").extract()
        values = rating_block.xpath(".//div[@class='distribution']/div/text()").extract()
        keys = [i.strip() for i in keys]
        values = [i.strip() for i in values if i.strip() != ""]

        for key, value in dict(zip(keys, values)).items():
            if key.lower() == "ico profile":
                rating["commenter"] = value
            elif key.lower() == "team":
                rating["teamScore"] = value
            elif key.lower() == "vision":
                rating["visionScore"] = value
            elif key.lower() == "product":
                rating["prodScore"] = value

        rating['totalScore'] = rating_block.xpath(".//div[@itemprop='ratingValue']/div[contains(@class, rate)]/text()").extract()[0]
        item["rating"] = rating
        # print rating

    def parse_financial(self, response, item):
        financial = Financial()
        financial['other'] = []
        financial_data = response.xpath(".//div[@class='financial_data']")
        # 未处理已结束的情况
        status = financial_data.xpath(".//div[@class='row']/div/div/text()").extract()[0]
        if status.lower() in ["ended", "unknown"]:
            self.log("status = {}".format(status))
            item['status'] = 'ended'
        else:
            self.log("status = {}".format(status))
            item['status'] = 'active'
            period = financial_data.xpath(".//div[@class='row']/div/small/text()").extract()[0]
            start_time, end_time = period.split(' - ')
            item["startTime"] = start_time
            item["endTime"] = end_time

        keys = financial_data.xpath(".//div[@class='data_row']/div/text()").extract()
        values = financial_data.xpath(".//div[@class='data_row']/div/b/text() |"
                                      ".//div[@class='data_row']/div/b/a/text()").extract()
        keys = [i.strip() for i in keys if i.strip() != '']
        values = [i.strip() for i in values]

        for key, value in dict(zip(keys, values)).items():
            item["ticker"] = item['name']   # 设置ticker是为了兼容icodrops
            if key.lower() == "token":
                financial["token"] = value
                item["ticker"] = value
            elif key.lower() == "preico price":
                financial["preICOPrice"] = value
            elif key.lower() == "price":
                financial["ICOPrice"] = value
            elif key.lower() == "bonus":
                financial["bonusInfo"] = value
            elif key.lower() == "bounty":
                financial["bountyInfo"] = value
            elif key.lower() == "platform":
                financial["platform"] = value
            elif key.lower() == "accepting":
                financial["coins_accepted"] = value
            elif key.lower() == "minimum investment":
                financial["minPersonalCap"] = value
            elif key.lower() == "soft cap":
                financial["softCap"] = value
            elif key.lower() == "hard cap":
                financial["hardCap"] = value
            elif key.lower() == "country":
                item["country"] = value
            elif key.lower() == "whitelist/kyc":
                financial["kycInfo"] = value
            elif key.lower() == "restricted areas":
                financial["can_not_participate"] = value
            else:
                financial["other"].append(key)

        # parse website
        website = financial_data.xpath("./a/@href").extract()
        if website:
            resource = Resource()
            resource["link"] = website[0].split('?')[0]
            resource["type"] = 'website'
            resource["title"] = 'website'
            item['resources'].append(resource)

        item['financial'] = financial

    def parse_social(self, response, item):
        socials_links = response.xpath(".//div[@class='fixed_data']/div[@class='socials']/a/@href").extract()
        socials_network = response.xpath(".//div[@class='fixed_data']/div[@class='socials']/a/text()").extract()
        for network, link in dict(zip(socials_network, socials_links)).items():
            social = Social()
            if network.lower() == 'www':
                link = link.split("?")[0]
            social["network"] = network
            social["link"] = link
            item['social_links'].append(social)

    def parse_whitepaper(self, response, item):
        resource = Resource()
        wp_link = response.xpath(".//div[@class='tabs']/a/@href").extract()[-1]
        item['file_urls'].append(wp_link)

        resource['link'] = hex_hash(wp_link) + '.pdf'
        resource['type'] = 'whitepaper'
        resource['title'] = 'whitepaper'
        item["resources"].append(resource)

    def parse_team(self, response, item):
        team = Team()
        team["members"] = []
        kards = response.xpath(".//div[@id='team']/div/div[contains(@class, 'col_3')]")

        for kard in kards:
            member = Member()
            member["bio_link"] = []

            pattern = r"/images/icos/team/.*\.jpg"
            avatar_str = kard.xpath("./a/div/@style").extract()[0]
            avatar_uri = re.search(pattern, avatar_str)
            if avatar_uri:
                self.log("匹配头像图片地址成功: {}".format(self.domains + avatar_uri.group()), )
                item["image_urls"].append(self.domains + avatar_uri.group())
                member["avatar"] = hex_hash(avatar_uri.group()) + '.jpg'
            else:
                member["avatar"] = ''
                self.log("没有匹配到头像地址: {}".format(avatar_str))

            member["name"] = kard.xpath("./h3/text()").extract()[0]

            try:
                member["about"] = kard.xpath("./h4/text()").extract()[0]
            except IndexError:
                pass

            socials = kard.xpath("./div[@class='socials']")
            if socials:
                for social in socials:
                    s = Social()
                    s["network"] = social.xpath("./a/text()").extract()[0]
                    s["link"] = social.xpath("./a/@href").extract()[0]
                    member["bio_link"].append(s)

            team["members"].append(member)
        team["teamSize"] = len(team["members"])
        item["team"] = team

    def parse_milestones(self, response, item):
        steps = response.xpath(".//div[@id='milestones']/div/div[contains(@class, 'row')]")
        for step in steps:
            ms = MileStone()
            ms["index"] = step.xpath("./div[@class='number']/text()").extract()[0]
            ms["when"] = step.xpath("./div/div[@class='condition']/text()").extract()[0]
            what = step.xpath("./div[@class='bubble']/p/text()").extract()
            ms["what"] = [w.strip() for w in what]
            item["mileStones"].append(ms)



















