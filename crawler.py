import scrapy
import yaml
import os


class Plugin(scrapy.Item):
    name = scrapy.Field()
    compatiblePhpVersions = scrapy.Field()


class GetShopPluginsPhpVersions(scrapy.Spider):
    name = 'shop-systems'

    def start_requests(self):
        with open(os.path.abspath('config.yml'), 'r') as url:
            links = yaml.load(url)

        for url in links['plugins']:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        item = Plugin()
        item['name'] = response.css('div.markdown-body table tr td::text')[0].get()
        for title in response.css('div.markdown-body table tr'):
            item['compatiblePhpVersions'] = response.css('div.markdown-body table tr td::text')[5].get()

        yield {
            item['name'].capitalize(): item['compatiblePhpVersions']
        }
