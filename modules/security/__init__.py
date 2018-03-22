
from core.security import require_permissions
from core.arguments import syntax

from core.database import Database
from core.telegram import TelegramService

class SecurityModule():

    def __init__(self):
        self._init_database(Database.instance())
        self.commands = {
            "grant_role" : (self._grant_role, True)
        }
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("roles", True)
        
    #@validate("security/grant_role")
    @syntax("security/grant_role")
    #@usage("security/grant_role")
    @require_permissions("security.manage")
    def _grant_role(self, args):
        user, role = args['user'], args['role']
        users = self.database['users']

        
        TelegramService.respond("called grant role")