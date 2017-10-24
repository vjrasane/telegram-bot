from telegram.ext import CommandHandler
from validate import validate, validate_parameters
from validate import not_empty, is_number, is_positive, is_expression, is_url, is_boolean, is_empty
from validate import shorter, any_of, is_flag, equals
from convert import to_float, to_boolean

from errors import CommandFailure
from utils import sort_data_parames, parse_args, is_flag_set, sort_unlabeled_params, image_msg

BALANCE_LIST_TOKEN = "* "

class Economy():
    def __init__(self, config, callbacks):
        self.database = config["database"]
        self.images = config["images"]
        self.respond = callbacks["respond"]
        self.require = callbacks["permissions"]
        self.handlers = [ CommandHandler("create_currency", self._create_currency, pass_args=True),
            CommandHandler("open_account", self._open_account, pass_args=True),
            CommandHandler("close_account", self._close_account, pass_args=True),
            CommandHandler("balance", self._balance, pass_args=True),
            CommandHandler("transfer", self._transfer, pass_args=True)]
        
    _create_currency_label_params = {
        "initial" : { "validators" : [ is_number, is_positive ], "data" : True, "converter": to_float },
        "allowance" : { "depends" : [ "period" ], "validators" : [ is_number, is_positive ], "data" : True, "converter": to_float },
        "period" : { "depends" : [ "allowance" ], "validators" : [ is_expression ], "data" : True },
        "sign" : { "validators" : [ not_empty, shorter(15) ], "data" : True },
        "trickle" : { "validators" : [ is_flag ], "data" : True },
        "override" : { "validators" : [ is_flag ] }
    }
    _create_currency_unlabel_params = {
        "name" : { "position":0, "required" : True, "validators" : [ not_empty ], "data" : True }
    }
    def _create_currency(self, bot, update, args):
        params = validate_parameters(
            args, 
            label_schema=self._create_currency_label_params,
            unlabel_schema=self._create_currency_unlabel_params)
        permissions = _global_currency_permissions(["create"])
        
        self.require(required=permissions, user=update.message.from_user, password=params.get("master_password", None))
        
        currency_data, non_data = sort_data_parames(params=params, schema=self._create_currency_params)
        currency_name = currency_data["name"]
        currencies_group = self.database.group("economy").group("currencies")
        
        if currency_name in currencies_group.tables and not is_flag_set("override", non_data):
            raise CommandFailure("Currency '%s' already exists." % currency_name)
            
        currency_group = currencies_group.group(currency_name)
        currency_info_table = currency_group.table("info")
        currency_info_table.write(currency_data)
        
        self.respond(bot, update, "Created new currency '%s'" % currency_name)
        
    _open_account_label_params = {
        "user" : { "validators" : [ not_empty ] }
    }
    _open_account_unlabel_params = {
        "currency" : { "position" : 0, "required": True, "validators": [ not_empty ] }
    }
    def _open_account(self, bot, update, args):
        params = validate_parameters(
            args, 
            label_schema=self._open_account_label_params,
            unlabel_schema=self._open_account_unlabel_params) 

        currency_name = params["currency"]
        
        username = update.message.from_user.username
        if "user" in params:
            permissions = _currency_permissions(currency_name, ["manage"])
            self.require(required=permissions, user=update.message.from_user)
            username = params["user"]
            
        currencies_group = self.database.group("economy").group("currencies")
        
        if currency_name not in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
            
        currency_group = currencies_group.group(currency_name)
        currency_info_table = currency_group.table("info")
        currency_data = currency_info_table.read()
        
        currency_owners_group = currency_group.group("owners")
                
        if username in currency_owners_group.tables:
            raise CommandFailure("User %s already has %s account." % (username, currency_name))
            
        user_owner_table = currency_owners_group.table(username)
        balance = currency_data.get("initial", 0)
        sign = currency_data.get("sign", "")
        
        user_owner_data = { "balance" : balance }
        user_owner_table.write(user_owner_data)
        
        self.respond(bot, update, "Created new %s account for user %s with balance: %s %s%s" % (currency_name, username, balance, sign.decode('utf-8'), image_msg("open_account", self.images)))

    _close_account_label_params = {
        "user" : { "validators" : [ not_empty ] },
    }
    _close_account_unlabel_params = {
        "currency" : { "position":0, "validators" : [ not_empty ], "required" : True }
    }
    def _close_account(self, bot, update, args):
        params = validate_parameters(
            args, 
            label_schema=self._close_account_label_params,
            unlabel_schema=self._close_account_unlabel_params) 
        
        currency_name = params["currency"]
        permissions = _currency_permissions(currency_name, ["manage"])
        self.require(required=permissions, user=update.message.from_user)
        
        currencies_group = self.database.group("economy").group("currencies")
        if currency_name not in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
            
        currency_group = currencies_group.group(currency_name)       
        currency_owners_group = currency_group.group("owners")
        
        username = params["user"] if "user" in params else update.message.from_user.username
        
        if username not in currency_owners_group.tables:
            raise CommandFailure("User %s does not have %s account." % (username, currency_name))
        
        currency_owners_group.drop(username)
        self.respond(bot, update, "Closed %s's %s account.%s" % (username, currency_name, image_msg("close_account", self.images)))
    
    _balance_label_params = {
        "user" : { "validators" : [ not_empty ] }
    }
    _balance_unlabel_params = {
        "currency" : { "position":0, "validators" : [ not_empty ] }
    }
    def _balance(self, bot, update, args):
        params = validate_parameters(
            args, 
            label_schema=self._balance_label_params,
            unlabel_schema=self._balance_unlabel_params) 

        current_user = update.message.from_user
        target_username = current_user.username
        if "user" in params:
            target_username = params["user"]
            
        currency_name = params.get("currency", None)
        balances = []
        if currency_name:
            balances = self._get_currency_balance(currency_name, target_username, current_user)
        else:
            balances = self._get_all_balances(target_username, current_user)
        
        if len(balances) > 0:
            balance_string = "\n".join([ BALANCE_LIST_TOKEN + "%s %s" % (b, c) for c, b in balances.iteritems()])
            self.respond(bot, update, "User %s's balances:\n%s" % (target_username, balance_string))
        else:
            self.respond(bot, update, "User %s does not have any open accounts." % target_username)
    
    def _get_all_balances(self, target_username, current_user):
        if target_username != current_user.username:
            permissions = _global_currency_permissions(["manage", "inspect"])
            self.require(required=permissions, user=current_user)

        balances = {}
        currencies_group = self.database.group("economy").group("currencies")
        for c in currencies_group.tables:
            currency_group = currencies_group.group(c)
            currency_owners_group = currency_group.group("owners")
            if target_username in currency_owners_group.tables:
                user_owner_data = currency_owners_group.table(target_username).read()
                balances[c] = user_owner_data.get("balance", 0)
        return balances
    
    def _get_currency_balance(self, currency, target_username, current_user):
        if target_username != current_user.username:
            permissions = _currency_permissions(currency,["manage", "inspect"])
            self.require(required=permissions, user=current_user)

        currencies_group = self.database.group("economy").group("currencies")
        if not currency in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency)
        
        currency_group = currencies_group.group(currency)
        currency_owners_group = currency_group.group("owners")
        
        if not target_username in currency_owners_group.tables:
            raise CommandFailure("User %s does not have %s account." % (target_username, currency))
            
        user_owner_data = currency_owners_group.table(target_username).read()
        return { currency : user_owner_data.get("balance", 0) }
        
    _transfer_labeled_params = {
        "from" : { "validators" : [ not_empty ] }
    }
    _transfer_unlabeled_params = {
        "to" : { "position":-2,"required":True, "flag" : True, "validators":[ not_empty ]},
        "amount" : { "position":0, "required":True, "validators":[ is_number, is_positive ], "converter": to_float },
        "currency" : { "position":1, "required":True, "validators":[ not_empty ] }
    }
    def _transfer(self, bot, update, args):
        params = validate_parameters(
            args, 
            label_schema=self._transfer_labeled_params, 
            unlabel_schema=self._transfer_unlabeled_params)
        
        currency_name = params.get("currency", None)
        amount = params.get("amount", None)
        target_user = params.get("to", None)
        
        source_user = update.message.from_user.username
        if "from" in params and params["from"] != source_user:
            permissions = _currency_permissions(currency_name, ["manage"])
            self.require(required=permissions, user=update.message.from_user)
            source_user = params["from"]
        
        currencies_group = self.database.group("economy").group("currencies")
        if not currency_name in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
        
        currency_group = currencies_group.group(currency_name)
        currency_owners_group = currency_group.group("owners")
        
        if source_user not in currency_owners_group.tables:
            raise CommandFailure("User %s does not have %s account." % (source_user, currency_name))
        if target_user not in currency_owners_group.tables:
            raise CommandFailure("User %s does not have %s account." % (target_user, currency_name))
            
        source_table = currency_owners_group.table(source_user)
        target_table = currency_owners_group.table(target_user)
        source_data = source_table.read()
        target_data = target_table.read()
        
        balance = source_data.get("balance", 0)
        if balance < amount:
            raise CommandFailure("User %s has insufficient %s funds." % (source_user, currency_name))
        source_data["balance"] = balance - amount
        target_data["balance"] = target_data.get("balance",0) + amount
        source_table.write(source_data)
        target_table.write(target_data)
        
        currency_info_table = currency_group.table("info")
        currency_data = currency_info_table.read()
        sign = currency_data.get("sign", "")
        
        self.respond(bot, update, "%s%s %s transfered from %s to %s." % (amount, sign, currency_name, source_user, target_user))
        

def _global_currency_permissions(types):
    permissions = [ "admin", "currency" ]
    for t in types:
        permissions.append("currency:%s" % t)
    return permissions
    
def _currency_permissions(currency, types):
    permissions = [ "currency:%s" % currency ] + _global_currency_permissions(types)
    for t in types:
        permissions.append("currency:%s:%s" % (currency, t))
    return permissions
