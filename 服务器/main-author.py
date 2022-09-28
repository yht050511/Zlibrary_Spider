# Z-Library爬虫项目(人类文化保护工程)
# 运行于服务器上,对目标进行下载保存(./temp文件夹)
# 当前方案:服务器获得下载链接后直接下载文件保存,使用server.js传输给客户端(主要流量耗费在服务器)
# 备选方案:服务端仅获得下载链接,客户端读取mysql内downloadHref进行下载(主要流量耗费在VPN)
# 值得一提的是,该网站反爬虫措施非常恐怖,必须使用代理ip,且40%以上的代理ip都被封锁了(使用数据中心/静态住宅).最终我在net.py中加入了getAvalibleIp()函数,对封锁情况进行尝试,直到没被封锁.
# 不仅如此,下载时必须使用selenium进行爬取,requests库会被发现并跳转至图书介绍页.

# 本文件对目标author进行爬取,而不再依赖category-list,因为后者不全,前者作为补充.

import random
import shutil
import sys
import tempfile
import threading
import time
import net
import requests
import database
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import wget
import socket
import os
import string
import urllib.request as ulib
import urllib.parse

rootUrl = 'https://zh.usa1lib.org'
dlSgBookMaxRetries = 3
dlSgTimeout = 20  # 加载页面等待时间
tempFileTimeout = 30*60
serverRoot = 'http://服务器ip:8081/'
socket.setdefaulttimeout(60)


downloadLink = ''
drivers = ['', '', '', '']
tempFiles = []
driversClosed = [1, 1, 1, 1]
downloadingNum = 0
maxDownloadingNum = 10



# 下载整个网站
def downloadWebsite():
    authors=database.getAuthors()
    for i in authors:
        print('\n[TRACE] 当前作者:'+i[0])
        downloadSingleAuthor(i[0])
    return 1


# 下载单个种类
def downloadSingleAuthor(authorName):
    authorName=urllib.parse.quote(authorName)
    num = 1
    while True:
        print('\n[TRACE] 当前页面:'+str(num))
        time.sleep(3)
        status = downloadSinglePageInAuthor(authorName, num)
        if status == 0:
            break
        num += 1
    return 1


# 下载单个页面
def downloadSinglePageInAuthor(authorName, page):
    pageData = getSinglePageInAuthor(authorName, page)
    if len(pageData) == 0:
        return 0
    downloadMultiBooks(pageData,authorName)
    return 1


# 获取单个页面的内容
def getSinglePageInAuthor(authorName, page):
    pageData = []
    url = f'{rootUrl}/s/?q=author:{str(authorName)}&page={str(page)}'
    data = net.getUtf8(url)

    if '看来这些域名已经被你的互联网服务商封锁了' in str(data) or str(data)=='0':
        net.getAvalibleProxy()
        return getSinglePageInAuthor(authorName, page)

    bs = BeautifulSoup(data, 'lxml')
    items = bs.select('#searchResultBox .resItemBox')
    handleEach = [
        "itemData['name']=i.select('h3 a')[0].text.replace('\\n','')",
        "itemData['bookHref']=rootUrl+i.select('h3 a')[0]['href']",
        """
tempData = i.select('.authors')
itemData['authors']=[]
for k in tempData:
    itemData['authors'].append(k.text)
""",
        "itemData['publisher']=i.find_all(attrs={'title': 'Publisher'})[0].text",
        "itemData['coverHref']=i.select('img.cover')[0]['data-src']",
        # "itemData['coverImg']=requests.get(i.select('img.cover')[0]['data-src']).content",
        "itemData['year']=i.select('.property_year .property_value')[0].text",
        "itemData['language']=i.select('.property_language .property_value')[0].text",
        "itemData['format']=i.select('.property__file .property_value')[0].text.split(',')[0]",
        "itemData['size']=i.select('.property__file .property_value')[0].text.split(',')[1].replace(' ','')",
        "itemData['interestScore']=i.select('.book-rating-interest-score')[0].text.replace('\\n','').replace(' ','')",
        "itemData['qualityScore']=i.select('.book-rating-quality-score')[0].text.replace('\\n','').replace(' ','')",
        "itemData['category']=bs.select('.page-title__name')[0].text.replace('\\n','')",
    ]

    for i in items:
        itemData = {'name': 'undefined',
                    'authors': 'undefined',
                    'publisher': 'undefined',
                    'detail': 'undefined',
                    'category': 'Author-'+urllib.parse.unquote(authorName),
                    'year': 'undefined',
                    'language': 'undefined',
                    'format': 'undefined',
                    'size': 'undefined',
                    'interestScore': 'undefined',
                    'qualityScore': 'undefined',
                    'comments': 'undefined',
                    # 'coverImg': 'undefined',
                    'bookHref': 'undefined',
                    'coverHref': 'undefined',
                    'downloadHref': 'undefined',
                    }
        for j in handleEach:
            try:
                exec(j)
            except Exception as e:
                # print(e)
                continue

        pageData.append(itemData)

    return pageData


# 下载多本图书
def downloadMultiBooks(Data,authorName):
    global tempFiles
    for data in Data:
        if (data['language'] == 'chinese' or (data['language'] == 'undefined' and isChinese(data["name"]))) and database.authorRight(urllib.parse.unquote(authorName),data['authors']) and not database.bookExists(data['bookHref']):
            print('[TRACE] 处理图书:'+data["name"])
            print('[TRACE] 获取下载链接...')
            status, dlUrl, detail, comments = downloadSingleBook(
                data['bookHref'])
            if status:
                data['downloadHref'] = dlUrl
                data['detail'] = detail
                data['comments'] = comments
                print('[TRACE] 获取成功.')
                if maxDownloadingNum-1 < downloadingNum:
                    print('[TRACE] 已达到下载数量限制,等待中...')
                    while maxDownloadingNum-1 < downloadingNum:
                        time.sleep(1)
                print('[TRACE] 开始下载. '+dlUrl)
                thread = threading.Thread(
                    target=downloadAndcommit, args=(data,))
                thread.setDaemon(True)
                thread.start()
            else:
                print('[ERROR] 获取失败.')
        else:
            print('[TRACE] 跳过图书:'+data['name'])
    return Data


# 对请求进行拦截,当发现token(下载链接)时abort,结束selenium
def interceptorDownload(request):
    global downloadLink
    if 'dtoken' in request.path:
        downloadLink = request.url
        request.abort()
    # 省流量
    if request.path.endswith(('.png', '.jpg', '.ico', '.woff2', '.jpeg', '.gif', '.css')):
        request.abort()


# 下载单本图书
def downloadSingleBook(url, num=1):
    global drivers, downloadLink
    downloadLink = ''
    drivers[num] = net.getWithChrome(url)  # 打开书籍链接
    # 获取下载按钮
    try:
        button = WebDriverWait(drivers[num], dlSgTimeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.dlButton')))
        try:
            detailBox = drivers[num].find_element(
                By.CSS_SELECTOR, '#bookDescriptionBox')
            detail = detailBox.get_attribute('innerHTML')
        except BaseException as e:
            detail = 'undefined'
        try:
            commentsBox = drivers[num].find_elements(
                By.CSS_SELECTOR, '.jscommentsCommentBox')
            comments = []
            for i in commentsBox:
                commentAuthor = i.find_element(
                    By.CSS_SELECTOR, '.jscommentsCommentAuthor div').get_attribute('innerText')
                commentText = i.find_element(
                    By.CSS_SELECTOR, '.jscommentsCommentText').get_attribute('innerText')
                commentDate = i.find_element(
                    By.CSS_SELECTOR, '.jscommentsCommentDate').get_attribute('innerText')
                comments.append({
                    'commentAuthor': commentAuthor,
                    'commentText': commentText,
                    'commentDate': commentDate})
        except BaseException as e:
            comments = 'undefined'
        drivers[num].request_interceptor = interceptorDownload
        button.click()  # 下载
        drivers[num].quit()
        if downloadLink == '':
            raise Exception('Ip次数已用完,刷新中...')
        return 1, downloadLink, detail, comments
    except BaseException as e:
        print('[ERROR] '+str(e))
        try:
            drivers[num].quit()
        except BaseException:
            pass
        if num < dlSgBookMaxRetries:
            net.getAvalibleProxy()
            return downloadSingleBook(url, num+1)
        else:
            return 0, 0, 0, 0


def downloadAndcommit(data):
    global downloadingNum, tempFiles
    downloadingNum += 1
    print('[TRACE] 当前下载数:'+str(downloadingNum))
    try:
        path = randomTempPath()
        name = path
        getFile(data['coverHref'], path)
        data['coverHref'] = serverRoot+name
    except BaseException as e:
        pass

    try:
        path = randomTempPath()
        name = path
        getFile(data['downloadHref'], path)
    except BaseException as e:
        downloadingNum -= 1
        print('[TRACE] '+data['name']+' 下载失败 '+str(e))
        print('[TRACE] 当前下载数:'+str(downloadingNum))
        return 0

    data['downloadHref'] = serverRoot+name
    tempFiles.append({'path': name, 'name': data['name'], 'time': time.time()})
    print('[TRACE] '+data['name']+' 下载成功')
    database.addBook(data)
    # print('[TRACE] 上传成功')
    downloadingNum -= 1
    print('[TRACE] 当前下载数:'+str(downloadingNum))
    return 1


def progress_callback(blocks, block_size, total_size):
    # print(blocks, block_size, total_size)
    pass


def getFile(url, savePath):
    try:
        (fd, tmpfile) = tempfile.mkstemp(
            ".tmp", prefix='tempFile', dir="./temp")
        os.close(fd)
        os.unlink(tmpfile)
        (tmpfile, headers) = ulib.urlretrieve(url, tmpfile, progress_callback)
        if os.path.exists(tmpfile):
            shutil.move(tmpfile, savePath)
            return 1
    except BaseException as e:
        if 'timed out' in str(e):
            print('[ERROR] 超时,放弃下载.')
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
    raise ZeroDivisionError


# 其他函数
# 判断图书是否为中文
def isChinese(ch):
    for i in str(ch):
        if '\u4e00' <= i <= '\u9fff':
            return True
    return False


# 定时删除临时文件
def rmTempFileWhenTimeout():
    global tempFiles
    while True:
        t = time.time()
        for i in tempFiles:
            if t-i['time'] > tempFileTimeout:
                if os.path.exists(i['path']):
                    os.remove(i['path'])
                    print('[TRACE] 临时文件:'+i['name']+',已到期,删除.')
                tempFiles.remove(i)
        time.sleep(0.2)


# 清空临时文件
def rmAllTempFiles():
    os.popen('rm ./temp/* -f')


def randomTempPath():
    path = 'temp/' + \
        ''.join(random.sample(string.ascii_letters + string.digits, 32))
    while os.path.exists(path):
        path = 'temp/' + \
            ''.join(random.sample(string.ascii_letters + string.digits, 32))
    return path


rmAllTempFiles()
thread = threading.Thread(
    target=rmTempFileWhenTimeout, args=())
thread.setDaemon(True)
thread.start()  # 启动线程
print('启动')

downloadWebsite()
# downloadSingleAuthor('xxx')
