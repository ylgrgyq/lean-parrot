import hmac
import hashlib
import random
import string
import config

def generate_id(size=10, chars=string.ascii_letters + string.digits):
    return ''.join(random.choices(chars, k=size))

def sign(msg, k):
    return hmac.new(k.encode('utf-8'), msg.encode('utf-8'), hashlib.sha1).digest().hex()

def session_open_sign(peerid, timestamp, nonce):
    return sign(":".join([config.APP_ID, peerid, "", str(timestamp), nonce]), config.APP_MASTER_KEY)
