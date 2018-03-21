from telegram.ext import CommandHandler
from core.security import require_permissions
from core.database import Database
#from core.arguments import parse_arguments

class SecurityModule():
    def __init__(self, callbacks):
        self._init_database(Database.instance())
        self.respond = callbacks["respond"]
        self.handlers = {
            CommandHandler("grant_role", self._grant_role, pass_args=True),
        }
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("roles", True)
        
    #@validate_arguments("security")
    #@parse_arguments("security")
    #@usage("security")
    @require_permissions("security.manage")
    def _grant_role(self, bot, update, args):
        # self.database['']
        pass