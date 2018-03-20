import inspect
from pprint import pprint

class UnauthorizedException(Exception):
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
    def __init__(self):
        self.permissions = set()
        self.clear()
        
    def clear(self):
        self.current_user = None
        
    def add_permissions(self, permissions):
        self.permissions.update(permissions)
        
    def is_authorized(self, permissions):
        return self.current_user.is_authorized(permissions)
    
    @staticmethod
    def user(user):
        SecurityService.instance().current_user = user
    
    @staticmethod
    def instance():
        global SECURITY
        SECURITY = SecurityService() if not SECURITY else SECURITY
        return SECURITY
        
def require_permissions(*permissions):
    SecurityService.instance().add_permissions(permissions)
    
    def decorator(orig):
        def func(*args, **kwargs):
            if SecurityService.instance().is_authorized(permissions):
                return orig(*args, **kwargs)
            raise UnauthorizedException()
        return func
    return decorator

    
