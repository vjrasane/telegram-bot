
from core.security import require_permissions
from core.arguments import syntax

from core.database import Database
from core.telegram import TelegramService

from utils.errors import CommandFailure
    
class SecurityModule():
    def __init__(self):
        self._init_database(Database.instance())
        self.commands = {
            'authorize' : self._authorize,
            'create_role' : self._create_role,
            'deauthorize' : self._deauthorize,
            'roles' : self._roles,
            'grant' : self._grant,
            'revoke' : self._revoke,
        }
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("roles", True)
        
    #@usage("security/grant_role")
    @syntax("security/authorize")
    @require_permissions("security.manage")
    def _authorize(self, args):
        role, permissions = args['role'], args['permissions']
        roles = self.database['roles']
        
        if not role in roles.data:
            raise CommandFailure("No such role: '%s'" % role)
            
        roles.data[role]['permissions'] = list(set(permissions + roles.data[role]['permissions']))
        roles.save()
        
        TelegramService.respond("Auhtorized role '%s' with permissions: %s" % (role, permissions))
        
    @syntax("security/create_role")
    @require_permissions("security.manage")
    def _create_role(self, args):
        role, permissions = args['role'], args.get('permissions', [])
        roles = self.database['roles']
        
        if role in roles.data:
            raise CommandFailure("Role '%s' already exists" % role)
            
        roles.data[role] = { "permissions" : permissions }
        roles.save()
        
        TelegramService.respond("Created role '%s' with permissions: %s" % (role, permissions))
        
    @syntax("security/deauthorize")
    @require_permissions("security.manage")
    def _deauthorize(self, args):
        role, permissions = args['role'], args.get('permissions', [])
        roles = self.database['roles']
        
        if not role in roles.data:
            raise CommandFailure("No such role: '%s'" % role)
        
        remove = [ p for p in permissions if p in roles.data[role]['permissions'] ]
        if len(remove) > 0:
            roles.data[role]['permissions'] = [ p for p in roles.data[role]['permissions'] if not p in remove ] 
            roles.save()
            TelegramService.respond("Deauthorized role '%s' with permissions: %s" % (role, remove))
        else:
            TelegramService.respond("Role '%s' does not have any of permissions: %s" % (role, permissions))
        
    @syntax("security/roles")
    @require_permissions("security.manage", "security.view")
    def _roles(self, args):
        user = args.get('user', TelegramService.user().username)
        users = self.database['users']
        if not user in users.data or len(users.data[user]['roles']) == 0:
            TelegramService.respond("User '%s' has no assigned roles." % user)
        else:
            TelegramService.respond("User '%s' has roles: %s" % (user, users.data[user]['roles']))
        
    #@validate("security/grant_role")
    
    #@usage("security/grant_role")
    @syntax("security/grant")
    @require_permissions("security.manage")
    def _grant(self, args):
        user, role = args['user'], args['role']
        users = self.database['users']
        
        if not user in users.data:
            users.data[user] = { "roles" : [] }
        
        if role in users.data[user]['roles']:
            raise CommandFailure("User '%s' already has role '%s'" % (user, role))
            
        users.data[user]['roles'].append(role)
        users.save()
        
        TelegramService.respond("Granted role '%s' to user '%s'" % (role, user))
        
    @syntax("security/revoke")
    @require_permissions("security.manage")
    def _revoke(self, args):
        user, role = args['user'], args['role']
        users = self.database['users']
        
        if not user in users.data or not role in users.data[user]['roles']:
            raise CommandFailure("User '%s' does not have role '%s'" % (role, user))
            
        users.data[user]['roles'] = [ r for r in users.data[user]['roles'] if r != role ] 
        users.save()
        
        TelegramService.respond("Revoked role '%s' from user '%s'" % (role, user))

        
