import json
from Crypto.Cipher import AES
import base64

def base64_encode(data):
    data_bytes = bytes.fromhex(data)
    encoded_data = base64.b64encode(data_bytes).decode('utf-8')
    return encoded_data

def AES_ECB_decrypt(ciphertext, key):
    data = base64_encode(ciphertext)
    def add_16(par):
        par = par.encode('utf-8')
        while len(par) % 16 != 0:
            par += b'\x00'
        return par
    aes = AES.new(add_16(key), AES.MODE_ECB)
    text = base64.decodebytes(data.encode('utf-8'))
    decrypt_text = aes.decrypt(text)
    return decrypt_text.decode('utf-8').strip('\0')

def decrypt(content, k):
    key = f"1a2b3c4d{k}"
    text = AES_ECB_decrypt(content[7:], key)
    data = json.loads(text)
    return data
