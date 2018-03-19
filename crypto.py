import sys

from numpy.polynomial.polynomial import polyval
from numpy import poly1d

ALPHABET = [ chr(i) for i in range(ord('a'),ord('z')+1) ]

plaintext = sys.argv[1]
polynom = poly1d([ int(s) for s in sys.argv[2].split(',') ])

if polynom.order == 0:
    raise Exception("Polynomial must have order larger than 0")

SPACE = ' '

def transpose(plaintext, transposer):
    transposed = []
    for c in plaintext:
        trans = c
        if c.lower() in ALPHABET:
            is_upper = c.isupper()
            
            i = ALPHABET.index(c.lower()) + 1
            value = transposer(i)
            index = value.astype(int) % len(ALPHABET) - 1
            trans = ALPHABET[index]
            
            trans = trans if not is_upper else trans.upper()
        transposed.append(trans)
    return ''.join(transposed)
    
def encrypt(plaintext, polynom):
    return transpose(plaintext, lambda i : polynom(i) )
    
def decrypt(ciphertext, polynom):
    return transpose(ciphertext, lambda i : (polynom - i).roots[0] )

cipher = encrypt(plaintext, polynom)
print cipher
print decrypt(cipher, polynom)


