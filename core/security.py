import inspect
from pprint import pprint
from core.database import Database
from utils.errors import CommandFailure

class SecurityException(CommandFailure):
    pass

class UnauthorizedException(SecurityException):
    pass
    
def require_permissions(*permissions):
    def decorator(orig):
        def func(*args, **kwargs):
            print "Call to '%s' requiring permissions: %s" % (orig.__name__, list(permissions))
            if SecurityService.is_authorized(permissions):
                print "Access granted to '%s' for user '%s'" % (orig.__name__, SecurityService.instance().current_user.name)
                return orig(*args, **kwargs)
            print "Access denied to '%s' for user '%s'" % (orig.__name__, SecurityService.instance().current_user.name)
            raise UnauthorizedException("Unauthorized. Required permissions: %s" % list(permissions))
        return func
    return decorator

class Subject():
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
        self.current_channel = None
        self._init_database(database)
        #self.permissions = set()
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("channels", True)
        self.database.table("roles", True)
        
    def add_permissions(self, permissions):
        self.permissions.update(permissions)

    @staticmethod
    def is_authorized(permissions):
        inst = SecurityService.instance()
        return inst.current_channel.is_authorized(permissions) or inst.current_user.is_authorized(permissions)
        
    @staticmethod
    def current(message):
        inst = SecurityService.instance()
        inst.user(message.from_user)
        inst.channel(message.chat)
        
    def user(self, user):
        username = user.username
        db = self.database
        users = db['users'].data
        # Fetch user roles
        user_roles = []
        if username in users:  
            roles = db['roles'].data
            user_roles = [ Role(r, *roles[r]['permissions']) for r in users[username]['roles'] if r in roles ]
            
        self.current_user = Subject(username, *user_roles)
        print "Current user set '%s'" % username
        
    def channel(self, chat):
        db = self.database
        channels = db['channels'].data
        chat_id = str(chat.id)
        
        channel_roles = []
        if chat_id in channels:
            roles = db['roles'].data
            channel_roles = [ Role(r, *roles[r]['permissions']) for r in channels[chat_id]['roles'] if r in roles ]

        channel_name = chat.title or "<undefined>"
        self.current_channel = Subject(channel_name, *channel_roles)
        print "Current channel set '%s'" % channel_name
        
    @staticmethod
    def clear():
        inst = SecurityService.instance()
        inst.current_user = None
        inst.current_channel = None
        print "Current user/channel cleared" 
