from os.path import expanduser

home = expanduser("~")

BOT_NAME = 'ico_spider'
DOWNLOAD_DELAY = 1
COOKIES_ENABLED = True
SPIDER_MODULES = ['ico_spider.spiders']
NEWSPIDER_MODULE = 'ico_spider.spiders'

MONGODB_COLLECTION = 'icos'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
ITEM_PIPELINES = {'scrapy.contrib.pipeline.images.ImagesPipeline': 1,
                  # 'mma.pipelines.MongoDBPipeline': 2
                  }
MONGODB_SERVER = "192.168.1.196"
MONGODB_PORT = 27017
MONGODB_DB = "ICO"
# use fighters if crawl only the details
# MONGODB_COLLECTION = "chinese_fighter_details"
# LOG_FILE = home + '/logs/boxerec_daily_update.txt'
# LOG_LEVEL = 'INFO'
IMAGES_STORE = 'images'
MONGODB_ADD_TIMESTAMP = True

