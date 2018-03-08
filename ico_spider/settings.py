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
                  'scrapy.contrib.pipeline.files.FilesPipeline': 2,
                  }
MONGODB_SERVER = config.MONGODB_SERVER
MONGODB_PORT = config.MONGODB_PORT
MONGODB_DB = "ICO"
IMAGES_STORE = 'images'
FILES_STORE ='files'
MONGODB_ADD_TIMESTAMP = True

SERVER_ADDR = '127.0.0.1:8080'
