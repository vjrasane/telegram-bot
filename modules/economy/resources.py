from utils.resources import Resource

from utils.validate import validate, val
from utils.validate import no, get_variable, get_value
from utils.validate import positive, at_most, under_max
from utils.validate import shorter, any_of, flag, equals, enum, exists

from utils.constants import USER_NAME_LIMIT

from utils.command_grammar import CommandGrammar

# ======== CONSTANTS ========

CURRENCY_NAME_LIMIT = 30
CURRENCY_SIGN_LIMIT = 10

ECONOMY_GRAMMARS_DIR = "grammars/economy/"

CURRENCIES_PATH = [ "economy", "currencies" ]
CURRENCY_OWNERS_PATH = CURRENCIES_PATH + [ "{currency}", "owners" ]
CURRENCY_OWNER_VALIDATORS = [shorter(USER_NAME_LIMIT), exists(CURRENCY_OWNERS_PATH)]

CURRENCY_DATA_PATH = CURRENCY_OWNERS_PATH + [ "{user}" ]

GLOBAL_CURRENCY_PERMISSIONS = [ "admin", "currency" ]
CURRENCY_PERMISSION = "currency:{currency}"
CURRENCY_PERMISSIONS = GLOBAL_CURRENCY_PERMISSIONS + [ CURRENCY_PERMISSION ]
CURRENCY_OP_PERMISSIONS = CURRENCY_PERMISSIONS + [ CURRENCY_PERMISSION + ":<operation>" ]

# ===== CREATE CURRENCY =====

_create_currency_usage = """
        /create_currency <name> [-initial <amount>] [-sign <sign>]
    """
_create_currency_validators = [
    val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), no(exists(CURRENCIES_PATH))]),
    val("initial", funcs=[under_max, positive]),
    val("sign", funcs=[shorter(CURRENCY_SIGN_LIMIT)])
]
_create_currency_permissions = GLOBAL_CURRENCY_PERMISSIONS + [ "currency:create" ]
_create_currency_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "create_currency", _create_currency_usage)

CREATE_CURRENCY_RES = Resource(_create_currency_validators, _create_currency_grammar, _create_currency_permissions)

# ===== DELETE CURRENCY =====

_delete_currency_usage = """
        /delete_currency <name>
    """
_delete_currency_validators = [
    val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), exists(CURRENCIES_PATH)]),
]
_delete_currency_permissions = GLOBAL_CURRENCY_PERMISSIONS + [ "currency:delete" ]
_delete_currency_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "delete_currency", _create_currency_usage)

DELETE_CURRENCY_RES = Resource(_delete_currency_validators, _delete_currency_grammar, _delete_currency_permissions)

# ===== MODIFY CURRENCY =====

_modify_currency_usage = """
        /modify_currency <name> [-initial <amount>] [-sign <sign>]
    """
_modify_currency_validators = [
    val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), exists(CURRENCIES_PATH)]),
    val("initial", funcs=[under_max, positive]),
    val("sign", funcs=[shorter(CURRENCY_SIGN_LIMIT)])
]
_modify_currency_permissions = GLOBAL_CURRENCY_PERMISSIONS + [ "currency:modify" ]
_modify_currency_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "create_currency", _modify_currency_usage)

MODIFY_CURRENCY_RES = Resource(_modify_currency_validators, _modify_currency_grammar, _modify_currency_permissions)

# ====== OPEN ACCOUNT ======

_open_account_usage = """
    /open_account <currency> [-user <user>]
"""
_open_account_validators = [
    val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), exists(CURRENCIES_PATH)]),
    val("user", funcs=[shorter(USER_NAME_LIMIT), no(exists(CURRENCY_OWNERS_PATH))])
]
_open_account_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "open_account", _open_account_usage)
_open_account_permissions = {
    "common" : CURRENCY_PERMISSIONS + [ "currency:participate" ],
    "specific" : CURRENCY_PERMISSIONS + [ "currency:participate", CURRENCY_PERMISSION + ":participate" ],
    "manage" : CURRENCY_PERMISSIONS + [ "currency:manage", CURRENCY_PERMISSION + ":manage" ]
}
OPEN_ACCOUNT_RES = Resource(_open_account_validators, _open_account_grammar, _open_account_permissions)

# ====== BALANCE ======

_balance_usage = """
    /balance [<currency>] [-user <user>]
"""
_balance_grammar = CommandGrammar(ECONOMY_GRAMMARS_DIR + "balance", _balance_usage)
_balance_validators = [ 
    val("currency", funcs=[shorter(CURRENCY_NAME_LIMIT), exists(CURRENCIES_PATH)]),
    val("user", depends=["currency"], funcs=[shorter(USER_NAME_LIMIT), exists(CURRENCY_OWNERS_PATH)]) 
]
BALANCE_RES = Resource(_balance_validators, _balance_grammar, _open_account_permissions)

