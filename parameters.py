import shlex
from utils import lchop, add_to_list_map, CommandFailure
from validate import validate, is_number

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
            while (arg.arity == "N" or len(consumed) < arg.arity) and index + 1 < len(input):
                index += 1 
                consumed.append(input[index])
            return True, consumed, index
    return False, [], index

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
        
        is_argument, values, index = _get_argument(inputs, index, schema.arguments)
        if is_argument:
            if len(schema.arguments[input_word].positions) > 0:
                input_segments.append(ArgSeg(input_word, values))
            else:
                add_to_list_map(categorized, input_word, values)
        else:
            input_segments.append(Seg(input_word))
        index += 1
       
    _update_positions(input_segments)
    
    tmp = input_segments[:]
    print [ s.word for s in tmp]
    for seg in reversed(input_segments):
        if isinstance(seg, ArgSeg):
            positions = schema.arguments[seg.word].positions
            if not seg.pos in positions and not seg.rev in positions:
                print (seg.word, seg.pos, seg.rev, positions)
                tmp = tmp[:seg.pos] + seg.split() + tmp[seg.pos + 1:]
                _update_positions(tmp)
    
    for seg in tmp:
        if isinstance(seg, ArgSeg):
            add_to_list_map(categorized, seg.word, seg.values)
        else:
            is_parameter, key = _get_parameter(tmp, seg.pos, schema.parameters)
            if is_parameter:
                add_to_list_map(categorized, key, [seg.word])
            else:
                remainder.append(seg.word)
                
    return categorized, remainder


def _validate_inputs(inputs, remainder, schema):
    issues = []

    missing_req = []
    converted = {}
    
    for schema_input in schema.inputs:
        if schema_input.name in inputs:
            occurrences = inputs[schema_input.name]
            if len(occurrences) == 1:
                input_values = occurrences[0]
                
                for v in input_values:        
                    valid, reason = validate(v, schema_input.validators)
                    if not valid:
                        issues.append("Invalid '%s' value '%s': %s" % (schema_input.name, v, reason))
                    else:
                        add_to_list_map(converted, schema_input.name, schema_input.converter(v))
                        
                    missing_dep = []
                    for d in schema_input.depends:
                        if not d in inputs:
                            missing_dep.append(d)
                    if len(missing_dep) > 0:
                        issues.append("Parameter '%s' requires parameters: %s" % (schema_input.name, ", ".join(missing_dep)))
            else:
                issues.append("Parameter '%s' occurred %s times, but was expected once." % (schema_input.name, len(occurrences)))
        elif schema_input.required:
            missing_req.append(schema_input.name)
                
    if len(missing_req) > 0:
        issues.append("Missing required parameters: %s" % ", ".join(missing_req))

    if len(remainder) > 0:   
        issues.append("Unknown parameters: %s" % ", ".join(remainder))
    return converted, issues

class Schema():
    def __init__(self, inputs=[], name=None):
        self.name = name
        self.inputs = inputs
        self.parameters = { p.name: p for p in inputs if isinstance(p, Parameter) }
        self.arguments = { a.name: a for a in inputs if isinstance(a, Argument) }
    
def param(name, position, required=True, validators=[], converter=None):
    return Parameter(name, position, required, validators, converter)
    
def arg(name, positions=[], required=True, validators=[], converter=None, arity=1, prefix="allowed"):
    return Argument(name, positions, required, validators, converter, arity, prefix)

class Input(object):
    def __init__(self, name, required=True, validators=[], converter=None, depends=[]):
        self.name = name
        self.required = required
        self.validators = validators
        self.converter = converter if converter else lambda v: v
        self.depends = depends
        
class Parameter(Input):
    def __init__(self, name, position, required=True, validators=[], converter=None, depends=[]):
        super(Parameter, self).__init__(name, required, validators, converter, depends)
        self.position = position
        
class Argument(Input):
    def __init__(self, name, positions=[], required=True, validators=[], converter=None, arity=1, prefix="allowed", depends=[]):
        super(Argument, self).__init__(name, required, validators, converter, depends)
        self.arity = arity
        self.positions = positions
        self.prefix = prefix
        print self.depends
        
    def validate_prefix(self, is_prefix):
        if self.prefix == "required":
            return is_prefix
        elif self.prefix == "forbidden":
            return not is_prefix
        return self.prefix == "allowed"
        
schema = Schema([
    param("param", position=0),
    arg("arg", arity=2, positions=[1, -1]),
    param("p", position=2),
    ])
ISSUE_LIST_TOKEN = "* "
def parse_inputs(inputs, schema):
    inputs = _format_args(inputs)
    categorized, remainder = _categorize_inputs(inputs, schema)
    converted, issues = _validate_inputs(categorized, remainder, schema)
    
    if len(issues) > 0:
        raise CommandFailure("Incorrect usage:\n%s" % "\n".join([ ISSUE_LIST_TOKEN + i for i in issues ]))    
    
    return converted
