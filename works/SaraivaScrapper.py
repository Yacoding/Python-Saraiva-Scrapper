import re
from PyQt4.QtCore import QThread, pyqtSignal
from db.DbHelper import DbHelper
from logs.LogManager import LogManager
from utils.Csv import Csv
from utils.Utils import Utils
from spiders.Spider import Spider
from utils.Regex import Regex
from bs4 import BeautifulSoup

__author__ = 'Rabbi'


class SaraivaScrapper(QThread):
    notifySaraiva = pyqtSignal(object)

    def __init__(self, urlList, category, htmlTag, replaceTag):
        QThread.__init__(self)
        self.logger = LogManager(__name__)
        self.spider = Spider()
        self.regex = Regex()
        self.utils = Utils()
        self.urlList = urlList
        self.category = category
        self.htmlTag = htmlTag
        self.replaceTag = replaceTag
        self.csvWriter = Csv(category + '.csv')
        csvDataHeader = ['Link', 'Name', 'Subtitle', 'Price', 'Synopsis and Characteristics', 'Picture']
        self.csvWriter.writeCsvRow(csvDataHeader)
        self.mainUrl = 'http://busca.livrariasaraiva.com.br'
        self.scrapUrl = None
        self.dbHelper = DbHelper('saraiva.db')
        self.dbHelper.createTable(category)
        self.total = self.dbHelper.getTotalProduct(category)

    def run(self, retry=0):
        try:
            if self.urlList is not None and len(self.urlList):
                for url in self.urlList:
                    if len(url) > 0:
                        url = self.regex.replaceData('(?i)\r', '', url)
                        url = self.regex.replaceData('(?i)\n', '', url)
                        self.notifySaraiva.emit('<font color=green><b>Saraiva Main URL: %s</b></font>' % url)
                        paginationUrl, self.maxRecords = self.reformatUrl(url)
                        self.notifySaraiva.emit(
                            '<font color=black><b>Total Records: %s</b></font>' % str(self.maxRecords))
                        print 'Max records: ', self.maxRecords
                        print 'URL: ' + str(paginationUrl)
                        sortList = ['&isort=globalpop', '&isort=best', '&isort=title', '&isort=title+rev',
                                    '&isort=price+rev',
                                    '&isort=price', '&isort=date+rev']
                        for sort in sortList:
                            self.scrapResults(paginationUrl, sort)
            self.notifySaraiva.emit('<font color=red><b>Saraiva Data Scraping finished.</b></font>')
        except Exception, x:
            print x.message
            self.logger.error('Exception at run: ', x.message)
            if retry < 5:
                self.run(retry + 1)

    def reformatUrl(self, url):
        detailUrl = url
        maxData = 60
        try:
            print 'URL: ', url
            self.notifySaraiva.emit('<font color=black><b>URL: %s</b></font>' % url)
            data = self.spider.fetchData(url)
            if data and len(data) > 0:
                data = self.regex.reduceNewLine(data)
                data = self.regex.reduceBlankSpace(data)
                soup = BeautifulSoup(data)
                detailUrl = url
                maxData = 60
                detailLinkChunk = soup.find('div', class_='sli_makeview sli_font')
                if detailLinkChunk is not None and detailLinkChunk.find('a') is not None:
                    detailUrl = detailLinkChunk.find('a').get('href')
                    detailUrl = self.regex.replaceData('(?i)view=grid', 'view=list', detailUrl)
                    detailUrl = self.regex.replaceData('(?i)&srt=\d+', '', detailUrl)
                    detailUrl = self.regex.replaceData('(?i)&isort=[a-zA-Z]+', '', detailUrl)
                    detailUrl += '&cnt=60'

                if soup.find('span', class_='sli_ultima').find('a') is not None:
                    lastLink = soup.find('span', class_='sli_ultima').find('a').get('href')
                    maxData = self.regex.getSearchedData('(?i)(\d+)$', lastLink)
                del soup
                del data
                return detailUrl, maxData
        except Exception, x:
            print x
            self.logger.error('Exception at reformat url: ', x.message)
        return detailUrl, maxData

    def scrapResults(self, url, sort='', page=0, retry=0):
        try:
            mainUrl = url + "&srt=" + str(page * 60) + sort
            print 'Main URL: ' + mainUrl
            self.notifySaraiva.emit('<font color=green><b>Saraiva URL: %s</b></font>' % mainUrl)
            data = self.spider.fetchData(mainUrl)
            if data and len(data) > 0:
                data = self.regex.reduceNewLine(data)
                data = self.regex.reduceBlankSpace(data)
                self.scrapResultPage(data)

                if int((page + 1) * 60) < int(self.maxRecords):
                    del data
                    return self.scrapResults(url, sort, page + 1, retry=0)
        except Exception, x:
            print x.message
            self.logger.error('Exception at scrap reformat data: ', x.message)
            if retry < 5:
                self.scrapResults(url, sort, page, retry + 1)

    def scrapResultPage(self, data):
        try:
            soup = BeautifulSoup(data, from_encoding='utf-8')
            results = soup.find_all('div', class_='sli_list_result')
            if results is not None and len(results) > 0:
                self.logger.debug('Total records found from this page: %s' % str(len(results)))
                print 'Total records found from this page: ', len(results)
                for result in results:
                    image = ''
                    link = ''
                    name = ''
                    subTitle = ''
                    price = ''
                    productId = None
                    if result.find('div', class_='sli_list_image').find('a') is not None:
                        image = result.find('div', class_='sli_list_image').find('a').find('img').get('src')
                        productId = self.regex.getSearchedData('(?i)pro_id=(\d+)', image)
                        if self.dbHelper.searchProduct(productId, self.category) is True:
                            self.notifySaraiva.emit(
                                '<font color=red><b>Duplicate Product: [%s].</b></font>' % str(productId))
                            continue
                    if result.find('div', class_='sli_list_content') is not None:
                        content = result.find('div', class_='sli_list_content')
                        if content.find('h1', class_='titulo_produto') is not None:
                            titleChunk = content.find('h1', class_='titulo_produto')
                            link = titleChunk.find('a', class_='sli_list_title').get('title')
                            name = titleChunk.find('span', class_='entry-title').text
                        if content.find('h2', class_='titulo_autor') is not None:
                            subTitle = content.find('h2', class_='titulo_autor').text
                    if result.find('div', class_='sli_list_right').find('h3', class_='preco_por') is not None:
                        price = result.find('div', class_='sli_list_right').find('h3', class_='preco_por').text
                        price = self.regex.getSearchedData(u'(?i)\$(.*?)$', price).strip()

                    ## Now scrap product detail and write to csv
                    self.scrapProductDetail(link, name, subTitle, price, image, productId)
            del soup
            del data
        except Exception, x:
            print x
            self.logger.error('Exception at scrap data: ', x.message)

    def scrapProductDetail(self, link, name, subTitle, price, image, productId, retry=0):
        try:
            print 'Product Link: ', link
            self.notifySaraiva.emit('<font color=green><b>Product Details URL: [%s].</b></font>' % link)
            data = self.spider.fetchData(link)
            if data and len(data) > 0:
                data = self.regex.reduceNewLine(data)
                data = self.regex.reduceBlankSpace(data)
                soup = BeautifulSoup(data, from_encoding='utf-8')
                productSpec = ''
                if soup.find('div', id='PassosConteudo') is not None:
                    productSpecs = soup.find('div', id='PassosConteudo').find_all('div', id=re.compile('(?i)aba\d+'))
                    for spec in productSpecs:
                        productSpec += spec.text + '\n'
                    productSpec = self.regex.replaceData(u'(?i)%s' % self.replaceTag, productSpec.encode('utf-8'),
                                                         self.htmlTag.encode('utf-8'))

                csvData = [link, name, subTitle, price, productSpec, image]
                self.csvWriter.writeCsvRow(csvData)
                print csvData
                self.logger.debug(csvData)
                self.dbHelper.saveProduct(productId, self.category)
                self.total += 1
                self.notifySaraiva.emit('<font color=green><b>Product Scraped: [%s].</b></font>' % str(productId))
                self.notifySaraiva.emit(
                    '<font color=black><b>Total Products Scraped: [%s].</b></font>' % str(self.total))
                del data
                del soup
        except Exception, x:
            print 'Exception when scrap product detail: ', x.message
            self.logger.error('Exception at scrap product detail: ', x.message)
            if retry < 5:
                self.notifySaraiva.emit(
                    '<font color=red><b>Exception when scrap product detail for: [%s]! Retry...</b></font>' % str(
                        productId))
                return self.scrapProductDetail(link, name, subTitle, price, image, productId, retry + 1)
            else:
                self.notifySaraiva.emit(
                    '<font color=red><b>Scrap product detail for: [%s] failed after maximum 5 retry!</b></font>' % str(
                        productId))