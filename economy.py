from telegram.ext import CommandHandler
from validate import validate, validate_parameters
from validate import not_empty, is_number, is_positive, is_expression, is_url, is_boolean, is_empty
from validate import shorter, any_of, is_flag

from errors import CommandFailure
from utils import sort_data_parames, parse_args, is_flag_set, sort_unlabeled_params

class Economy():
    def __init__(self, config, callbacks):
        self.database = config["database"]
        self.respond = callbacks["respond"]
        self.require = callbacks["permissions"]
        self.handlers = [ CommandHandler("create_currency", self._create_currency, pass_args=True),
            CommandHandler("create_account", self._create_account, pass_args=True)]
        
    _create_currency_params = {
        "name" : { "required" : True, "validators" : [ not_empty ], "data" : True },
        "initial" : { "validators" : [ is_number, is_positive ], "data" : True },
        "allowance" : { "depends" : [ "period" ], "validators" : [ is_number, is_positive ], "data" : True },
        "period" : { "depends" : [ "allowance" ], "validators" : [ is_expression ], "data" : True },
        "sign" : { "validators" : [ not_empty, shorter(3) ], "data" : True },
        "trickle" : { "validators" : [ is_flag ], "data" : True },
        "override" : { "validators" : [ is_flag ] }
    }
    
    def _create_currency(self, bot, update, args):
        labeled, unlabeled = parse_args(args)
        permissions = [ "admin", "currency", "currency:create" ]
        
        self.require(required=permissions, user=update.message.from_user, password=labeled.get("master_password", None))
        validate_parameters(params=labeled, schema=self._create_currency_params)
        
        currency_data, params = sort_data_parames(params=labeled, schema=self._create_currency_params)
        currency_name = currency_data["name"]
        currencies_group = self.database.group("economy").group("currencies")
        
        if currency_name in currencies_group.tables and not is_flag_set("override", params):
            raise CommandFailure("Currency '%s' already exists." % currency_name)
            
        currency_group = currencies_group.group(currency_name)
        currency_info_table = currency_group.table("info")
        currency_info_table.write(currency_data)
        
        self.respond(bot, update, "Created new currency '%s'" % currency_name)
        
        
    def _create_account(self, bot, update, args):
        labeled, unlabeled = parse_args(args)
        validate_parameters(params=labeled, schema={}) # Check for unknown parameters
        
        sorted = sort_unlabeled_params(unlabeled, ["currency"])
        currency_name = sorted["currency"]
        currencies_group = self.database.group("economy").group("currencies")
        
        if currency_name not in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
            
        currency_group = currencies_group.group(currency_name)
        currency_info_table = currency_group.table("info")
        currency_data = currency_info_table.read()
        
        currency_owners_group = currency_group.group("owners")
        user = update.message.from_user
        
        if user.username in currency_owners_group.tables:
            raise CommandFailure("User %s already has %s account." % (user.username, currency_name))
            
        user_owner_table = currency_owners_group.table(user.username)
        user_owner_data = { "amount" : currency_data.get("initial", 0) }
        user_owner_table.write(user_owner_data)
        
        self.respond(bot, update, "Created new %s account" % currency_name)

        
        
