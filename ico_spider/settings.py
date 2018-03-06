from os.path import expanduser
import config

home = expanduser("~")

BOT_NAME = 'ico_spider'
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = True
SPIDER_MODULES = ['ico_spider.spiders']
NEWSPIDER_MODULE = 'ico_spider.spiders'

MONGODB_COLLECTION = 'icos'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
ITEM_PIPELINES = {'scrapy.contrib.pipeline.images.ImagesPipeline': 1,
                  }
MONGODB_SERVER = config.MONGODB_SERVER
MONGODB_PORT = config.MONGODB_PORT
MONGODB_DB = "ICO"
IMAGES_STORE = 'images'
MONGODB_ADD_TIMESTAMP = True
