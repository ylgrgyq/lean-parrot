import random
import string

def generate_id(size=10, chars=string.ascii_letters + string.digits):
    return ''.join(random.choices(chars, k=size))
