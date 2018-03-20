#!/usr/bin/python
# -*- coding: latin-1 -*-

import sys
import numpy as np

from numpy.polynomial.polynomial import polyval
from numpy import poly1d

ALPHABET = [ chr(i) for i in range(ord('a'),ord('z')+1) ]
SCANDIC_ALPHABET = ALPHABET + [ c.decode('utf8') for c in [ 'å', 'ä', 'ö' ] ]
ALPHABET_LENGTH = len(ALPHABET)

def get_factors(x):
    factors = []
    for i in range(1, x + 1):
        if x % i == 0:
            factors.append(i)
    return factors
    
def common_factors(x, y):
    x_factors = get_factors(x)
    y_factors = get_factors(y)
    return [ f for f in x_factors if f in y_factors ]
    
def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

class Cipher():
    def __init__(self, key, alphabet=ALPHABET):
        self.key = key
        self.alphabet = alphabet
        
    def __call__(self, plaintext):
        return self.encrypt(plaintext)
        
    def encrypt(self, plaintext):
        return plaintext
        
    def decrypt(self, ciphertext):
        return ciphertext
        
    def transpose(self, c, transposer):
        trans = c
        
        if c.lower() in self.alphabet:
            is_upper = c.isupper()
            index = int(transposer(self.alphabet.index(c.lower()))) % len(self.alphabet)
            trans = self.alphabet[index]
            trans = trans if not is_upper else trans.upper()
        return trans
        
class VigenereCipher(Cipher):
    def _transpose_text(self, text, direction):
        key_index = 0
        transposed = []
        for i in range(len(text)):
            char = text[i]
            if char.lower() in self.alphabet:
                char = self.transpose(char, lambda n : n + direction * self.alphabet.index(key[key_index].lower()))
                key_index = (key_index + 1) % len(key)
            transposed.append(char)
        return ''.join(transposed)
        
    def encrypt(self, plaintext):
        return self._transpose_text(plaintext, 1)
        
    def decrypt(self, ciphertext):
        return self._transpose_text(ciphertext, -1)
        
class AffineCipher(Cipher):
    def __init__(self, key):
        self.scalar = key[0]
        factors = common_factors(scalar, len(self.alphabet))
        if len(factors) > 1:
            raise Exception("Invalid scalar value '%s', must be co-prime with alphabet length '%s'. Common factors: %s" % (scalar, len(self.alphabet), factors))
        self.increment = key[1]

    def encrypt(self, plaintext):
        return ''.join([self.transpose(c, lambda i : i * self.scalar + self.increment) for c in plaintext ])  
       
    def decrypt(self, ciphertext):
        modular_inverse = modinv(self.scalar, len(self.alphabet))
        return ''.join([self.transpose(c, lambda i : modular_inverse * (i - self.increment)) for c in ciphertext ])

plaintext = sys.argv[1].decode('utf8')
key = sys.argv[2]

cipher = VigenereCipher(key, SCANDIC_ALPHABET)
encrypted = cipher(plaintext)
print encrypted
print cipher.decrypt(encrypted)


