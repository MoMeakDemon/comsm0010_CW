import hashlib
import time
from binascii import hexlify
import sys



start = time.perf_counter()

orig_message = 'COMSM0010cloud'

def My_CND(zeros, ranges, margin):
    target = (2 ** (256 - zeros)) - 1
    for nonce in range(margin * (ranges-1), margin * ranges):
        input_str = str(orig_message) + str(nonce)
        hashval = hashlib.sha256(hashlib.sha256(input_str.encode('utf-8')).digest()).hexdigest()
        if int(hashval, 16) <= target:
            print("Find it! nonce is " + str(nonce))
            return nonce



a = sys.argv[1]
b = sys.argv[2]
c = sys.argv[3]
a = int(a)
b = int(b)
c = int(c)
nonce = My_CND(a, b, c)
