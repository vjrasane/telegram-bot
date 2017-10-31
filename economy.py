from telegram.ext import CommandHandler
from enum import Enum
from validate import validate
from validate import not_empty, number, positive, expression, url, boolean, empty
from validate import shorter, any_of, flag, equals, enum
from parameters import Schema, param, arg, flag, pos_num_arg, parse_inputs
from convert import to_float, to_boolean, to_enum
from interval import Interval
from errors import CommandFailure
from utils import is_flag_set, image_msg, get_single

import schedule

OUTPUT_LIST_TOKEN = "* "

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
            CommandHandler("open_account", self._open_account, pass_args=True),
            CommandHandler("close_account", self._close_account, pass_args=True),
            CommandHandler("balance", self._balance, pass_args=True),
            CommandHandler("transfer", self._transfer, pass_args=True),
            CommandHandler("allowance", self._allowance, pass_args=True),
            CommandHandler("schedule_allowance", self._schedule_allowance, pass_args=True)
        ]
        # _schedule_allowances()
        
    # def _schedule_allowances(self):
        # currencies_group = self.database.group("economy").group("currencies")
        # for c in currencies_group.tables:
            # currency_group = currencies_group.group(c)
            # currency_info = currency_group.table("info")
            # allowance = currency_info.get("allowance", None)
            # period = currency_info.get("period", None)
    
    _create_currency_schema = Schema([
        pos_num_arg("initial", required=False),
        arg("sign", required=False, validators=[not_empty, shorter(15)], data=True),
        flag("override"),
        param("name", position=0, validators=[not_empty, shorter(25)], data=True)
    ])
    def _create_currency(self, bot, update, args):
        data, non_data = parse_inputs(args, self._create_currency_schema)
        permissions = _global_currency_permissions(["create"])
        
        self.require(required=permissions, user=update.message.from_user, password=non_data.get("master_password",None))

        currency_name = data["name"]
        currencies_group = self.database.group("economy").group("currencies")
        
        if currency_name in currencies_group.tables and not is_flag_set("override", non_data):
            raise CommandFailure("Currency '%s' already exists." % currency_name)
        
        currency_group = currencies_group.group(currency_name)
        currency_info_table = currency_group.table("info")
        currency_info_table.write(data)
        
        self.respond(bot, update, "Created new currency '%s'" % currency_name)
    
    _schedule_allowance_schema = Schema([
        param("currency", position=0, validators=[not_empty]),
        param("amount", position=1, validators=[number, positive], converter=to_float),
        arg("type", required=False, validators=[enum(Allowance)], converter=to_enum(Allowance))
        arg("every", positions=[-1, -2], arity=2, prefix="disallowed", 
            validators=[not_empty, any_of(enum(Weekday), sequence(all_of(number, positive), enum(TimeUnit)))]),
        arg("at", positions=[-2, -1], prefix="disallowed", required=False,
            validators=[time])
    ])
    def _schedule_allowance(self, bot, update, args):
        pass
    
    _allowance_schema = Schema([
        param("currency", position=0, validators=[not_empty]),
        param("amount", position=1, validators=[number, positive], converter=to_float),
        arg("type", required=False, validators=[enum(Allowance)], converter=to_enum(Allowance))
    ])
    def _allowance(self, bot, update, args):
        _, non_data = parse_inputs(args, self._allowance_schema)   
        currency_name = non_data["currency"]

        permissions = _currency_permissions(currency_name, ["manage"])
        self.require(required=permissions, user=update.message.from_user)
        
        amount = non_data["amount"]
        type = non_data.get("type", Allowance.normal)
        
        output = self._grant_allowance(currency_name, amount, type)
        self.respond(bot, update, "Granted allowance:\n%s%s" % (OUTPUT_LIST_TOKEN,output))
            
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
    
    _open_account_schema = Schema([
        param("currency", position=0, validators=[not_empty]),
        arg("user", validators=[not_empty], required=False)
    ])
    def _open_account(self, bot, update, args):
        _, non_data = parse_inputs(args, self._open_account_schema)
        currency_name = non_data["currency"]
        
        username = update.message.from_user.username
        if "user" in non_data:
            permissions = _currency_permissions(currency_name, ["manage"])
            self.require(required=permissions, user=update.message.from_user)
            username = non_data["user"]
            
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

    _close_account_schema = Schema([
        arg("user", required=False, validators=[not_empty]),
        param("currency", position=0, validators=[not_empty])
    ])
    def _close_account(self, bot, update, args):
        _, non_data = parse_inputs(args, self._close_account_schema)
        
        currency_name = non_data["currency"]
        permissions = _currency_permissions(currency_name, ["manage"])
        self.require(required=permissions, user=update.message.from_user)
        
        currencies_group = self.database.group("economy").group("currencies")
        if currency_name not in currencies_group.tables:
            raise CommandFailure("Currency '%s' does not exist." % currency_name)
            
        currency_group = currencies_group.group(currency_name)       
        currency_owners_group = currency_group.group("owners")
        
        username = non_data["user"] if "user" in non_data else update.message.from_user.username
        
        if username not in currency_owners_group.tables:
            raise CommandFailure("User %s does not have %s account." % (username, currency_name))
        
        currency_owners_group.drop(username)
        self.respond(bot, update, "Closed %s's %s account.%s" % (username, currency_name, image_msg("close_account", self.images)))
    
    _balance_schema = Schema([
        arg("user", required=False, validators=[not_empty]),
        param("currency", required=False, position=0, validators=[not_empty])
    ])
    def _balance(self, bot, update, args):
        _, non_data = parse_inputs(args, self._balance_schema)

        current_user = update.message.from_user
        target_username = non_data.get("user", current_user.username)
            
        currency_name = non_data.get("currency", None)
        balances = []
        if currency_name:
            balances = self._get_currency_balance(currency_name, target_username, current_user)
        else:
            balances = self._get_all_balances(target_username, current_user)
        
        if len(balances) > 0:
            balance_string = "\n".join([ OUTPUT_LIST_TOKEN + "%s %s" % (b, c) for c, b in balances.iteritems()])
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
                balance = user_owner_data.get("balance", 0)
                
                currency_data = currency_group.table("info").read()
                sign = currency_data.get("sign","").decode('utf-8')
                balances[c] = "%s%s" % (balance, sign)
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
        balance = user_owner_data.get("balance", 0)
        
        currency_data = currency_group.table("info").read()
        sign = currency_data.get("sign","").decode('utf-8')
        return { currency : "%s%s" % (balance, sign) }
        
    _transfer_schema = Schema([
        arg("to", prefix="disallowed", validators=[not_empty], position=-1),
        arg("from", prefix="disallowed", required=False, validators=[not_empty], position=-2),
        param("amount", position=0, validators=[number, positive], converter=to_float),
        param("currency", position=1, validators=[not_empty])
    ])
    def _transfer(self, bot, update, args):
        _, non_data = parse_inputs(args, self._transfer_schema)
        
        currency_name = non_data["currency"]
        amount = non_data["amount"]
        target_user = non_data["to"]
        
        source_user = update.message.from_user.username
        if non_data.get("from", source_user) != source_user:
            permissions = _currency_permissions(currency_name, ["manage"])
            self.require(required=permissions, user=update.message.from_user)
            source_user = non_data["from"]
        
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
