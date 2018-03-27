# -*- coding: utf-8 -*-
from scrapy.cmdline import execute

# name = 'icodrops'
# name = 'video'
name = 'icobench'
cmd = 'scrapy crawl {}'.format(name)
execute(cmd.split())

