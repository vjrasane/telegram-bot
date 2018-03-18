from telegram.ext import CommandHandler
from enum import Enum
from pprint import pprint

from utils.validate import validate, val
from utils.validate import positive, no, get_variable
from utils.validate import shorter, any_of, flag, equals, enum, exists, at_most, get_value

from utils.errors import CommandFailure
from utils.utils import is_flag_set, image_msg, get_single
from utils.command_grammar import CommandGrammar
from utils.constants import USER_NAME_LIMIT
from utils.utils import replace_placeholders

from modules.economy.resources import CREATE_CURRENCY_RES, DELETE_CURRENCY_RES, MODIFY_CURRENCY_RES
from modules.economy.resources import OPEN_ACCOUNT_RES, BALANCE_RES

from modules.economy.resources import CURRENCIES_PATH, CURRENCY_OWNERS_PATH

from collections import Counter

import sys

OUTPUT_LIST_TOKEN = "* "

ECONOMY_GRAMMARS_DIR = "grammars/economy/"

CURRENCY_NAME_LIMIT = 30
CURRENCIES_PATH = [ "economy", "currencies" ]
CURRENCY_OWNERS_PATH = CURRENCIES_PATH + [ "{currency}", "owners" ]
CURRENCY_OWNER_VALIDATORS = [shorter(USER_NAME_LIMIT), exists(CURRENCY_OWNERS_PATH)]

CURRENCY_DATA_PATH = CURRENCY_OWNERS_PATH + [ "{user}" ]

GLOBAL_CURRENCY_PERMISSIONS = [ "admin", "currency" ]
CURRENCY_PERMISSION = "currency:{currency}"
CURRENCY_PERMISSIONS = GLOBAL_CURRENCY_PERMISSIONS + [ CURRENCY_PERMISSION ]
CURRENCY_OP_PERMISSIONS = CURRENCY_PERMISSIONS + [ CURRENCY_PERMISSION + ":<operation>" ]

class Allowance(Enum):
    normal = 0
    trickle = 1
    interest = 2

class Economy():
    def __init__(self, config, callbacks):
        self.database = config["database"]
        self.images = config["images"]
        self.respond = callbacks["respond"]
        self.require = callbacks["permissions"]
        self.handlers = [ 
            CommandHandler("create_currency", self._create_currency, pass_args=True),
            CommandHandler("delete_currency", self._delete_currency, pass_args=True),
            CommandHandler("update_currency", self._modify_currency, pass_args=True),
            
            CommandHandler("open_account", self._open_account, pass_args=True),
            CommandHandler("close_account", self._close_account, pass_args=True),
            CommandHandler("balance", self._balance, pass_args=True),
            CommandHandler("transfer", self._transfer, pass_args=True),
            CommandHandler("allowance", self._allowance, pass_args=True),
            CommandHandler("schedule_allowance", self._schedule_allowance, pass_args=True)
        ]
    
    def _create_currency(self, bot, update, args):
        params = CREATE_CURRENCY_RES.grammar.parse(args)
        self.require(required=CREATE_CURRENCY_RES.permissions, user=update.message.from_user)
        validate(params, CREATE_CURRENCY_RES.validators, self.database)
        
        self._write_currency_data(params)
        self.respond(bot, update, "Created new currency '%s'" % params["currency"])
        
    def _modify_currency(self, bot, update, args):
        params = MODIFY_CURRENCY_RES.grammar.parse(args)
        self.require(required=MODIFY_CURRENCY_RES.permissions, user=update.message.from_user)
        validate(params, MODIFY_CURRENCY_RES.validators, self.database)
        
        self._write_currency_data(params)
        self.respond(bot, update, "Updated currency '%s'" % params["currency"])
        
    def _write_currency_data(self, params):
        params["initial"] = params["initial"] if params["initial"] != None else 0.0
        params["sign"] = params["initial"] if params["initial"] != None else ""
        self.database.create(CURRENCIES_PATH + [ params["currency"], "info" ], params)

    def _delete_currency(self, bot, update, args):
        params = DELETE_CURRENCY_RES.grammar.parse(args)
        self.require(required=DELETE_CURRENCY_RES.permissions, user=update.message.from_user)
        validate(params, DELETE_CURRENCY_RES.validators, self.database)
        
        self.database.delete(CURRENCIES_PATH + [ params["currency"] ])
        self.respond(bot, update, "Deleted currency '%s'" % params["currency"])

    _schedule_allowance_usage = """
        /schedule_allowance <currency> <amount> every <interval> [-type <type>] 
    """
    _schedule_allowance_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "schedule_allowance", _schedule_allowance_usage)
    def _schedule_allowance(self, bot, update, args):
        self._schedule_allowance_grammar.parse(args)
    
    # _allowance_schema = Schema([
        # param("currency", position=0, validators=[not_empty]),
        # param("amount", position=1, validators=[number, positive], converter=to_float),
        # arg("type", required=False, validators=[enum(Allowance)], converter=to_enum(Allowance))
    # ])
    
    _allowance_usage = """
        /allowance <currency> <amount> [-type <type>]
    """
    _allowance_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "allowance", _allowance_usage)
    def _allowance(self, bot, update, args):
        self._allowance_grammar.parse(args)
        # _, non_data = parse_inputs(args, self._allowance_schema)   
        # currency_name = non_data["currency"]

        # permissions = _currency_permissions(currency_name, ["manage"])
        # self.require(required=permissions, user=update.message.from_user)
        
        # amount = non_data["amount"]
        # type = non_data.get("type", Allowance.normal)
        
        # output = self._grant_allowance(currency_name, amount, type)
        # self.respond(bot, update, "Granted allowance:\n%s%s" % (OUTPUT_LIST_TOKEN,output))
            
    def _grant_allowance(self, currency, amount, type=Allowance.normal): 
        currencies_group = self.database.group("economy").group("currencies")
        if currency not in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
    
        currency_group = currencies_group.group(currency)
        currency_owners_group = currency_group.group("owners")
        
        currency_table = currency_group.table("info")
        currency_data = currency_table.read()
        
        print_amount = str(amount)
        num_users = len(currency_owners_group.tables)
        if type == Allowance.trickle:
            sink = currency_data.get("sink", 0)
            total_amount = max(sink * ( amount / 100 ), 0)
            currency_data["sink"] = sink - total_amount
            currency_table.write(currency_data)
            amount = total_amount / num_users
            print_amount = str(amount)
        if type == Allowance.interest:
            print_amount += "% interest on"
        else:
            print_amount += currency_data.get("sign","").decode('utf-8')
        
        for owner in currency_owners_group.tables:
            owner_table = currency_owners_group.table(owner)
            owner_data = owner_table.read()
            balance = owner_data.get("balance", 0)
            amount = amount if type == Allowance.normal else balance * (amount / 100)
            owner_data["balance"] = balance + amount
            owner_table.write(owner_data)
        return "%s %s to %s users" % (print_amount, currency, num_users)
    
    # _open_account_schema = Schema([
        # param("currency", position=0, validators=[not_empty]),
        # arg("user", validators=[not_empty], required=False)
    # ])
    _open_account_usage = """
        /open_account <currency> [-user <user>]
    """
    _open_account_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "open_account", _open_account_usage)
    def _open_account(self, bot, update, args):
        params = OPEN_ACCOUNT_RES.grammar.parse(args)
        if params.get("user",None) == None:
            params["user"] = update.message.from_user.username
            self.require(required=OPEN_ACCOUNT_RES.permissions["common"], params=params, user=update.message.from_user)
        else:
            self.require(required=OPEN_ACCOUNT_RES.permissions["manage"], params=params, user=update.message.from_user)
        
        validate(params, OPEN_ACCOUNT_RES.validators, self.database)

        data = self.database.get_data(CURRENCIES_PATH + [params["currency"], "info"])
        balance = data.get("initial", 0.0) or 0.0
        sign = data.get("sign", "")
        
        user_owner_data = { "balance" : balance }
        self.database.create(replace_placeholders(CURRENCY_DATA_PATH, params), user_owner_data)
        self.respond(bot, update, "Created new %s account for user %s with balance: %s %s%s" % (params["currency"], params["user"], balance, sign.decode('utf-8'), image_msg("open_account", self.images)))

    # _close_account_schema = Schema([
        # arg("user", required=False, validators=[not_empty]),
        # param("currency", position=0, validators=[not_empty])
    # ])
    _close_account_usage = """
        /close_account <currency> [-user <user>]
    """
    _close_account_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "close_account", _close_account_usage)
    def _close_account(self, bot, update, args):
        self._close_account_grammar.parse(args)
        # _, non_data = parse_inputs(args, self._close_account_schema)
        
        # currency_name = non_data["currency"]
        # permissions = _currency_permissions(currency_name, ["manage"])
        # self.require(required=permissions, user=update.message.from_user)
        
        # currencies_group = self.database.group("economy").group("currencies")
        # if currency_name not in currencies_group.tables:
            # raise CommandFailure("Currency '%s' does not exist." % currency_name)
            
        # currency_group = currencies_group.group(currency_name)       
        # currency_owners_group = currency_group.group("owners")
        
        # username = non_data["user"] if "user" in non_data else update.message.from_user.username
        
        # if username not in currency_owners_group.tables:
            # raise CommandFailure("User %s does not have %s account." % (username, currency_name))
        
        # currency_owners_group.drop(username)
        self.respond(bot, update, "Closed %s's %s account.%s" % (username, currency_name, image_msg("close_account", self.images)))
    
    def _balance(self, bot, update, args):
        params = BALANCE_RES.grammar.parse(args)
        if params.get("user", None) == None:
            params["user"] = update.message.from_user.username
            if params.get("currency", None) != None:
                self.require(required=BALANCE_RES.permissions["common"], params=params, user=update.message.from_user)
        else:
            self.require(required=BALANCE_RES.permissions["manage"], params=params, user=update.message.from_user)
        
        
        
        validate(params, BALANCE_RES.validators, self.database)
        
        if params.get("currency", None) != None:
            balances = self._get_currency_balance(params["currency"], params["user"])
        else:
            balances = self._get_all_balances(params["user"])
        
        if len(balances) > 0:
            balance_string = "\n".join([ OUTPUT_LIST_TOKEN + "%s %s" % (b, c) for c, b in balances.iteritems()])
            self.respond(bot, update, "User %s's balances:\n%s" % (target_username, balance_string))
        else:
            self.respond(bot, update, "User %s does not have any open accounts." % target_username)
    
    def _get_all_balances(self, user):
        balances = {}
        currencies_group = self.database.group("economy").group("currencies")
        for name, group in currencies_group.tables.iteritems():
            balance = group.get_value(["owners", user], "balance")
            if balance != None:
                sign = group.get_value(["info"], "sign").decode('utf-8')
                balances[c] = "%s%s" % (balance, sign)
        return balances
    
    def _get_currency_balance(self, currency, user):
        balance = self.database.get_value(CURRENCIES_PATH + ["owners", user], "balance")
        sign = self.database.get_value(CURRENCIES_PATH + ["info"], "sign").decode('utf-8')
        return { currency : "%s%s" % (balance, sign) }
    
    _transfer_usage = """
        /transfer <amount> <currency> to <user> [from <user>]
    """
    _transfer_permissions = CURRENCY_PERMISSIONS + [ CURRENCY_PERMISSION + ":transfer" ]
    _transfer_validators = {
        "initial" : [
            val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), exists(CURRENCIES_PATH)]),
            val("target", depends=["currency"], funcs=CURRENCY_OWNER_VALIDATORS),
            val("source", depends=["currency"], funcs=CURRENCY_OWNER_VALIDATORS)
        ],
        "final" : [
            val("source", depends=["currency"], funcs=[no(equals(get_variable("target")))]),
            val("amount", depends=["currency", "source", "_current_user"], 
            funcs=[positive, at_most(sys.float_info.max), at_most(get_value(CURRENCY_OWNERS_PATH + ["{source}"], "balance"))])
        ]
    }
    _transfer_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "transfer", _transfer_usage)
    def _transfer(self, bot, update, args):
        params = self._transfer_grammar.parse(args)       
        
        validate(params, self._transfer_validators["initial"], self.database)
        # Override source if it wasn't defined
        if params.get("source", None) == None:
            params["source"] = update.message.from_user.username
        else:
            # If transfering from another user, require currency management permissions
            self.require(required=replace_placeholders(_transfer_permissions, params), user=update.message.from_user)
        
        # Handle final validation after we can be sure the source has been set
        validate(params, self._transfer_validators["final"], self.database)
        
        # _, non_data = parse_inputs(args, self._transfer_schema)
        
        # currency_name = non_data["currency"]
        # amount = non_data["amount"]
        # target_user = non_data["to"]
        
        # source_user = update.message.from_user.username
        # if non_data.get("from", source_user) != source_user:
            # permissions = _currency_permissions(currency_name, ["manage"])
            # self.require(required=permissions, user=update.message.from_user)
            # source_user = non_data["from"]
        
        # currencies_group = self.database.group("economy").group("currencies")
        # if not currency_name in currencies_group.tables:
            # raise CommandFailure("Currency '%s' does not exist." % currency_name)
        
        # currency_group = currencies_group.group(currency_name)
        # currency_owners_group = currency_group.group("owners")
        
        # if source_user not in currency_owners_group.tables:
            # raise CommandFailure("User %s does not have %s account." % (source_user, currency_name))
        # if target_user not in currency_owners_group.tables:
            # raise CommandFailure("User %s does not have %s account." % (target_user, currency_name))
            
        # source_table = currency_owners_group.table(source_user)
        # target_table = currency_owners_group.table(target_user)
        # source_data = source_table.read()
        # target_data = target_table.read()
        
        # balance = source_data.get("balance", 0)
        # if balance < amount:
            # raise CommandFailure("User %s has insufficient %s funds." % (source_user, currency_name))
        # source_data["balance"] = balance - amount
        # target_data["balance"] = target_data.get("balance",0) + amount
        # source_table.write(source_data)
        # target_table.write(target_data)
        
        # currency_info_table = currency_group.table("info")
        # currency_data = currency_info_table.read()
        # sign = currency_data.get("sign", "")
        
        # self.respond(bot, update, "%s%s %s transfered from %s to %s." % (amount, sign, currency_name, source_user, target_user))

        
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
