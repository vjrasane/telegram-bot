
from core.security import require_permissions
from core.arguments import syntax

from core.database import Database
from core.telegram import TelegramService

from utils.errors import CommandFailure

import utils.string_utils as string_utils
    
class SecurityModule():
    def __init__(self):
        self._init_database(Database.instance())
        self.commands = {
            'authorize' : self._authorize,
            'create_role' : self._create_role,
            'deauthorize' : self._deauthorize,
            'roles' : self._roles,
            'permissions' : self._permissions,
            'grant' : self._grant,
            'revoke' : self._revoke      
        }
        
    def _init_database(self, database):
        # Creates namespace and table files if they do not exist
        self.database = database.namespace("security", True)
        self.database.table("users", True)
        self.database.table("channels", True)
        self.database.table("roles", True)
        
    @require_permissions("security.manage")
    @syntax("security/authorize")
    def _authorize(self, args):
        role, permissions = args['role'], args['permissions']
        roles = self.database['roles']
        
        if not role in roles.data:
            raise CommandFailure("No such role: '%s'" % role)
            
        roles[role]['permissions'] = list(set(permissions + roles[role]['permissions']))
        roles.save()
        
        TelegramService.respond("Auhtorized role '%s' with permissions: %s" % (role, permissions))
    
    @require_permissions("security.manage")    
    @syntax("security/create_role")
    def _create_role(self, args):
        role, permissions = args['role'], args.get('permissions', [])
        roles = self.database['roles']
        
        if role in roles.data:
            raise CommandFailure("Role '%s' already exists" % role)
            
        roles[role] = { "permissions" : permissions }
        roles.save()
        
        TelegramService.respond("Created role '%s' with permissions: %s" % (role, permissions))
    
    @require_permissions("security.manage")    
    @syntax("security/deauthorize")
    def _deauthorize(self, args):
        role, permissions = args['role'], args.get('permissions', [])
        roles = self.database['roles']
        
        if not role in roles.data:
            raise CommandFailure("No such role: '%s'" % role)
        
        remove = [ p for p in permissions if p in roles[role]['permissions'] ]
        if len(remove) > 0:
            roles[role]['permissions'] = [ p for p in roles[role]['permissions'] if not p in remove ] 
            roles.save()
            TelegramService.respond("Deauthorized role '%s' with permissions: %s" % (role, remove))
        else:
            TelegramService.respond("Role '%s' does not have any of permissions: %s" % (role, permissions))
    
    @require_permissions("security.manage", "security.view")    
    @syntax("security/roles")
    def _roles(self, args):
        if not 'user' in args or args['user'] == None:
            user = TelegramService.current_user().username
        else:
            user = args['user']
        users = self.database['users']
        if not user in users.data or len(users[user]['roles']) == 0:
            TelegramService.respond("User '%s' has no assigned roles." % user)
        else:
            user_roles = users[user]['roles']
            response = "User '%s' has roles:\n%s" % (user, string_utils.joinlines(user_roles, prefix=" * "))
            if args.get('permissions', False):
                permissions = set([ p for r, v in self.database['roles'].data.iteritems() if r in user_roles for p in v['permissions'] ])
                response += "\nRole permissions:\n%s" % (string_utils.joinlines(permissions, prefix=" - "))
            TelegramService.respond(response)
        
    @require_permissions("security.manage")
    @syntax("security/grant")
    def _grant(self, args):
        role = args['role']
        
        subject_base = { "roles" : [] }
        if args.get('channel', False):
            chat = TelegramService.instance().chat
            if chat.type == 'private':
                raise CommandFailure("Cannot grant role to private chat")
                
            subject = str(chat.id)
            subject_name = chat.title
            subject_base['title'] = subject_name
        else:
            subject = subject_name = args['user']
        
        subject_term = 'channel' if args.get('channel', False) else 'user'
        subject_plural = subject_term + "s"
            
        subjects = self.database[subject_plural]
        if not subject in subjects.data:
            subjects[subject] = subject_base
        
        if role in subjects[subject]['roles']:
            raise CommandFailure("%s '%s' already has role '%s'" % (subject_term.capitalize(), subject_name, role))
        
        subjects[subject]['roles'].append(role)
        subjects.save()
        
        TelegramService.respond("Granted role '%s' to %s '%s'" % (role, subject_term, subject_name))
    
    @require_permissions("security.manage")    
    @syntax("security/revoke")
    def _revoke(self, args):
        user, role = args['user'], args['role']
        users = self.database['users']
        
        if not user in users.data or not role in users[user]['roles']:
            raise CommandFailure("User '%s' does not have role '%s'" % (user, role))
            
        users[user]['roles'] = [ r for r in users[user]['roles'] if r != role ] 
        users.save()
        
        TelegramService.respond("Revoked role '%s' from user '%s'" % (role, user))
    
    @require_permissions("security.manage", "security.view")
    @syntax("security/permissions")
    def _permissions(self, args):
        role = args['role']
        roles = self.database['roles']
        if not role in roles.data:
            raise CommandFailure("Role '%s' does not exist" % role)
        TelegramService.respond("Role '%s' permissions:\n%s" % (role, string_utils.joinlines([ p for p in roles[role]['permissions'] ], " - ")))
        
        