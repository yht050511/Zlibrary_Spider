import requests
import sys
import json
from baidu import *
import wget
from crypt import *


key = b'文件加密密钥'
Key = My_AES_ECB(key)


path = sys.argv[1]
savePath = sys.argv[2]

disk = NetDisk('百度网盘开发者API密钥')
url = str(disk.getDownloadLink(path))
print('<url>'+url+'</url>')
if url == '0':
    print('<status>0</status>')
else:
    try:
        filePath = wget.download(url, savePath)
        f = open(filePath, 'rb')
        d = f.read()
        f.close()
        d = Key.decrypt(d)
        f = open(savePath, 'wb')
        f.write(d)
        f.close()
        print('<status>1</status>')
    except BaseException as e:
        print('<status>0</status>')

sys.stdout.flush()
