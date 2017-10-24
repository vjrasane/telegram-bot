import math
import validators
from utils import parse_args, remove_indexes
from errors import CommandFailure

def equals(value):
    return lambda v : v == value

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
def validate_parameters(args, label_schema={}, unlabel_schema={}):
    labeled, unlabeled = parse_args(args)
    
    all_issues = []
    sorted, issues = _sort_unlabeled_params(unlabeled, unlabel_schema)
    all_issues += issues
    converted, issues = _validate_labeled_params(labeled, label_schema)
    all_issues += issues
    
    if len(all_issues) > 0:
        raise CommandFailure("Incorrect usage:\n%s" % "\n".join([ ISSUE_LIST_TOKEN + i for i in all_issues ]))    
        
    return dict(converted.items() + sorted.items())
    
def _find_flag_pos(params, flag, positions):
    if positions == None or len(positions) == 0:
        for i in range(len(params)):
            p = params[i]
            if p == flag:
                return i, i + 1 
    else:
        for p in positions:
            if len(params) > abs(p) and params[p] == flag:
                return p, p + 1
    return None, None
    
    
def _sort_unlabeled_params(params=[], schema={}):
    issues = []
    missing_req = []
    sorted = {}
    
    flags = { p:a for p,a in schema.iteritems() if a.get("flag", False) }
    others = { p:a for p,a in schema.iteritems() if p not in flags }
    
    handled = []
    for flag_param, attrs in flags.iteritems():
        pos =  attrs.get("position", None)  
        if pos != None and not isinstance(pos, list):
            pos = [ pos ]
        flag_pos, pos = _find_flag_pos(params, flag_param, pos)
        if flag_pos != None:
            handled.append(flag_pos)
        if pos == None or len(params) <= abs(pos):
            if attrs.get("required", False):
                missing_req.append(flag_param)
        else:
            value = params[pos]                      
            validators = attrs.get("validators", [])
            valid, reason = validate(value, validators)
            if not valid:
                issues.append("Invalid '%s' value '%s': %s" % (flag_param, value, reason))
            else:
                converter = attrs.get("converter", None)
                sorted[flag_param] = converter(value) if converter else value
            handled.append(pos)

    params = remove_indexes(params, handled)
    handled = []
    for other_param, attrs in others.iteritems():   
        pos =  attrs.get("position", None)  
        if pos == None or len(params) <= abs(pos):
            if attrs.get("required", False):
                missing_req.append(other_param)
        else:
            value = params[pos]                      
            validators = attrs.get("validators", [])
            valid, reason = validate(value, validators)
            if not valid:
                issues.append("Invalid '%s' value '%s': %s" % (other_param, value, reason))
            else:
                converter = attrs.get("converter", None)
                sorted[other_param] = converter(value) if converter else value
            handled.append(pos)

    params = remove_indexes(params, handled)
    if len(missing_req) > 0:
        issues.append("Missing required values: %s" % ", ".join(missing_req))
    
    if len(params) > 0:
        issues.append("Unexpected values: %s" % ", ".join(params))
    
    return sorted, issues
    
def _validate_labeled_params(params={}, schema={}):
    issues = []
    missing_req = []
    converted = {}
    for schema_param, attrs in schema.iteritems():
        if schema_param in params:
            validators = attrs.get("validators", [])
            valid, reason = validate(params[schema_param], validators)
            if not valid:
                issues.append("Invalid '%s' value '%s': %s" % (schema_param, params[schema_param], reason))
            else:
                converter = attrs.get("converter", None)
                converted[schema_param] = converter(params[schema_param]) if converter else params[schema_param]
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
    return converted, issues
    
    
