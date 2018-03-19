

def load_words():
    words = []
    with open("words_alpha.txt", 'r') as words_file:
        words = words_file.read().splitlines()    
    return words
        
all_words = load_words()

starting_letter_frequency = [ 't','a','o','i','s','w','c','b','p','h','f','m','d','r','e','l','n','g','u','v','y','j','k','q','x','z' ]

word_length = 1
while True:
    words_of_length = [ w for w in all_words if len(w) == word_length ]
    if len(words_of_length) == 0:
        break
    
    with open("words_length_%s" % word_length, 'w') as word_length_file:    
        for letter in starting_letter_frequency:
            [ word_length_file.write("%s\n" % s) for s in [ w for w in words_of_length if w.startswith(letter) ] ]
    word_length += 1
