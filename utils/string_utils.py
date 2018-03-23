
def joinlines(list, prefix="", suffix=""):
    stringlines = [ "%s%s%s" % (prefix, s, suffix) for s in list ]
    return "\n".join(stringlines)