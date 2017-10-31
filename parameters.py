import shlex
from enum import Enum 
from utils import lchop, add_to_list_map, CommandFailure
from validate import validate, is_number, number, positive, boolean, not_empty
from convert import to_boolean, to_float

def _match_position(index, pos, length):
    return index == pos or index - length == pos
        
def _format_args(args):
    # args will be a list of strings split by spaces
    arg_str = " ".join(args).encode('utf-8')
    shell_args = shlex.split(arg_str)
    return shell_args

ARGUMENT_PREFIX = "-"
def remove_prefix(word):
    if word.startswith(ARGUMENT_PREFIX):
        chopped = lchop(word, ARGUMENT_PREFIX)
        if not is_number(chopped):
            return True, chopped
    return False, word
    
def _get_argument(input, index, schema_arguments):
    argument = input[index]
    is_prefix, argument = remove_prefix(argument)
    if argument in schema_arguments:
        arg = schema_arguments[argument]
        if arg.validate_prefix(is_prefix):
            consumed = []
            arity = arg.arity

            min_arity = arity[0]
            max_arity = arity[1]
            while ((not min_arity or len(consumed) < min_arity) and
                (not max_arity or len(consumed) < max_arity) and
                index + 1 < len(input)):
                index += 1 
                consumed.append(input[index])
                valid, _ = validate(" ".join(consumed), arg.validators)
                if valid:
                    break
            return True, argument, consumed, index
    return False, None, [], index

class Seg(object):
    def __init__(self, word):
        self.word = word
        self.pos = None

class ArgSeg(Seg):
    def __init__(self, word, values=[]):
        super(ArgSeg, self).__init__(word)
        self.values = values
        
    def split(self):
        return [ Seg(self.word) ] + [ Seg(v) for v in self.values ]

def _update_positions(segments):
    length = len(segments)
    for i in range(length):
        seg = segments[i]
        seg.pos = i
        seg.rev = i - length
        
def _get_parameter(segments, index, parameters):
    for name, param in parameters.iteritems():
        if _match_position(index, param.position, len(segments)):
            return True, name
    return False, None
      
def _categorize_inputs(inputs, schema):  
    categorized = {}
        
    remainder = []
    
    index = 0
    input_segments = []
    while len(inputs) > index:
        input_word = inputs[index]
        
        is_argument, arg, values, index = _get_argument(inputs, index, schema.arguments)
        if is_argument:
            if len(schema.arguments[arg].positions) > 0:
                input_segments.append(ArgSeg(arg, values))
            else:
                add_to_list_map(categorized, arg, " ".join(values))
        else:
            input_segments.append(Seg(input_word))
        index += 1
       
    _update_positions(input_segments)
    
    tmp = input_segments[:]
    for seg in reversed(input_segments):
        if isinstance(seg, ArgSeg):
            positions = schema.arguments[seg.word].positions
            if not seg.pos in positions and not seg.rev in positions:
                tmp = tmp[:seg.pos] + seg.split() + tmp[seg.pos + 1:]
                _update_positions(tmp)

    for seg in tmp:
        if isinstance(seg, ArgSeg):         
            add_to_list_map(categorized, seg.word, " ".join(seg.values))
        else:
            is_parameter, key = _get_parameter(tmp, seg.pos, schema.parameters)
            if is_parameter:
                add_to_list_map(categorized, key, seg.word)
            else:
                remainder.append(seg.word)
                
    return categorized, remainder

def _validate_inputs(inputs, remainder, schema):
    issues = []

    missing_req = []
    data = {}
    non_data = {}

    for schema_input in schema.inputs:
        map = data if schema_input.data else non_data
        if schema_input.name in inputs:
            occurrences = inputs[schema_input.name]

            if len(occurrences) == 1:
                input_value = occurrences[0]
                valid, reason = validate(input_value, schema_input.validators)
                if not valid:
                    issues.append("Invalid '%s' value '%s': %s" % (schema_input.name, input_value, reason))
                else:
                    map[schema_input.name] = schema_input.converter(input_value)
            else:
                issues.append("Parameter '%s' occurred %s times, but was expected once." % (schema_input.name, len(occurrences)))
            
            missing_dep = []
            for d in schema_input.depends:
                if not d in inputs:
                    missing_dep.append(d)
            if len(missing_dep) > 0:
                issues.append("Parameter '%s' requires parameters: %s" % (schema_input.name, ", ".join(missing_dep)))
        elif schema_input.required:
            missing_req.append(schema_input.usage_name())
                
    if len(missing_req) > 0:
        issues.append("Missing required parameters: %s" % ", ".join(missing_req))

    if len(remainder) > 0:   
        issues.append("Unknown parameters: %s" % ", ".join(remainder))
    return data, non_data, issues
    
def param(name, position, required=True, validators=None, converter=None, data=False, depends=None):
    return Parameter(name, position, required=required, validators=validators, converter=converter, data=data, depends=depends)
    
def arg(name, position=None, positions=None, required=True, validators=None, converter=None, arity=1, prefix=None, data=False, depends=None):
    pos = [position] if position else positions
    return Argument(name, positions=positions, required=required, validators=validators, converter=converter, arity=arity, prefix=prefix, data=data, depends=depends)

def flag(name, positions=None, data=False, prefix=None):
    return Argument(name, positions, required=False, validators=[flag], converter=to_boolean(True), prefix=prefix, data=data, arity=0)

def pos_num_arg(name, positions=None, required=True, depends=None):
    return Argument(name, positions, required, validators=[number, positive], data=True, converter=to_float, depends=depends)
    
class Input(object):
    def __init__(self, name, required=True, data=False, validators=None, converter=None, depends=None):
        self.name = name
        self.required = required
        self.validators = validators or []
        self.converter = converter if converter else lambda v: v
        self.depends = depends or []
        self.data = data
        
    def usage_name(self):
        return self.name
        
class Parameter(Input):
    def __init__(self, name, position, required=True, data=False, validators=None, converter=None, depends=None):
        super(Parameter, self).__init__(name, required=required, data=data, validators=validators, converter=converter, depends=depends)
        self.position = position

class ArgPrefix(Enum):
    allowed = 1
    disallowed = 2
    required = 3
        
class Argument(Input):
    def __init__(self, name, positions=None, required=True, data=False, validators=None, converter=None, arity=None, prefix=None, depends=None):
        super(Argument, self).__init__(name, required=required, data=data, validators=validators, converter=converter, depends=depends)
        self.arity = arity or (1,1)
        if not isinstance(self.arity, tuple):
            self.arity = (self.arity, self.arity)
        self.positions = positions or []
        self.prefix = ArgPrefix[prefix or "required"]
        
    def validate_prefix(self, is_prefix):
        if self.prefix == ArgPrefix.required:
            return is_prefix
        elif self.prefix == ArgPrefix.disallowed:
            return not is_prefix
        return self.prefix == ArgPrefix.allowed
        
    def usage_name(self):
        return ARGUMENT_PREFIX + self.name if self.prefix == ArgPrefix.required else self.name 
        
global_inputs = [ arg("master_password", required=False, validators=[not_empty] ) ]
class Schema():
    def __init__(self, inputs=None, name=None):
        self.name = name
        self.inputs = (inputs or []) + global_inputs
        self.parameters = { p.name: p for p in self.inputs if isinstance(p, Parameter) }
        self.arguments = { a.name: a for a in self.inputs if isinstance(a, Argument) }
    
ISSUE_LIST_TOKEN = "* "
def parse_inputs(inputs, schema):
    inputs = _format_args(inputs)
    categorized, remainder = _categorize_inputs(inputs, schema)
    data, non_data, issues = _validate_inputs(categorized, remainder, schema)
    
    if len(issues) > 0:
        raise CommandFailure("Incorrect usage:\n%s" % "\n".join([ ISSUE_LIST_TOKEN + i for i in issues ]))    
    
    return data, non_data
