import math
import validators
from errors import CommandFailure

def is_empty(value):
    valid, _ = not_empty(value)
    if not valid:
        return True, []
    return False, "Non-empty value"
    
def is_boolean(value):
    if value in [ "True", "False", "true", "false" ]:
        return True, []
    return False, "Not a boolean"

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
    
def shorter(length):
    return lambda v : _shorter(v, length)
    
def any_of(*validators):
    return lambda v : _any_of(v, list(validators))

def is_number(value):
    try:
        f = float(value)
        if not math.isnan(f):
            return True, None
    except:
        pass
    return False, "Not a number."
        
def is_positive(value):
    if float(value) > 0:
        return True, None
    else:
        return False, "Not a positive number."
        
def is_url(value):
    if validators.url(value):
        return True, None
    else:
        return False, "Not an URL."

def is_expression(value):
    # TODO
    return True, None
    
def is_flag(value):
    return any_of(is_empty, is_boolean)(value)
    
def not_empty(value):
    if value == None or len(value) == 0:
        return False, "Empty value"
    return True, None
    
def validate(value, validators):
    for v in validators:
        valid, reason = v(value)
        if not valid:
            return False, reason
    return True, None

ISSUE_LIST_TOKEN = "* "
def validate_parameters(params, schema):
    issues = []
    missing_req = []
    for schema_param, attrs in schema.iteritems():
        if schema_param in params:
            validators = attrs.get("validators", [])
            valid, reason = validate(params[schema_param], validators)
            if not valid:
                issues.append("Invalid '%s' value '%s': %s" % (schema_param, params[schema_param], reason))
            missing_dep = []
            for d in attrs.get("depends", []):
                if not d in params:
                    missing_dep.append(d)
            if len(missing_dep) > 0:
                issues.append("Parameter '%s' requires parameters: %s" % (schema_param, ", ".join(missing_dep)))
        elif attrs.get("required", False):
            missing_req.append(schema_param)
    if len(missing_req) > 0:
        issues.append("Missing required parameters: %s" % ", ".join(missing_req))
            
    unknown = []
    for p in params:
        if p not in schema:
            unknown.append(p)
    if len(unknown) > 0:   
        issues.append("Unknown parameters: %s" % ", ".join(unknown))
        
    if len(issues) > 0:
        raise CommandFailure("Incorrect usage:\n%s" % "\n".join([ ISSUE_LIST_TOKEN + i for i in issues ]))    
        