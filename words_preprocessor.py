
starting_letter_frequency = [ 't','a','o','i','s','w','c','b','p','h','f','m','d','r','e','l','n','g','u','v','y','j','k','q','x','z' ]
def load_words(filename):
    words = []
    with open(filename, 'r') as words_file:
        words = words_file.read().splitlines()    
    return words
        
dictionary_words = load_words("crypto/dictionary/words_alpha.txt")

word_length = 1
while True:
    words_of_length = [ w for w in dictionary_words if len(w) == word_length ]
    if len(words_of_length) == 0:
        break
    
    with open("crypto/dictionary/words_length_%s.txt" % word_length, 'w') as word_length_file:    
        for letter in starting_letter_frequency:
            [ word_length_file.write("%s\n" % s) for s in [ w for w in words_of_length if w.startswith(letter) ] ]
    word_length += 1

common_words = load_words("crypto/common/words_common.txt")
with open("crypto/common/words_common_filtered.txt", 'w') as filtered_word_file:    
    [ filtered_word_file.write("%s\n" % f) for f in common_words if len(f) > 2 ]
        

