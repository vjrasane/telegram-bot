import random
from utils import lchop, rchop

phrases = [
    "<adjective:indef:capital> <noun> is <adjective:indef> <noun>",
    "<numeral:capital> <noun:plural> don't <object-verb> <noun:indef>",
    "The <adjective> <noun> gets the <noun>",
    "When the <noun> gets <adjective>, the <noun:plural> get going",
    "No <noun> is <noun:indef>",
    "<noun:capital> favors the <noun:plural>",
    "<noun:plural:capital> who live in glass <noun:plural> should not throw <noun:plural>",
    "A <noun> is worth a thousand <noun:plural>",
    "There's no such thing as <adjective:indef> <noun>",
    "There's no <noun> like <proper-noun>",
    "The <adjective> <noun> catches the <noun>",
    "Never look <noun:indef> in the <noun>",
    "You can't make <noun:indef> without <object-verb:ing> a few <noun:plural>",
    "<noun:capital> <object-verb:present> those who <object-verb> themselves",
    "You can't always <object-verb> what you <object-verb>",
    "<noun:plural:capital> speak louder than <noun:plural>",
    "If it ain't <adjective>, don't <object-verb> it"
]

words = {
    "numeral" : [ "two", "three", "ten", "thousand" ],
    "proper-noun" : [ "Rome", "Helsinki" ],
    "noun" : [ "home", "god", "place", "gift", "horse", "mouth","worm", "bird", "word","picture", "fortune", "master", "student", "wheel", "grease", "man", "island", "person", "house", "stone" ],
    "adjective" : [ "perfect", "true", "eternal", "squeaky", "tough", "free", "early", "broke" ],
    "verb" : [ "go", "do" ],
    "object-verb" : [ "help", "fuck", "kill", "make", "break", "fix", "want" ] 
}

exceptions = {
    "person" : { "plural" : "people" },
    "man" : { "plural": "men" },
    "go" : { "present": "goes" },
    "do" : { "present": "does" },
}

def present_verb(word):
    return word + "s"

def add_ing(word):
    return word + "ing"
    
a_sounds = [ "b","c","d","f","g","h","j","k","l","m","n","q","r","s","t","u","v","x","z","y" ]
an_sounds = [ "a","e","i","o" ]
def add_indef(word):
    a_prefixes = [ a for a in a_sounds if word.startswith(a) ]
    an_prefixes = [ an for an in an_sounds if word.startswith(an) ]
    if len(an_prefixes) < len(an_prefixes):
        return "an " + word
    return "a " + word
    
def pluralize(word):
    if word in exceptions and "plural" in exceptions[word]:
        return exceptions[word]["plural"]
    return word + "s"
    
modifiers = {
    "plural" : pluralize,
    "ing" : add_ing,
    "indef" : add_indef,
    "capital" : lambda w: w.capitalize(),
    "present" : present_verb
}

punctuation = [ '!', '?', '.', ',', ';', ':' ]

def is_placeholder(word):
    return word.startswith("<") # Won't check the end here because there could be punctuation
    
def strip_placeholder(word):
    placeholder = rchop(lchop(word, "<"), ">").split(":")
    return placeholder[0], placeholder[1:]

def construct_wisdom(phrase, words):
    constructed = []
    phrase_words = phrase.split(" ")
    for phrase_word in phrase_words:
        if is_placeholder(phrase_word):
            punct = ""
            char = phrase_word[-1]
            if char in punctuation:
                punct = char
                phrase_word = phrase_word[:-2]
            placeholder, mods = strip_placeholder(phrase_word)
            if not placeholder in words or len(words[placeholder]) == 0:
                raise Exception("No replacements for placeholder '%s' in phrase '%s'" % (placeholder, phrase))
            word = random.choice(words[placeholder])
            for m in mods:
                if not m in modifiers:
                    raise Exception("No modifier for '%s' found." % m)
                word = modifiers[m](word)
            constructed.append(word + punct)
        else:
            constructed.append(phrase_word)
    return " ".join(constructed)
    
MAX_RETRIES = 10
def get_wisdom():
    retries = 0
    tmp = phrases[:]
    while retries < MAX_RETRIES and len(tmp) > 0:
        phrase = random.choice(tmp)
        try:
            return construct_wisdom(phrase, words)  
        except Exception as e:
            print e
            pass
        tmp.remove(phrase)
        retries += 1
    raise Exception("Could not construct wisdom after %s retries." % retries)

print construct_wisdom(phrases[-1], words)

               

