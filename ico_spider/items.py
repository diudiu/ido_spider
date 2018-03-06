# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy.item import Field


class ICO(scrapy.Item):
    source = Field()  # where we crawled this for example icorating
    ticker = Field()  # the uuid of the ico
    name = Field()  # name of project
    categories = Field()  # categories of this ico
    description = Field()  # basic description
    message = Field()  # extra message related to the ico like alert
    country = Field()
    avatar = Field()
    team = Field()  # team info
    financial = Field()
    mileStones = Field()  # list of mile stones
    resources = Field()  # list of resources
    rating = Field()
    shortreview = Field()
    social_links = Field()
    status = Field()
    startTime = Field()
    endTime = Field()
    image_urls = Field()  # for scrapy image pipeline, do not change name
    images = Field()  # for scrapy image pipeline, do not change name
    create_at = Field()
    update_at = Field()
    sync_done = Field()  # whether this record is put into our prod database


class Team(scrapy.Item):
    teamSize = Field()
    members = Field()


class Member(scrapy.Item):
    name = Field()  # name of person
    avatar = Field()
    nationality = Field()  # country info
    about = Field()  # description of this person
    bio_link = Field()  # a link of this person for example linkedin


class MileStone(scrapy.Item):
    when = Field()
    what = Field()
    index = Field()


class Financial(scrapy.Item):
    token = Field()
    platform = Field()
    type = Field()
    coins_accepted = Field()  # 接受的币种
    percentage_distributed_ico = Field()  # what is the percentage on sale for ico
    softCap = Field()
    hardCap = Field()
    amountCollected = Field()
    percentageCollected = Field()
    tokenNumber = Field()
    minPersonalCap = Field()
    maxPersonalCap = Field()
    bonusInfo = Field()
    bountyInfo = Field()
    kycInfo = Field()
    can_not_participate = Field()  # an array of region or country can not participate  example: [u'USA', u'Singapore', u'China']
    preICOPrice = Field()
    preSaleAmount = Field()
    tokenIssuePolicy = Field()
    ICOPrice = Field()
    currentPrice = Field()


class Rating(scrapy.Item):
    commenter = Field()
    teamScore = Field()
    visionScore = Field()
    prodScore = Field()
    riskLevel = Field()
    hypoLevel = Field()
    ROIScore = Field()
    totalScore = Field()
    comment = Field()


class Social(scrapy.Item):
    network = Field()
    link = Field()


class Resource(scrapy.Item):
    link = Field()
    cover = Field()  # some resource like video might have a cover
    type = Field()  # one of screenshot, video, website, bounty,onepager,prototype,whitepaper,white list
    title = Field()


class ShortReview(scrapy.Item):
    exchagnes = Field()  # Exchanges
    teamNum = Field()  # Number of Team Members
    teamFrom = Field()  # Team from
    prototype = Field()  # Prototype
    unsoldTokens = Field()  # Unsold Tokens
    company = Field()  # Registered Company
    activeFrom = Field()  # ICO Active from
