import textx as tx
from collections import Counter
from errors import CommandFailure

GRAMMAR_FILE_EXTENSION = ".tx"
class CommandGrammar():
    def __init__(self, file, usage):
        self.usage = usage
        self.file = file if file.endswith(GRAMMAR_FILE_EXTENSION) else file + GRAMMAR_FILE_EXTENSION
        self.metamodel = tx.metamodel_from_file(self.file, auto_init_attributes=False)
        
    def parse(self, args):
        string = " ".join(args).encode('utf-8')
        try:
            model = self.metamodel.model_from_str(string)
            model_map = model.__dict__ if isinstance(model, dict) else {}
            [ model_map.pop(k) for k in model_map.keys() if k.startswith("_tx_") ]
            return model_map
        except tx.TextXSyntaxError as e:
            raise CommandFailure("Syntax error! Usage: " + self.usage)
        except Exception as e:
            raise CommandFailure("Invalid input: " + str(e))
