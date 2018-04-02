# -*- coding: utf-8 -*-

import re
import os.path
from pytube import YouTube
from scrapy.conf import settings
from scrapy.spider import Spider, Request


class VideoSpider(Spider):
    name = "bench_video"
    allowed_domains = ["icodrops.com", "icobench.com", "youtube.com"]
    domains = "https://icobench.com"
    save_path = settings["VIDEO_STORE"]
    start_urls = []

    def __init__(self, start=1, end=213, *args, **kwargs):
        super(VideoSpider, self).__init__(*args, **kwargs)
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
            yield Request(self.domains + uri, self.parse_video)

        self.current_page += 1
        yield Request(self.base_url.format(self.current_page), self.parse)

    def parse_video(self, response):
        ico_information = response.xpath(".//div[@class='ico_information']")
        name = ico_information.xpath(".//div[contains(@class, 'name')]/h1/text()").extract()[0].split('(')[0]

        onclick_str = ico_information.xpath(".//div[@class='video']/@onclick").extract()[0]
        pattern = "'[a-zA-Z0-9/\.:\s\?\-=_&]*?'"
        video_url = re.search(pattern, onclick_str).group().replace("'", "")
        if not video_url.startswith('http'):
            self.log('onclick_str = {}'.format(onclick_str))
            self.log('video_url = {}'.format(video_url))

        if not self.isdownloaded(name):
            yield Request(video_url, self.parse_video_play_page, name)

    def parse_video_play_page(self, response):
        self.log('video play url: A response from %s just arrived!' % response.url)
        name = response.meta.get('name')
        video_url = response.xpath("//link[contains(@href, 'youtube.com/watch')]/@href").extract()[0]
        self.download_video(video_url, name)

    def isdownloaded(self, name):
        return os.path.isfile(os.path.join(self.save_path, name + '.mp4'))

    def download_video(self, url, name):
        self.log('download video_url: {}'.format(url))
        yt = YouTube(url)
        yt.streams.filter(subtype='mp4').first().download(self.save_path, filename=name)





