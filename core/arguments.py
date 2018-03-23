from utils.errors import CommandFailure
import textx as tx
import os

def syntax(filepath):
    def decorator(orig):
        def func(*args, **kwargs):    
            syn = CommandSyntax(filepath)
            
            # Its possible to check whether 'orig' is a method with inspect.ismethod(), 
            # but its unclear at this time whether non-method syntaxes are needed
            
            object = args[0] # The calling object
            arguments = args[1] # Command arguments are placed second
            
            parsed = syn.parse(arguments)
            return orig(object, parsed, **kwargs)
        return func
    return decorator

RESOURCE_DIR = "resources"
SYNTAX_DIRECTORY = "%s/syntax" % RESOURCE_DIR
USAGE_DIRECTORY = "%s/usage" % RESOURCE_DIR
    
SYNTAX_FILE_EXTENSION = ".tx"
USAGE_FILE_EXTENSION = ".usg"
class CommandSyntax():
    def __init__(self, file):
        syntax_filename = file if file.endswith(SYNTAX_FILE_EXTENSION) else file + SYNTAX_FILE_EXTENSION
        usage_filename = file if file.endswith(USAGE_FILE_EXTENSION) else file + USAGE_FILE_EXTENSION
        
        self.syntax_filepath = "%s/%s" % (SYNTAX_DIRECTORY, syntax_filename)
        
        self.usage = None
        usage_filepath = "%s/%s" % (USAGE_DIRECTORY, usage_filename)
        if os.path.exists(usage_filepath):
            with open(usage_filepath) as usage_file:
                self.usage = "\n%s" % usage_file.read()

        self.metamodel = tx.metamodel_from_file(self.syntax_filepath, auto_init_attributes=False)
        
    def parse(self, args):
        string = " ".join(args).encode('utf-8')
        try:
            model = self.metamodel.model_from_str(string)
            model_map = model.__dict__ if model else {}
            [ model_map.pop(k) for k in model_map.keys() if k.startswith("_tx_") ]
            return model_map
        except tx.TextXSyntaxError as e:
            raise CommandFailure("Syntax error! Usage: " + (self.usage or "<unavailable>"))
        except Exception as e:
            raise CommandFailure("Invalid input: " + str(e))
