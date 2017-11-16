from textx.metamodel import metamodel_from_file
from textx.exceptions import TextXSyntaxError
from errors import CommandFailure

GRAMMAR_FILE_EXTENSION = ".tx"
class CommandGrammar():
    def __init__(self, file, usage):
        self.usage = usage
        self.file = file if file.endswith(GRAMMAR_FILE_EXTENSION) else file + GRAMMAR_FILE_EXTENSION
        self.metamodel = metamodel_from_file(self.file, auto_init_attributes=False)
        
    def parse(self, args):
        string = " ".join(args).encode('utf-8')
        try:
            return self.metamodel.model_from_str(string).__dict__
        except TextXSyntaxError as e:
            raise CommandFailure("Syntax error! Usage: " + self.usage)
