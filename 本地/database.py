# 数据库操作程序
# 服务端客户端均需要

import time
import pymysql


def bookExists(bookHref):
    try:
        check_connection()
        string = 'SELECT * FROM `Z-Library`.BookData WHERE bookHref = "' + \
            str(bookHref)+'"'
        cursor.execute(string)
        data = cursor.fetchone()
        db.commit()
        return data != None
    except BaseException as e:
        print("[TRACE] 重新连接数据库.")
        connectDb()
        return bookExists(bookHref)


def getNotDownloadedBooks():
    global cursor
    try:
        check_connection()
        cursor = db.cursor()
        string = 'SELECT * FROM `Z-Library`.BookData WHERE downloaded = 0'
        cursor.execute(string)
        data = cursor.fetchall()
        db.commit()
        return data
    except BaseException as e:
        print("[TRACE] 重新连接数据库.")
        connectDb()
        return getNotDownloadedBooks()


def clearDownloadingBooks():
    try:
        global cursor
        check_connection()
        cursor = db.cursor()
        string = 'UPDATE `Z-Library`.BookData SET downloaded = 0 WHERE downloaded = 2'
        cursor.execute(string)
        data = cursor.fetchall()
        db.commit()
        return data
    except BaseException as e:
        print("[TRACE] 重新连接数据库.")
        connectDb()
        return clearDownloadingBooks()


def updateBookDownloadStatus(id, status, bookPath, coverPath):
    try:
        check_connection()
        string = "UPDATE `Z-Library`.BookData SET downloaded=" + \
            str(status)+',bookPath="'+str(bookPath) + \
            '",coverPath="'+str(coverPath)+'" WHERE id='+str(id)
        # print('[TRACE] 更新下载情况')
        cursor.execute(string)
        db.commit()
    except BaseException as e:
        print("[TRACE] 重新连接数据库.")
        connectDb()
        return updateBookDownloadStatus(id, status, bookPath, coverPath)


def addBook(bookData):
    try:
        check_connection()
        print('[TRACE] 添加数据到数据库')
        keys, placeHolder, values = handleItems(bookData)
        insert_sql = "insert into `Z-Library`.BookData(" + \
            keys+") values("+placeHolder+");"
        cursor.execute(insert_sql, values)
        db.commit()
    except BaseException as e:
        print('[ERROR] '+str(e))


def getBookByHref(bookHref):
    try:
        check_connection()
        string = 'SELECT * FROM `Z-Library`.BookData where bookHref = "' + \
            str(bookHref)+'"'
        cursor.execute(string)
        data = cursor.fetchone()
        db.commit()
        return data
    except BaseException as e:
        print("[TRACE] 重新连接数据库.")
        connectDb()
        return getBookByHref(bookHref)


def handleItems(data):  # 处理数据
    keywords = r'''?&|!{}[]()^~*:\\"'+- '''
    keys = ""
    placeHolder = ""
    values = []
    for i in data:  # 对于特殊字符,添加斜杠
        keys += i+','
        placeHolder += '%s'+','
        values.append(str(data[i]))
    keys = keys[:-1]
    placeHolder = placeHolder[:-1]
    return keys, placeHolder, values


# 检查链接,断开重新连接.
def check_connection():
    try:
        db.ping(reconnect=True)
    except:
        connectDb()
        print("[TRACE] 重新连接数据库.")


def connectDb():
    global db, cursor
    while True:
        try:
            db = pymysql.connect(host='填写你的host', user='用户名',
                             password='密码', database='Z-Library', charset='utf8')
            cursor = db.cursor()
            return
        except:
            time.sleep(3)


db = ''
cursor = ''
connectDb()
