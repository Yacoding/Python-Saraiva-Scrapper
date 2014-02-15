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

    def __init__(self, urlList, category):
        QThread.__init__(self)
        self.logger = LogManager(__name__)
        self.spider = Spider()
        self.regex = Regex()
        self.utils = Utils()
        self.urlList = urlList
        self.category = category
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
                        print 'Max recored', self.maxRecords
                        self.total = 0
                        print 'URL: ' + str(paginationUrl)
                        sortList = ['&isort=globalpop', '&isort=best', '&isort=title', '&isort=title+rev',
                                    '&isort=price+rev',
                                    '&isort=price', '&isort=date+rev']
                        for sort in sortList:
                            self.scrapReformatData(paginationUrl, sort)
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
            print 'URL when reformat: ', url
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
                    print detailUrl
                    detailUrl = self.regex.replaceData('(?i)&isort=[a-zA-Z]+', '', detailUrl)
                    print detailUrl
                    detailUrl += '&cnt=60'

                if soup.find('span', class_='sli_ultima').find('a') is not None:
                    lastLink = soup.find('span', class_='sli_ultima').find('a').get('href')
                    print 'Last link: ', lastLink
                    maxData = self.regex.getSearchedData('(?i)(\d+)$', lastLink)
                    print 'Max data: ', maxData
                del soup
                return detailUrl, maxData
        except Exception, x:
            print x
            self.logger.error('Exception at reformat url: ', x.message)
        return detailUrl, maxData

    def scrapReformatData(self, url, sort='', page=0, retry=0):
        try:
            # mainUrl = url + "&srt=" + str(page * 60) + sort
            mainUrl = url + "&srt=" + str(page * 60) + sort
            print 'Main URL: ' + mainUrl
            self.notifySaraiva.emit('<font color=green><b>Saraiva URL: %s</b></font>' % mainUrl)
            data = self.spider.fetchData(mainUrl)
            if data and len(data) > 0:
                data = self.regex.reduceNewLine(data)
                data = self.regex.reduceBlankSpace(data)
                # TODO
                # self.scrapData(data)

                if int((page + 1) * 60) < int(self.maxRecords):
                    del data
                    return self.scrapReformatData(url, sort, page + 1, retry=0)
        except Exception, x:
            print x.message
            self.logger.error('Exception at scrap reformat data: ', x.message)
            if retry < 5:
                self.scrapReformatData(url, sort, page, retry + 1)

    def scrapData(self, data):
        try:
            data = self.regex.reduceNewLine(data)
            data = self.regex.reduceBlankSpace(data)
            results = None
            soup = BeautifulSoup(data, from_encoding='iso-8859-8')
            if len(soup.find_all('div', id=re.compile('^result_\d+$'))) > 0:
                print 'Total results div pattern: ' + str(len(soup.find_all('div', {'id': re.compile('^result_\d+$')})))
            elif len(soup.find_all('li', id=re.compile('^result_\d+$'))) > 0:
                results = soup.find_all('li', id=re.compile('^result_\d+$'))
                print 'Total results li pattern: ' + str(len(results))

            if results is not None:
                for result in results:
                    print result
                    if self.dbHelper.searchProduct(result.get('name').strip(), self.category) is False:
                        self.dbHelper.saveProduct(result.get('name').strip(), self.category)
                        self.scrapDataFromResultPage(result)
                    else:
                        print 'Duplicate product found [%s]' % result.get('name')
                        self.notifySaraiva.emit(
                            '<font color=red><b>Duplicate product: [%s]</b></font>' % result.get('name'))
                del soup
                del data
                return True
            else:
                del soup
                del data
                return False
        except Exception, x:
            print x
            self.logger.error('Exception at scrap data: ', x.message)

    def scrapDataFromResultPage(self, data):
        try:
            if data and len(data) > 0:
                title = ''
                subTitle = ''
                price = ''
                image = ''
                url = ''

                ## Scrapping Title
                if data.find('span', class_='lrg bold') is not None:
                    title = data.find('span', class_='lrg bold').text

                ## Scrapping SubTitle
                if self.regex.isFoundPattern('(?i)<span class="med reg"[^>]*?>\s*?by.*?</span>', data):
                    subTitle = self.regex.getSearchedData('(?i)<span class="med reg"[^>]*?>\s*?by(.*?)</span>', data)
                elif self.regex.isFoundPattern('(?i)<span class="ptBrand">by.*?</span>', data):
                    subTitle = self.regex.getSearchedData('(?i)<span class="ptBrand">by(.*?)</span>', data)

                if subTitle is not None:
                    subTitle = self.regex.replaceData('(?i)<a href=[^>]*?>', '', subTitle)
                    subTitle = self.regex.replaceData('(?i)</a>', '', subTitle)
                    subTitle = self.regex.replaceData('(?i) and', ',', subTitle)

                ## Scrapping Price
                if data.find('span', class_='red bld') is not None:
                    price = data.find('span', class_='red bld').text
                elif data.find('span', class_='bld lrg red') is not None:
                    price = data.find('span', class_='bld lrg red').text

                ## Scrapping Image
                if data.find('img', class_='ilo2 ilc2').get('src'):
                    image = data.find('img', class_='ilo2 ilc2').get('src')

                ##Scrapping URL
                if data.find('h3', class_='newaps').find('a').get('href') is not None:
                    url = data.find('h3', class_='newaps').find('a').get('href')
                print 'URL: ', url
                print 'Title: ' + title + ', Sub Title: ' + subTitle + ', Price: ' + price + ', Image: ' + image
                return self.scrapProductDetail(url, title, subTitle, price, image)
            return False
        except Exception, x:
            print x.message
            self.logger.error('Exception at scrap data from result page: ', x.message)

    def scrapProductDetail(self, url, title, subTitle, price, productImage):
        try:
            print 'Product URL: ', url
            self.notifySaraiva.emit('<font color=green><b>Product Details URL [%s].</b></font>' % url)
            data = self.spider.fetchData(url)
            if data and len(data) > 0:
                data = self.regex.reduceNewLine(data)
                data = self.regex.reduceBlankSpace(data)

                soup = BeautifulSoup(data, from_encoding='iso-8859-8')
                productSpec = None
                if soup.find('div', id='detailBullets_feature_div') is not None:
                    productSpec = soup.find('div', id='detailBullets_feature_div').find_all('span',
                                                                                            class_='a-list-item')

                ## Sub Title for Product
                if not subTitle or len(subTitle) == 0:
                    if soup.find('a', id='brand') is not None:
                        subTitle = soup.find('a', id='brand').text
                    elif soup.find_all('span', class_='author notFaded'):
                        print soup.find_all('span', class_='author notFaded')
                        subTitle = ', '.join([x.text for x in soup.find_all('span', class_='author notFaded')])
                    elif self.regex.isFoundPattern('(?i)<span class="brandLink"> <a href="[^"]*?"[^>]*?>([^<]*)</a>',
                                                   data):
                        subTitle = self.regex.getSearchedData(
                            '(?i)<span class="brandLink"> <a href="[^"]*?"[^>]*?>([^<]*)</a>', data)
                    elif self.regex.isFoundPattern('(?i)<span >\s*?by[^<]*<a href="[^"]*"[^>]*?>([^<]*)</a>', data):
                        subTitle = self.regex.getSearchedData('(?i)<span >\s*?by[^<]*<a href="[^"]*"[^>]*?>([^<]*)</a>',
                                                              data)
                    print "Sub Title: " + subTitle

                ## SKU for Product
                sku = 'N/A'
                if productSpec is not None:
                    sku = self.scrapProductSpec(productSpec, 'ASIN')
                elif self.regex.isFoundPattern('(?i)<li><b>ASIN:\s*?</b>([^<]*)<', data):
                    skuChunk = self.regex.getSearchedData('(?i)<li><b>ASIN:\s*?</b>([^<]*)<', data)
                    if skuChunk and len(skuChunk) > 0:
                        sku = skuChunk.strip()
                elif self.regex.isFoundPattern('(?i)<li><b>ISBN-13:</b>([^<]*)<', data):
                    skuChunk = self.regex.getSearchedData('(?i)<li><b>ISBN-13:</b>([^<]*)<', data)
                    if skuChunk and len(skuChunk) > 0:
                        sku = skuChunk.strip()
                print 'SKU: ', sku

                ## Shipping Weight for Product
                weight = 'N/A'
                if productSpec is not None:
                    weight = self.scrapProductSpec(productSpec, 'Shipping Weight')
                elif self.regex.isFoundPattern('(?i)<li>\s*?<b>Shipping Weight:</b>.*?</li>', data):
                    weightChunk = self.regex.getSearchedData('(?i)(<li><b>\s*?Shipping Weight\:</b>.*?</li>)', data)
                    if weightChunk and len(weightChunk) > 0:
                        weightChunk = self.regex.replaceData('(?i)\(.*?\)', '', weightChunk)
                        weight = self.regex.getSearchedData('(?i)<li>\s*?<b>\s*?Shipping Weight\:</b>([^<]*)</li>',
                                                            weightChunk)
                        weight = weight.strip()
                elif self.regex.isFoundPattern('(?i)<li>\s*?<b>\s*?Product Dimensions\:\s*?</b>.*?</li>', data):
                    weightChunk = self.regex.getSearchedData(
                        '(?i)(<li>\s*?<b>\s*?Product Dimensions\:\s*?</b>.*?</li>)',
                        data)
                    if weightChunk and len(weightChunk) > 0:
                        weightChunk = self.regex.replaceData('(?i)\(.*?\)', '', weightChunk)
                        weight = self.regex.getSearchedData('(?i)([0-9. ]+ounces)', weightChunk)
                        weight = weight.strip() if weight is not None else 'N/A'
                print 'WEIGHT: ', weight

                images = self.scrapImages(data)
                if productImage is not None and len(productImage) > 0:
                    productImage = self.regex.getSearchedData(
                        '(?i)(http://ecx.images-Saraiva.com/images/I/[^\.]*)\._.*?$', productImage)
                    if productImage and len(productImage) > 0:
                        productImage += '.jpg'
                        images.append(productImage)
                print 'SCRAPED IMAGES: ', images
                image = ', '.join(images)

                csvData = [sku, title, subTitle, price, weight, image]
                self.csvWriter.writeCsvRow(csvData)
                print csvData
                self.total += 1
                self.notifySaraiva.emit('<font color=black><b>All Products Scraped: [%s].</b></font>' % str(self.total))
                del data
                del soup
        except Exception, x:
            print x.message
            self.logger.error('Exception at scrap product detail: ', x.message)

    def scrapProductSpec(self, data, pattern):
        try:
            dataChunk = [w for w in data if pattern in w.text]
            dataChunk = dataChunk[0].find_all('span') if dataChunk is not None and len(dataChunk) > 0 else None
            spec = dataChunk[1] if dataChunk is not None and len(dataChunk) > 1 else None
            spec = self.regex.replaceData('(?i)\(.*?\)', '', spec.text) if spec is not None else None
            return spec.strip() if spec is not None else 'N/A'
        except Exception, x:
            print x
            self.logger.error('Exception at scrap product spec: ', x.message)
        return 'N/A'

    def scrapImages(self, data):
        images = []

        try:
            soup = BeautifulSoup(data)
            imageThumbs = soup.find_all('li', class_='a-spacing-small item')
            ## If matched with this pattern
            if imageThumbs is not None and len(imageThumbs) > 0:
                for imageChunk in soup.find_all('li', class_='a-spacing-small item'):
                    if imageChunk and len(imageChunk) > 0:
                        image = self.regex.getSearchedData(
                            '(?i)(http://ecx.images-Saraiva.com/images/I/[^\.]*)\._.*?$',
                            imageChunk.find('img').get('src'))
                        if image and len(image) > 0:
                            image += '.jpg'
                            if image not in images:
                                images.append(image)
            elif self.regex.isFoundPattern('(?i)<div id="thumb_\d+_inner"[^>]*?>.*?</div>', data):
                imageChunks = self.regex.getAllSearchedData('(?i)<div id="thumb_\d+_inner"[^>]*?>(.*?)</div>', data)
                if imageChunks and len(imageChunks) > 0:
                    for imageChunk in imageChunks:
                        imageChunk = self.regex.getSearchedData('(?i)\((.*?)\)', imageChunk)
                        image = self.regex.getSearchedData('(?i)(http://ecx.images-Saraiva.com/images/I/[^.]*)\._.*?$'
                            , imageChunk)
                        if image and len(image) > 0:
                            image += '.jpg'
                            if image not in images:
                                images.append(image)

            ## Else if it matches with this pattern
            elif self.regex.isFoundPattern('(?i)<td class="tiny"><img.*?src="[^"]*"', data):
                imageChunks = self.regex.getAllSearchedData('(?i)<td class="tiny"><img.*?src="([^"]*)"', data)
                if imageChunks and len(imageChunks) > 0:
                    for imageChunk in imageChunks:
                        if imageChunk and len(imageChunk) > 0:
                            image = self.regex.getSearchedData(
                                '(?i)(http://ecx.images-Saraiva.com/images/I/[^.]*)\._.*?$', imageChunk)
                            if image and len(image) > 0:
                                image += '.jpg'
                                if image not in images:
                                    images.append(image)
            elif self.regex.isFoundPattern(
                    '(?i)<div id="main-image-wrapper-outer">(.*?)<div id="main-image-unavailable">',
                    data):
                imageChunk = self.regex.getSearchedData(
                    '(?i)<div id="main-image-wrapper-outer">(.*?)<div id="main-image-unavailable">', data)
                if imageChunk and len(imageChunk) > 0:
                    mainImage = self.regex.getSearchedData('(?i)<img id="main-image" src="([^"]*)"', imageChunk)
                    mainImage = self.regex.getSearchedData('(?i)(http://ecx.images-Saraiva.com/images/I/[^.]*)\._.*?$',
                                                           mainImage)

                    if mainImage and len(mainImage) > 0:
                        mainImage += '.jpg'
                        if mainImage not in images:
                            images.append(mainImage)
                    otherImages = self.regex.getAllSearchedData('(?i)src=\'(.*?)\'', imageChunk)
                    if otherImages and len(otherImages) > 0:
                        for otherImage in otherImages:
                            otherImage = self.regex.getSearchedData(
                                '(?i)(http://ecx.images-Saraiva.com/images/I/[^.]*)\._.*?$', otherImage)
                            otherImage += '.jpg'
                            if otherImage not in images:
                                images.append(otherImage)

            elif self.regex.isFoundPattern('(?i)<h2 class="quorus-product-name">[^<]*</h2> <img src="([^"]*)"', data):
                imageChunk = self.regex.getSearchedData(
                    '(?i)<h2 class="quorus-product-name">[^<]*</h2> <img src="([^"]*)"',
                    data)
                if imageChunk and len(imageChunk) > 0:
                    image = self.regex.getSearchedData('(?i)(http://ecx.images-Saraiva.com/images/I/[^.]*)\._.*?$',
                                                       imageChunk)
                    if image and len(image) > 0:
                        image += '.jpg'
                        if image not in images:
                            images.append(image)

            elif self.regex.isFoundPattern(
                    '(?i)<div customfunctionname="[^"]*" class="[^"]*" id="thumbs-image"[^>]*?>.*?</div>', data):
                imageChunks = self.regex.getSearchedData(
                    '(?i)<div customfunctionname="[^"]*" class="[^"]*" id="thumbs-image"[^>]*?>(.*?)</div>', data)
                if imageChunks and len(imageChunks) > 0:
                    images = self.regex.getAllSearchedData('(?i)src="(http://ecx.images-Saraiva.com/images/I/[^"]*)"'
                        , imageChunks)
                    for image in images:
                        if image not in images:
                            images.append(image)
            elif self.regex.isFoundPattern('(?i)<div id="imageBlockContainer"[^>]*>(.*?)</div> </div></div>', data):
                imageChunks = self.regex.getSearchedData(
                    '(?i)<div id="imageBlockContainer"[^>]*>(.*?)</div> </div></div>',
                    data)
                if imageChunks and len(imageChunks) > 0:
                    images = self.regex.getAllSearchedData('(?i)src="(http://ecx.images-Saraiva.com/images/I/[^"]*)"'
                        , imageChunks)
                    for image in images:
                        if image not in images:
                            images.append(image)
        except Exception, x:
            print x
            self.logger.error('Exception at scrap images: ', x.message)

        return images