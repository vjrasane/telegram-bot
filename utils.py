import shlex
import string
import random
import json
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

ARGUMENT_PREFIX = "!"
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
    
def sort_unlabeled_params(params, positional=[], required=[], optional=[]):
    sorted = {}
    index = 0
    missing_req = []
    
    removed = []
    for i in range(len(params)):
        p = params[i]
        if p in positional and len(params) > i + 1:
            sorted[p] = params[i + 1]
            removed += [ p, params[i + 1] ]
    params = [ p for p in params if p not in removed ]
            
    missing_req += [ p for p in positional if p not in sorted ]    
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
        
def read_json(file):
    with open(file) as f:
        return json.load(f, encoding='utf-8', object_hook=encode_dict)
        
def image_msg(command, images):
    if command in images:
        return "\n%s" % images[command]
    return ""

    
def remove_indexes(values, indexes):
    index_map = { i:values[i] for i in range(len(values)) }
    for i in indexes:
        abs_i = i
        if abs_i < 0:
            abs_i = len(values) + abs_i
        if abs_i in index_map:
            index_map.pop(abs_i)
    return [ v for _,v in index_map.iteritems() ]        
    
