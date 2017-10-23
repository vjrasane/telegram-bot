import shlex
import string
import random
from validate import validate 
from errors import CommandFailure

current_milli_time = lambda : int(round(time.time() * 1000))
random_string = lambda N : ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def rchop(string, sub):
    return string[:-len(sub)] if string.endswith(sub) else string

def lchop(string, sub):
    return string[len(sub):] if string.startswith(sub) else string
    
def encode_list( u_list, encoding="utf-8" ):
    encoded = []
    for item in u_list:
        if isinstance(item, unicode):
            item = item.encode(encoding)
        elif isinstance(item, dict):
            item = encode_dict(item)
        elif isinstance(item, list):
            item = encode_list(item)
        encoded.append(item)
    return encoded

def encode_dict( u_dict, encoding="utf-8" ):
    encoded = {}
    for key,val in u_dict.iteritems():
        key = key.encode(encoding)
        if isinstance(val, unicode):
            val = val.encode(encoding)
        elif isinstance(val, list):
            val = encode_list(val, encoding)
        elif isinstance(val, dict):
            val = encode_dict(val, encoding)
        encoded[key] = val
    return encoded

ARGUMENT_PREFIX = "-"
ARGUMENT_EQUATOR = "="    
def parse_args(args):
    arg_str = " ".join(args).encode('utf-8')
    shell_args = shlex.split(arg_str)

    labeled = {}
    unlabeled = []
    for s in shell_args:
        if s.startswith(ARGUMENT_PREFIX):
            arg_split = s.split(ARGUMENT_EQUATOR)
            key = lchop(arg_split[0].strip(), ARGUMENT_PREFIX)
            if len(arg_split) == 2:
                labeled[key] = arg_split[1].strip()
            else:
                labeled[key] = None
        else:
            unlabeled.append(s)
    
    return labeled, unlabeled
    
def is_flag_set(flag, params):
    if not flag in params or params[flag] == False: # None is a 'falsy' value so we have to state this explicitly
        return False
    return True
    
def sort_unlabeled_params(params, required=[], optional=[]):
    sorted = {}
    index = 0
    missing_req = []
    for r in required:
        if len(params) <= index:
            missing_req.append(r)
        else:
            sorted[r] = params[index]
        index += 1
    if len(missing_req) > 0:
        raise CommandFailure("Missing parameter values: %s" % (", ".join(missing_req)))
        
    for o in optional:
        if len(params) > index:
            sorted[o] = params[index]
        index += 1
    return sorted
    
def sort_data_parames(params, schema):
    data = {}
    adds = {}
    for p in params:
        if schema[p].get("data", False):
            data[p] = params[p]
        else:
            adds[p] = params[p]
    return data, adds

def get_or_init(dict, key, init):
    if not key in dict:
        dict[key] = init
    return dict[key]
        
