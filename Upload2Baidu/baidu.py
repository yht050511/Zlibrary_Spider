from cmath import log
import json
import os
import time
import requests
import zxing
import urllib
from urllib.parse import quote
import hashlib
from PIL import Image
import pyzbar.pyzbar as pyzbar
import qr
from colorPrint import *
from crypt import *


class NetDisk():
    def __init__(self, Api_Key, Secret_Key):
        self.getGetQrUrl = f'https://openapi.baidu.com/oauth/2.0/device/code?response_type=device_code&client_id={Api_Key}&scope=basic,netdisk'
        self.getAuthUrl = f'https://openapi.baidu.com/oauth/2.0/token?grant_type=device_token&code=device_code&client_id={Api_Key}&client_secret={Secret_Key}'
        self.oAuthFilePath = './oAuth'

        self.readOAuthFile()

        self.getQuotaUrl = f'https://pan.baidu.com/api/quota?access_token={self.access_token}&checkfree=1&checkexpire=1'
        self.listDirUrl = f'https://pan.baidu.com/rest/2.0/xpan/file?method=list&dir=listPath&order=name&start=0&limit=limitNum&showempty=1&folder=0&access_token={self.access_token}'
        self.deleteUrl = f'http://pan.baidu.com/rest/2.0/xpan/file'
        self.uploadPreUrl = f"http://pan.baidu.com/rest/2.0/xpan/file?method=precreate&access_token={self.access_token}"
        self.sliceTempDir = './sliceTemp/'
        self.uploadFileUrl = f'https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?method=upload&access_token={self.access_token}&type=tmpfile'

    def readOAuthFile(self):
        try:
            f = open(self.oAuthFilePath, 'r')
            r = f.read()
            f.close()
            self.oAuthData = eval(r)
            self.access_token = self.oAuthData['access_token']
            if int(self.oAuthData['expire']) < time.time()+3600*24:
                print('[TRACE] 授权信息已过期.')
                raise ZeroDivisionError
            print('[TRACE] 已授权.')
            return True
        except:
            pass
        print('[TRACE] 无认证信息!请扫码.')
        self.getQr()
        self.getToken()
        return self.readOAuthFile()

    def getQr(self):
        try:
            data = eval(requests.get(self.getGetQrUrl).text)
            self.device_code = data['device_code']
            self.getAuthUrl = self.getAuthUrl.replace(
                'device_code', self.device_code)
            self.getQrUrl = data['qrcode_url'].replace(r'\/', r'/')
            self.qrExpire = time.time()+int(data['expires_in'])
            self.interval = int(data['interval'])
            urllib.request.urlretrieve(self.getQrUrl, "qr.png")
            img = Image.open('qr.png')
            self.qrUrl = pyzbar.decode(img)[0].data.decode('utf-8')
            cprint(self.qrUrl, 'green')
            qr.showQr(self.qrUrl)
            return True
        except BaseException as e:
            cprint(e, 'red')
            print('[ERROR] 获取授权二维码失败!')
            return False

    def getToken(self):
        try:
            while self.qrExpire > time.time():
                data = eval(requests.get(self.getAuthUrl).text)
                print(data)
                if 'access_token' in data:
                    data['expire'] = time.time()+int(data['expires_in'])
                    f = open(self.oAuthFilePath, 'w')
                    f.write(str(data))
                    f.close()
                    self.oAuthData = data
                    return True
                time.sleep(self.interval)
            print('[ERROR] 获取授权码超时!')
            return self.readOAuthFile()
        except BaseException as e:
            cprint(e, 'red')
            print('[ERROR] 获取授权码失败!')
            return False

    def getQuota(self):
        data = json.loads(requests.get(self.getQuotaUrl).text)
        if data['errno'] == 111:
            self.__init__()
            return self.getQuota()
        return {'free': int(data['free'])/1024/1024/1024, 'total': int(data['total'])/1024/1024/1024}

    def listDir(self, dir, limit=1000):
        if int(self.oAuthData['expire']) < time.time()+3600*24:
            self.readOAuthFile()
        dir = quote(dir, 'utf-8')
        url = self.listDirUrl.replace(
            'listPath', dir).replace('limitNum', str(limit))
        data = json.loads(requests.get(url).text)
        if data['errno'] == 111:
            self.__init__()
            return self.listDir(dir, limit)
        if data['errno'] == -9:
            return []
        return data['list']

    def dirExist(self, dir):  # 仅用于查询文件夹是否存在
        dir = quote(dir, 'utf-8')
        url = self.listDirUrl.replace(
            'listPath', dir).replace('limitNum', str(1))
        data = json.loads(requests.get(url).text)

        if data['errno'] == 111:
            self.__init__()
            return self.dirExist(dir)
        if data['errno'] == 0:
            return True
        else:
            return False

    def pathExist(self, path):  # 查询文件/文件夹是否存在
        if path[-1] == '/':
            path = path[:-1]
        dir = path[:-len(path.split('/')[-1])]
        name = path[-len(path.split('/')[-1]):]
        data = self.listDir(dir)
        for i in data:
            if i['server_filename'] == name:
                return True
        return False

    def delete(self, path):
        if int(self.oAuthData['expire']) < time.time()+3600*24:
            self.readOAuthFile()
        params = {
            'method': 'filemanager',
            'access_token': self.access_token,
            'opera': 'delete'
        }
        list = {"path": quote(path, 'utf-8')}
        data = f'async=0&filelist=[{str(list)}]'.replace('\'', '"')
        data = json.loads(requests.post(
            self.deleteUrl, params=params, data=data).text)
        if data['errno'] == 111:
            self.__init__()
            return self.delete(path)

    def upload(self, filePath, path, key):
        # path = quote(path, 'utf-8')
        if int(self.oAuthData['expire']) < time.time()+3600*24:
            self.readOAuthFile()
        f = open(filePath, 'rb')
        d = f.read()
        pc = My_AES_ECB(key)  # 初始化密钥
        d = pc.encrypt(d)
        sizeM = len(d)/1024/1024
        blockNum = int((sizeM)/4)+1
        try:
            os.remove(f'{self.sliceTempDir}*')
        except:
            pass
        blockList = []
        blockFileList = []
        for i in range(0, blockNum):
            k = open(self.sliceTempDir+str(i), 'wb')
            if not i+1 == blockNum:
                data = d[i*4*1024*1024:(i+1)*4*1024*1024]
            else:
                data = d[i*4*1024*1024:]
            k.write(data)
            k.close()
            blockList.append(hashlib.md5(data).digest().hex())
            blockFileList.append(
                ('file', open(self.sliceTempDir+str(i), 'rb')))

        payload = {'path': path,
                   'size': str(int(len(d))),
                   'rtype': '1',
                   'isdir': '0',
                   'autoinit': '1',
                   'block_list': str(blockList).replace('\'', '"')}
        files = []
        data = json.loads(requests.post(self.uploadPreUrl,
                          data=payload, files=files).text)

        if data['return_type'] == 1:
            for i in range(0, blockNum):
                url = self.uploadFileUrl+'&path='+quote(path, 'utf-8') + \
                    '&uploadid='+data['uploadid']+'&partseq='+str(i)
                response = requests.post(url, files=[blockFileList[i]])
                # print(response.text.encode('utf8'))
            url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token={self.access_token}"
            payload = {'path': path,
                       'size': str(int(len(d))),
                       'rtype': '1',
                       'isdir': '0',
                       'uploadid': data['uploadid'],
                       'block_list': str(blockList).replace('\'', '"')}
            data = json.loads(requests.request(
                "POST", url, data=payload).text.encode('utf8'))
            # print(data)
            if data['errno'] == 0:
                return True
            else:
                return False

    def getDownloadLink(self, url):
        try:
            dir = ''
            urlSplit = url.split('/')
            for i in urlSplit:
                if len(dir.split('/')) < len(urlSplit)-1 and i != '':
                    dir += '/'+i
            for i in self.listDir(dir):
                if i['path'] == url:
                    try:
                        return self.getDownloadLinkByFsId(i['fs_id'])
                    except Exception as e:
                        return 0
            return 0
        except Exception as e:
            return 0

    def getDownloadLinkByFsId(self, fs_id):
        url = f"https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas&access_token={self.access_token}"
        payload = {"fsids": "["+str(fs_id)+"]",
                   "dlink": 1}
        data = json.loads(requests.request(
            "POST", url, data=payload).text.encode('utf8'))
        return data['list'][0]['dlink']+f'&access_token={self.access_token}'



