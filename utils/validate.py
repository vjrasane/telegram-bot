import math
import validators
import re
import sys
from utils import parse_args, remove_indexes
from utils import lchop, rchop
from utils import replace_placeholders
from errors import CommandFailure

# ========= HELPERS =========

def _any_of(param, validators):
    reasons = []
    for v in validators:
        valid, reason = v(param)
        if valid:
            return True, None
        else:
            reasons.append(reason)
    return False, ", ".join(reasons)

def _shorter(param, length, validator=None):
    value = _get_callable_value(length, validator)
    if len(param) > value:
        return False, "Longer than limit (%s)" % value
    return True, []
    
def _enum(param, enum):
    try:
        _ = enum[param]
        return True, None
    except:
        return False, "Not a valid %s" % enum.__name__.lower()

def _get_callable_value(call, validator=None):
    if callable(call):
        return call(validator)
    return call
        
def _at_most(param, max_val, validator=None):
    value = _get_callable_value(max_val, validator)
    if param > value:
        return False, "'%s' exceeds maximum of %s" % (param, value)
    return True, None
        
def _get_value(path, field, validator):
    db_path = validator.replace_placeholders(path)
    return validator.database.get_value(db_path, field)
    
def _get_variable(var, validator):
    return validator.params.get(var, None)

def _equals(param, eq, validator=None):
    value = _get_callable_value(eq, validator)
    if param != value:
        return False, "'%s' does not equal '%s'" % (param, value)
    return True, "'%s' equals '%s'" % (param, value)
    
def _exists(path, param, validator):
    db_path  = validator.replace_placeholders(path)
    print (db_path, param)
    exists = validator.database.exists(db_path + [param])
    print exists
    if not exists:
        return False, "'%s' not found in database" % param
    return True, "'%s' exists in database" % param
    
def _not(tuple):
    return not tuple[0], tuple[1]
    
# ========= VALIDATORS =========

def no(func):
    return lambda p, v=None : _not(func(p,v))

def enum(e):
    return lambda p, v=None : _enum(p, e)

def equals(param):
    return lambda p, v=None : _equals(p, param, v)
    
def shorter(length):
    return lambda p, v=None : _shorter(p, length, v)
    
def any_of(*funcs):
    return lambda p, v=None : _any_of(p, v, list(funcs))
    
def under_max(param, validator=None):
    return at_most(sys.float_info.max)(param, validator)
    
def number(param, validator=None):
    if is_number(param):
        return True, None
    return False, "Not a number"

def positive(param, validator=None):
    if is_positive(param):
        return True, None
    return False, "Not a positive number."
    
def negative(param, validator=None):
    if not is_positive(param):
        return True, None
    return False, "Not a negative number."
    
def flag(param, validator=None):
    return any_of(is_empty, is_boolean)(param, validator)
    
def empty(param, validator=None):
    if is_empty(param):
        return True, "Empty value"
    return False, "Non-empty value"
    
def not_empty(param, validator=None):
    if not is_empty(param):
        return True, None
    return False, "Empty value"
    
def expression(param, validator=None):
    if is_expression(param):
        return True, None
    return False, "Not a valid expression"
    
def url(param, validator=None):
    if is_url(param):
        return True, None
    return False, "Not a URL"
    
def boolean(param, validator=None):
    if is_boolean(param):
        return True, "Boolean value"
    return False, "Not a boolean"
    
def at_most(max_val):
    return lambda p, v : _at_most(p, max_val, v)    

def exists(path):
    return lambda p, v : _exists(path, p, v)
    
# ========= RETRIEVERS =========

def get_value(path, field):
    return lambda v : _get_value(path, field, v)
    
def get_variable(var):
    return lambda v : _get_variable(var, v)
    
# ========= CHECKERS =========

def is_boolean(value):
    return value in [ "True", "False", "true", "false" ]

def is_number(value):
    try:
        f = float(value)
        if not math.isnan(f):
            return True
    except:
        pass
    return False
        
def is_positive(value):
    return float(value) > 0
        
def is_url(value):
    return validators.url(value)

def is_expression(value):
    # TODO
    return True, None
    
def is_empty(value):
    if value == None or len(value) == 0:
        return True
    return False

# ====== MAIN ======

def validate(params, validators, database=None):
    issues = {}
    success = []
    for v in validators:
        if len([d for d in v.depends if d not in success]) == 0:
            valid, reason = v.validate(params, database)
            if not valid:
                issues[v.variable] = reason
            else:
                success.append(v.variable)

    if len(issues) > 0:
        raise CommandFailure("Invalid usage:\n%s" % _format_issues(issues))    
   
def val(var, override=None, depends=None, funcs=None):
    return Validator(var, override, depends, list(funcs))
   
class Validator():
    def __init__(self, variable, override=None, depends=None, funcs=None):
        self.variable = variable
        self.funcs = funcs or []
        self.depends = depends or []
        self.override = override
        self.database = None
        self.params = {}
        
    def validate(self, params=None, database=None):
        self.params = params or {}
        self.database = database
        if params.get(self.variable, None) != None:
            param = params[self.variable]
            for f in self.funcs:
                valid, reason = f(param, self)
                if not valid:
                    return False, reason
        return True, None
        
    def replace_placeholders(self, strings):
        return replace_placeholders(strings, self.params)

# ======== PRIVATE ========

ISSUE_LIST_TOKEN = "* "
def _format_issues(issues):
    return "\n".join([ "%s%s: %s" % (ISSUE_LIST_TOKEN, v, i) for v,i in issues.iteritems() ])
