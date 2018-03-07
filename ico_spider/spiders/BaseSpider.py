# -*- coding: utf-8 -*-
from scrapy.http import Headers
from scrapy.spider import Spider
import scrapy
from selenium import webdriver
from pymongo import MongoClient
from scrapy.utils.response import open_in_browser
import ico_spider.config as config
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseSpider(Spider):
    # local_client = MongoClient('127.0.0.1', 27017)
    local_client = MongoClient(config.MONGODB_SERVER, config.MONGODB_PORT)
    local_cookie = None
    local_user_agent = None
    # 目前我们只存本地，如果有需要可以存prod


    def request(self, url, callback, item):
        """
         wrapper for scrapy.request
        """
        # cookieStr = "_ym_uid=1519365989608655240; __cfduid=d53f4e6df1e80b707f7d24de35c95c0b71519536411; cp_id_32cab=true; _ym_isad=1; time=3/6/2018, 9:26:30 PM; cf_clearance=599d4a4ad8f8c278dc92cf9ed4947b66aeed0475-1520400927-1800"
        #useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
        # headers = Headers({'user-agent': useragent})
        # cookie = SimpleCookie()
        # cookie.load(cookieStr)
        # Even though SimpleCookie is dictionary-like, it internally uses a Morsel object
        # which is incompatible with requests. Manually construct a dictionary instead.
        # cookies = {}
        # for key, morsel in cookie.items():
        #     cookies[key] = morsel.value

        request = scrapy.Request(url=url,
                                 headers={'user-agent': self.local_user_agent},
                                 cookies=self.local_cookie,
                                 callback=callback,
                                 meta={'item': item})
        return request

    def get_cookies(self):
        print 'get cookie'
        chrome_options = Options()
        chrome_options.add_argument('--dns-prefetch-disable')
        driver = Chrome(chrome_options=chrome_options)
        wait = WebDriverWait(driver, 10)

        # driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver')
        base_url = "https://icodrops.com/"
        driver.get(base_url)
        wait.until(EC.title_contains('ICO Drops'))
        cookies = driver.get_cookies()
        self.local_cookie = cookies
        self.local_user_agent = driver.execute_script("return navigator.userAgent")
        driver.close()
        return cookies
