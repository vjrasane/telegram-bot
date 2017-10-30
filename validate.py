import math
import validators
from utils import parse_args, remove_indexes
from errors import CommandFailure

# ========= HELPERS =========

def _any_of(value, validators):
    reasons = []
    for v in validators:
        valid, reason = v(value)
        if valid:
            return True, None
        else:
            reasons.append(reason)
    return False, ", ".join(reasons)

def _shorter(value, length):
    if len(value) > length:
        return False, "Longer than limit (%s)" % length
    return True, []  

# ========= VALIDATORS =========

def equals(value):
    return lambda v : v == value

def shorter(length):
    return lambda v : _shorter(v, length)
    
def any_of(*validators):
    return lambda v : _any_of(v, list(validators))
    
def number(value):
    if is_number(value):
        return True, None
    return False, "Not a number"

def positive(value):
    if is_positive(value):
        return True, None
    return False, "Not a positive number."
    
def negative(value):
    if not is_positive(value):
        return True, None
    return False, "Not a negative number."
    
def flag(value):
    return any_of(is_empty, is_boolean)(value)
    
def empty(value):
    if is_empty(value):
        return True, None
    return False, "Non-empty value"
    
def not_empty(value):
    if not is_empty(value):
        return True, None
    return False, "Empty value"
    
def expression(value):
    if is_expression(value):
        return True, None
    return False, "Not a valid expression"
    
def url(value):
    if is_url(value):
        return True, None
    return False, "Not a URL"
    
def boolean(value):
    if is_boolean(value):
        return True, None
    return False, "Not a boolean"
    
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
    
def validate(value, validators):
    for v in validators:
        valid, reason = v(value)
        if not valid:
            return False, reason
    return True, None

    
