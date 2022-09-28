import os
import time
from urllib import request
from io import BytesIO
import gzip
import random
from seleniumwire import webdriver

# 我使用的是brightdata,如果你不是,请注意修改代码
# 代理服务器
proxyHost = "代理服务器"
proxyPort = "代理服务器端口"

# 代理隧道验证信息
proxyUser = '代理用户名'  # 用户名
proxyPass = '代理密码'  # 密码
zone = '代理通道名称'  # 代理通道名称
bearerToken = '口令'  # 口令


# 网站验证信息
cookie = r'zlib网站的cookie(F12抓取)'
cookie_dict = {}

# 配置
url = 'https://zh.usa1lib.org/'  # 爬取的网站
timeoutCommon = 10  # 一般超时时间
timeoutChrome = 20  # chrome超时时间
getMaxRetries = 3  # get最大尝试次数
getUtf8MaxRetries = 3  # getUtf8最大尝试次数
gWCrmMaxRetries = 1  # getWithChrome最大尝试次数

opener = ''
drivers = ['', '', '', '']
proxyMeta = ''


def getTotalIps():
    data = os.popen(
        r'curl "https://brightdata.com/api/zone/route_ips?zone='+zone+r'" -H "Content-Type: application/json" -H "Authorization: Bearer '+bearerToken+' "').read()
    return data.splitlines()


def refreshIps():
    data = os.popen(
        r'curl "https://brightdata.com/api/zone/ips/refresh?zone='+zone+r'" -H "Content-Type: application/json" -H "Authorization: Bearer '+bearerToken+' "').read()
    return data


def resetProxy():
    global opener, proxyMeta
    session_id = random.random()
    proxyMeta = "http://%(user)s-session-%(session)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxyHost,
        "port": proxyPort,
        "user": proxyUser,
        "pass": proxyPass,
        "session": session_id,
    }
    proxy_handler = request.ProxyHandler({
        "http": proxyMeta,
        "https": proxyMeta,
    })
    opener = request.build_opener(proxy_handler)


# 获取可链接到目标网站的代理
def getAvalibleProxy():
    resetProxy()
    data = getUtf8(url)
    while data == 0:
        resetProxy()
        data = getUtf8(url)
    while '看来这些域名已经被你的互联网服务商封锁了' in data:
        print('[ERROR] 当前Ip被封锁,刷新中...')
        # print(eval(getUtf8('http://lumtest.com/myip.json'))['country'])
        resetProxy()
        time.sleep(0.5)
        data = getUtf8(url)
        while data == 0:
            resetProxy()
            data = getUtf8(url)
    # print(eval(getUtf8('http://lumtest.com/myip.json'))['country'])


def get(url, num=1):
    try:
        headers = [
            ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44"),
            ("Referer", url),
            ('sec-ch-ua', ' " Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"'),
            ('sec-ch-ua-platform', "Windows"),
            ("sec-ch-ua-mobile", "?0"),
            ("cookie", cookie),
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"),
            ("accept-encoding", "gzip, deflate, br"),
            ("accept-language", "zh-CN,zh;q=0.9,en;q=0.8")
        ]
        opener.addheaders = headers
        return opener.open(url, timeout=timeoutCommon).read()
    except Exception as e:
        print('[ERROR] '+str(e)+',重试中...')
        if num < getMaxRetries:
            return get(url, num+1)
        else:
            return 0


def getUtf8(url, num=1):
    try:
        headers = [
            ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44"),
            ("Referer", url),
            ('sec-ch-ua', ' " Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"'),
            ('sec-ch-ua-platform', "Windows"),
            ("sec-ch-ua-mobile", "?0"),
            ("cookie", cookie),
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"),
            ("accept-encoding", "gzip, deflate, br"),
            ("accept-language", "zh-CN,zh;q=0.9,en;q=0.8")
        ]
        opener.addheaders = headers
        data = opener.open(url, timeout=timeoutCommon).read()
        try:
            return data.decode('utf-8')
        except Exception as e:
            buff = BytesIO(data)
            f = gzip.GzipFile(fileobj=buff)
            return f.read().decode('utf-8')
    except Exception as e:
        print('[ERROR] '+str(e)+',重试中...')
        if num < getUtf8MaxRetries:
            resetProxy()
            return getUtf8(url, num+1)
        else:
            return 0


def interceptorImg(request):
    # Block PNG, JPEG and GIF images
    if request.path.endswith(('.png', '.jpg', '.ico', '.js', '.woff2', '.jpeg', '.gif', '.css')):
        request.abort()


def getWithChrome(url, num=1):
    global drivers
    ch_options = webdriver.ChromeOptions()
    # 为Chrome配置无头模式
    ch_options.add_argument("--headless")
    ch_options.add_argument('--no-sandbox')
    ch_options.add_argument('--disable-gpu')
    ch_options.add_argument('--disable-dev-shm-usage')
    # 设置代理
    proxyOptions = {
        'proxy': {
            'http': proxyMeta,
            'https': proxyMeta,
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
    # 在启动浏览器时加入配置
    drivers[num] = webdriver.Chrome(options=ch_options,
                                    seleniumwire_options=proxyOptions)
    drivers[num].request_interceptor = interceptorImg  # 不加载图片
    drivers[num].set_page_load_timeout(timeoutChrome)  # 设置超时
    # 打开网页
    try:
        drivers[num].get(url)
        # drivers[num].add_cookie(cookie_dict)
        return drivers[num]
    except Exception as e:  # 超时重试
        print('[ERROR] '+str(e)+',重试中...')
        try:
            print('[Close] '+str(num))
            drivers[num].close()
        except BaseException:
            pass
        if num < gWCrmMaxRetries:
            return getWithChrome(url, num+1)
        else:
            return 0


def init():
    getAvalibleProxy()


init()
# print(get(url).decode('utf-8'))
# http://lumtest.com/myip.json
