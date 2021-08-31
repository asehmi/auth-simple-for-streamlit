import base64
from hashlib import md5
# https://www.pycryptodome.org/en/latest/src/examples.html 
from Crypto.Cipher import AES

BLOCK_SIZE = 16

class aes256cbcExtended:
    password = None
    nonce = None
    KEY = None
    IV = None

    def __init__(self, password, nonce=None):
        self.password = password
        self.nonce = nonce if (nonce != None and len(nonce) > 0) else '_'

        password_enc = self.password.encode('utf-8')

        m = md5()
        m.update(password_enc)
        key_enc = m.hexdigest().encode('utf-8')
        self.KEY = key_enc

        m = md5()
        m.update(password_enc + key_enc)
        iv_enc = m.hexdigest().encode('utf-8')
        self.IV = iv_enc[:16]

    def __pad (self, data):
        pad = BLOCK_SIZE - len(data) % BLOCK_SIZE
        return data + (pad * chr(pad)).encode('utf-8')

    def __unpad (self, padded):
        pad = int(padded[-1])
        return padded[:-pad]

    def encrypt(self, plainText):
        data_enc = (plainText + self.nonce).encode('utf-8')
        padded = self.__pad(data_enc)
        aes = AES.new(self.KEY, AES.MODE_CBC, self.IV)
        encrypted = aes.encrypt(padded)
        return base64.urlsafe_b64encode(encrypted).decode("utf-8") 

    def decrypt(self, cipherText):
        data_enc = base64.urlsafe_b64decode(cipherText)
        aes = AES.new(self.KEY, AES.MODE_CBC, self.IV)
        return self.__unpad(aes.decrypt(data_enc)).decode('utf-8')[:-len(self.nonce)]

if __name__ == '__main__':
    password = 'YouWillNeverGuessThisSecretKey32'
    nonce = 'nonsensical'
    # https://ldapwiki.com/wiki/Client%20Secret
    secret_content = 'GBAyfVL7YWtP6gudLIjbRZV_N0dW4f3xETiIxqtokEAZ6FAsBtgyIq0MpU1uQ7J08xOTO2zwP0OuO3pMVAUTid'
    # secret_content = 'This is a top secret message!!'
    encrypted = aes256cbcExtended(password, nonce).encrypt(secret_content)
    decrypted = aes256cbcExtended(password, nonce).decrypt(encrypted)

    print('secret_content:', secret_content)
    print('password      :', password)
    print('nonce         :', nonce)
    print('encrypted     :', encrypted)
    print('decrypted     :', decrypted)
