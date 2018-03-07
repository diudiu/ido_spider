# -*- coding: utf-8 -*-
from scrapy.cmdline import execute

name = 'ico'
cmd = 'scrapy crawl {}'.format(name)
execute(cmd.split())