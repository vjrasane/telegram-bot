import inspect
from pprint import pprint
from core.database import Database
from utils.errors import CommandFailure

class SecurityException(CommandFailure):
    pass

class UnauthorizedException(SecurityException):
    pass

class User():
    def __init__(self, name, *roles):
        self.name = name
        self.roles = set(roles)
        
    def is_authorized(self, permissions):
        return next((r for r in self.roles if r.is_authorized(permissions)), None) != None
        
class Role():
    def __init__(self, name, *permissions):
        self.name = name
        self.permissions = set(permissions)
        
    def is_authorized(self, permissions):
        return next((p for p in self.permissions if p in permissions), None) != None
 
SECURITY = None     
class SecurityService():
    @staticmethod
    def instance():
        global SECURITY
        if SECURITY == None:
            SECURITY = SecurityService(Database.instance())
        return SECURITY
        
    def __init__(self, database):
        self.current_user = None
        self._init_database(database)
        #self.permissions = set()
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("roles", True)
        
    def add_permissions(self, permissions):
        self.permissions.update(permissions)

    @staticmethod
    def is_authorized(permissions):
        return SecurityService.instance().current_user.is_authorized(permissions)
        
    @staticmethod
    def user(user):
        username = user.username
        db = SecurityService.instance().database
        users = db['users'].data
        # Fetch user roles
        user_roles = []
        if username in users:  
            roles = db['roles'].data
            user_roles = [ Role(r, *roles[r]['permissions']) for r in users[username]['roles'] if r in roles ]
            
        SecurityService.instance().current_user = User(username, *user_roles)
        print "Current user set %s" % username
        
    @staticmethod
    def clear():
        SecurityService.instance().current_user = None
        print "Current user cleared"
        
def require_permissions(*permissions):
    def decorator(orig):
        print orig
        def func(*args, **kwargs):
            print "Call to '%s' requiring permissions: %s" % (orig.__name__, list(permissions))
            if SecurityService.is_authorized(permissions):
                print "Access granted to '%s' for user '%s'" % (orig.__name__, SecurityService.instance().current_user.name)
                return orig(*args, **kwargs)
            print "Access denied to '%s' for user '%s'" % (orig.__name__, SecurityService.instance().current_user.name)
            raise UnauthorizedException("Unauthorized. Required permissions: %s" % permissions)
        return func
    return decorator

    
