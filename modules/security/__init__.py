from core.security import require_permissions
from core.arguments import parse_arguments

class SecurityModule():
    def __init__(self, config, callbacks):
        self.database = config["database"]
        self.respond = callbacks["respond"]
        self.handlers = {
            CommandHandler("grant_role", self._authorize, pass_args=True),
            CommandHandler("deauthorize", self._deauthorize, pass_args=True),
            CommandHandler("permissions", self._permissions, pass_args=True)
        }
        
        @validate_arguments("security")
        @parse_arguments("security")
        @usage("security")
        @require_permissions("security.manage")
        def grant_role(self, bot, update, args):
            self.database.get_data(["security", "users", args["user"]])