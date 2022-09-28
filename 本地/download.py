# downloaded种类:
#   1=>已下载
#   0=>待下载
#   -1=>无法下载
#   2=>正在下载
import database
import wget
import time
import requests
import os
import threading
import urllib.request as ulib
import sys
import shutil
import tempfile
import math
import socket
import re


root = 'Books'
maxThreadNum = 30
filenameKeywords = ['\\', '/', '*', '>', '<', '?', '"', '|', ':']

socket.setdefaulttimeout(120)

downloadItems = []
finishedNum = 0


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
            print('[ERROR] 超时,放弃下载.', end="")
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        sys.exit()
    return 0


def download(data, num):
    global downloadItems
    try:
        coverPath = ''

        print('[TRACE] 接收任务:'+data[1])

        bookDir = re.sub(r'[\/:*?"<>|]', ' ',
                         str(data[4]), count=0, flags=0)
        dir = root+'/'+bookDir+'/'
        if not os.path.exists(dir):
            os.mkdir(dir)

        ans = str(data[1])
        ans = re.sub(r'[\/:*?"<>|]', ' ', ans, count=0, flags=0)
        if len(ans) > 64:
            ans = ans[:64]
        dir += ans
        while os.path.exists(dir):
            dir += '.2'
        dir += '/'
        os.mkdir(dir)

        try:
            coverPath = dir+'/cover.jpg'
            getFile(data[14], coverPath)
        except BaseException as e:
            coverPath = ''

        downloadPath = dir + '/' + 'book'+'.'+data[7].lower().replace(' ', '')

        getFile(data[15], downloadPath)
        print('[TRACE] 下载成功:'+data[1])
        downloadItems[num]['status'] = 1
        downloadItems[num]['updateData'] = [
            data[0], 1, './'+downloadPath, './'+coverPath]

    except BaseException as e:
        print('[ERROR] 下载失败:'+data[1]+' '+str(e))
        downloadItems[num]['status'] = -1
        downloadItems[num]['updateData'] = (data[0], -1, '', coverPath)


def handlePath(path):
    keywords = ['\\', '/', ':', '*', '?', '"', '>', "<", "|"]
    ans = ''
    for i in path:
        if not i in keywords:
            ans += i
    return ans


database.clearDownloadingBooks()

while True:
    books = database.getNotDownloadedBooks()
    if len(books) > 0 and len(downloadItems)-finishedNum < maxThreadNum:
        database.updateBookDownloadStatus(books[0][0], 2, '', '')
        downloadItems.append(
            {'id': books[0][0], 'name': books[0][1], 'status': 0})
        thread = threading.Thread(
            target=download, args=(books[0], len(downloadItems)-1))
        thread.setDaemon(True)
        thread.start()  # 启动线程
        print('[TRACE] 当前线程数:'+str(len(downloadItems)-finishedNum))

    # 检查下载情况
    for i in downloadItems:
        if not i['status'] == 0:
            database.updateBookDownloadStatus(
                i['updateData'][0], i['updateData'][1], i['updateData'][2], i['updateData'][3])
            i['status'] = 0
            finishedNum += 1
            if len(books) == 0:
                print('[TRACE] 当前线程数:'+str(len(downloadItems)-finishedNum))

    # time.sleep(0.3)
