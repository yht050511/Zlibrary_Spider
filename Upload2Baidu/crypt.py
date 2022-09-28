import uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def get_key(len=16):
    """获取指定位数的动态密钥
    """
    key = str(uuid.uuid4()).replace('-', '')[0:len].upper()
    return key.encode()


class My_AES_ECB():
    def __init__(self, key):
        # 密钥必须为8位
        self.key = key
        self.mode = AES.MODE_ECB
        self.cryptor = AES.new(self.key, self.mode)

    def encrypt(self, plain_text):
        encrypted_text = self.cryptor.encrypt(
            pad(plain_text, AES.block_size))
        return encrypted_text

    def decrypt(self, encrypted_text):
        plain_text = self.cryptor.decrypt(encrypted_text)
        plain_text = unpad(plain_text, AES.block_size)
        return plain_text

    def decryptFile(self, path):
        f = open(path, 'rb')
        r = f.read()
        f.close()
        w = self.decrypt(r)
        f = open(path, 'wb')
        f.write(w)
        f.close()
