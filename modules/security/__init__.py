
from core.security import require_permissions
from core.arguments import syntax

from core.database import Database
from core.telegram import TelegramService

def decorator(orig):
    print orig
    def wrapper():
        print "test decorator"
        return orig()
    return wrapper
    
    
class SecurityModule():
    def __init__(self):
        self._init_database(Database.instance())
        # print("Grant role: ", self._grant_role)
        print("Auhtorize: ", self._authorize)
        self.commands = {
            
            'authorize' : self._authorize,
            'grant_role' : self._grant_role,
            'test' : self._test
        }
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("roles", True)
        
    #@usage("security/grant_role")
   #@syntax("security/authorize")
    #@require_permissions("security.manage")
    def _authorize(self, bot, update, args):
        print "authorize"
        role, permissions = args['role'], args['permissions']
        print args
        
    #@validate("security/grant_role")
    
    #@usage("security/grant_role")
    #@syntax("security/grant_role")
    #@require_permissions("security.manage")
    def _grant_role(self, bot, update, args):
        print update
        print "grant role"
        # user, role = args['user'], args['role']
        # users = self.database['users']
        # users.data[user]['roles'].append(role)
        # users.save()
        
        # TelegramService.respond("Granted role '%s' to user '%s'" % (role, user))
    

        
    #@decorator    
    def _test(self, bot, update, args):
        print "test"
        
