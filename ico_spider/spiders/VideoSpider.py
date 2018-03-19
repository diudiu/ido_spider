# -*- coding: utf-8 -*-
#
# -*- coding: utf-8 -*-
from pytube import YouTube
from scrapy.conf import settings
from ..spiders.BaseSpider import BaseSpider
from ..items import ICO


class VideoSpider(BaseSpider):
    name = "video"
    allowed_domains = ["icodrops.com", "icobench.com", "youtube.com"]

    start_urls = []

    def __init__(self, mode='0', *args, **kwargs):
        super(VideoSpider, self).__init__(*args, **kwargs)
        if mode == '0':  # crawl icodrops.com
            self.start_urls.append("https://icodrops.com/category/active-ico/")
            self.start_urls.append("https://icodrops.com/category/upcoming-ico/")
            self.start_urls.append("https://icodrops.com/category/ended-ico/")

    def start_requests(self):
        self.get_cookies()
        for i, url in enumerate(self.start_urls):
            yield self.request(url, self.parse, None)

    def parse(self, response):
        print 'into parse'
        ico_cards = response.xpath(".//div[contains(@class, 'ico-card')]")
        for ico_card in ico_cards:
            item = ICO()
            name = ico_card.xpath('.//div[@class="ico-main-info"]').xpath('.//a[@rel="bookmark"]/text()')[
                        0].extract()
            item["name"] = name
            path = ico_card.xpath(".//h3/a/@href").extract()[0]
            yield self.request(path, self.parse_item_iframe, item)

    def parse_item_iframe(self, response):
        print "into parse_item_iframe"
        self.log('iframe: A response from %s just arrived!' % response.url)
        item = response.meta.get('item')
        try:
            iframe_url = response.css('iframe::attr(src)').extract()[0]
            print iframe_url
            yield self.request(iframe_url, self.download_video, item)
        except IndexError:
            image_url = response.xpath("//div[@class='ico-media']/div/img/@src").extract()
            print "Error iframe", image_url

    def download_video(self, response):
        self.log('download: A response from %s just arrived!' % response.url)
        item = response.meta.get('item')
        filename = item['name'].replace(' ', '').replace('.', '')
        save_path = settings["VIDEO_STORE"]
        video_url = response.xpath("//link[contains(@href, 'youtube.com/watch')]/@href").extract()[0]
        self.log('download video_url: {}'.format(video_url))
        yt = YouTube(video_url)
        yt.streams.filter(subtype='mp4').first().download(save_path, filename=filename)
