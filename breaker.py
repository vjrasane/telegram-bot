import os.path

class Breaker():
    def __init__(self, cipher, keygen, *analyzers):
        self.cipher = cipher
        self.keygen = keygen
        self.analyzers = analyzers
        
class KeyGenerator():
    key_length_order = [ i for i in range(3, 25) ] + [ 2, 1 ] 
    
    def __init__(self):
        self.key_length_state = 0
        
    @property
    def key_length(self):
        return self.key_length_order[self.key_length_state]
    
    @property
    def has_next(self):
        return True
    
    def __call__(self):
        return self.next()

    def next(self):
        return None
        
class BruteForceGenerator(KeyGenerator):
    pass
        
class DictionaryGenerator(KeyGenerator):
    key_length_order = [ i for i in range(3, 25) ] + [ 2, 1 ] 
    def __init__(self, dictionary):
        KeyGenerator.__init__(self)
        self.word_index = 0
        self.dictionary = dictionary
        self._load_words()
        
    @property
    def word_file(self):
        return "%s/words_length_%s.txt" % (self.dictionary, self.key_length)
        
    @property
    def has_next(self):
        if not os.path.isfile(self.word_file):
            return False
        if self.word_index >= len(self.words):
            return False
        return True

    def _load_words(self):
        with open(self.word_file, 'r') as word_file:
            self.words = word_file.read().splitlines()

    def _update_state(self):
        if self.word_index >= len(self.words) - 1:
            self.word_index = 0
            self.key_length_state += 1
            if os.path.isfile(self.word_file):
                self._load_words()
        else:
            self.word_index += 1
          
    def next(self):
        if self.has_next:
            word = self.words[self.word_index]
            self._update_state()
            return word
        return None
        
gen = DictionaryGenerator("crypto/dictionary")
while gen.key_length  < 4:
    gen.next()
    
print gen.key_length
print gen()
