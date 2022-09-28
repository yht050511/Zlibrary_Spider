import database
import re
from baidu import *
from crypt import *
from colorPrint import *


key = b'你文件的加密密钥'
Key = My_AES_ECB(key)
netdisk = NetDisk('百度网盘开发者API密钥')
uploadRoot = '/Data/'


def uploadMultiCategory(categories):
    for c in categories:
        uploadSingleCategory(c)


def uploadSingleCategory(category):
    subcategorys = database.getSubCategoryByCategory(category)
    uploadMultiSubCategory(subcategorys)


def uploadMultiSubCategory(subcategorys):
    for i in subcategorys:
        uploadSingleSubCategory(i)


def uploadSingleSubCategory(subcategory):
    print('[TRACE] 当前类别:'+subcategory)
    categoryData = database.getBooksBySubCategory(subcategory)
    # bytes.fromhex恢复
    dir = uploadRoot+Key.encrypt(subcategory.encode('utf-8')).hex()+'/'
    for i in categoryData:
        name = Key.encrypt(i[1].encode('utf-8')).hex()
        fileDir = re.sub(r'[\/: *?"<> |]', ' ', str(i[4]), count=0, flags=0)
        fileName = re.sub(r'[\/: *?"<> |]', ' ', str(i[1]), count=0, flags=0)
        fileFormat = i[7].lower().replace(' ', '')
        # filePath = f'\\\\192.168.0.112\\Z-Library\\{fileDir}\\{fileName}\\book.{fileFormat}'
        filePath = f'/Z-library/Books/{fileDir}/{fileName}/book.{fileFormat}'
        path = dir+name
        if os.path.exists(filePath) and not netdisk.pathExist(path):
            print('[TRACE] 处理文件:'+fileName)
            print('[TRACE] 上传文件 ', end='', flush=True)
            try:
                status = netdisk.upload(filePath, path, key)
                if not status:
                    raise ZeroDivisionError
                cprint('成功', 'green')
                database.updateBookPath(
                    i[0], 'BaiduDisk://'+path)
                os.remove(filePath)
            except BaseException as e:
                cprint('失败', 'red')
                print(e)
        else:
            print('[TRACE] 跳过文件:'+fileName)



