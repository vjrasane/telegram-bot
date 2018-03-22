from utils.errors import CommandFailure
import textx as tx

SYNTAX_DIRECTORY = "syntax"
def syntax(filepath):
    def decorator(orig):
        def func(*args, **kwargs):    
            syn = CommandSyntax("%s/%s" % (SYNTAX_DIRECTORY, filepath))
            
            # Its possible to check whether 'orig' is a method with inspect.ismethod(), 
            # but its unclear at this time whether non-method syntaxes are needed
            
            object = args[0] # The calling object
            arguments = args[1] # Command arguments are placed second
            parsed = syn.parse(arguments)
            return orig(object, parsed, **kwargs)
        return func
    return decorator
            
GRAMMAR_FILE_EXTENSION = ".tx"
class CommandSyntax():
    def __init__(self, file, usage=None):
        self.usage = usage
        self.file = file if file.endswith(GRAMMAR_FILE_EXTENSION) else file + GRAMMAR_FILE_EXTENSION
        self.metamodel = tx.metamodel_from_file(self.file, auto_init_attributes=False)
        
    def parse(self, args):
        string = " ".join(args).encode('utf-8')
        try:
            model = self.metamodel.model_from_str(string)
            print "'%s'" % model
            model_map = model.__dict__ if model else {}
            [ model_map.pop(k) for k in model_map.keys() if k.startswith("_tx_") ]
            return model_map
        except tx.TextXSyntaxError as e:
            print e
            raise CommandFailure("Syntax error! Usage: " + (self.usage or "<unavailable>"))
        except Exception as e:
            raise CommandFailure("Invalid input: " + str(e))
