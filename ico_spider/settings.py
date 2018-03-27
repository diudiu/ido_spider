from os.path import expanduser
from unipath import Path
import config

home = expanduser("~")

BOT_NAME = 'ico_spider'
DOWNLOAD_DELAY = 0.25
COOKIES_ENABLED = True
COOKIES_DEBUG = True
SPIDER_MODULES = ['ico_spider.spiders']
NEWSPIDER_MODULE = 'ico_spider.spiders'
MONGODB_COLLECTION = 'icos'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
# Crawl responsibly by identifying yourself (and your website) on the user-agent

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 30,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 31,
}

ITEM_PIPELINES = {
    'scrapy.pipelines.images.ImagesPipeline': 40,
    'scrapy.pipelines.files.FilesPipeline': 50,
}
MONGODB_SERVER = config.MONGODB_SERVER
MONGODB_PORT = config.MONGODB_PORT
MONGODB_DB = config.MONGODB_DB

PROJECT_DIR = Path(__file__).parent.parent
IMAGES_STORE = PROJECT_DIR.child('images')
FILES_STORE = PROJECT_DIR.child('files')
VIDEO_STORE = PROJECT_DIR.child('video')
MONGODB_ADD_TIMESTAMP = True

SERVER_ADDR = config.SERVER_ADDR

