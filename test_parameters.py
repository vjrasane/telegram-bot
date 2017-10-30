from utils import CommandFailure
from parameters import parse_inputs, Schema, param, arg

single_val_schema = Schema(
    [param("a", position=0)],
    name = "Single Variable Schema"
)
multi_val_schema = {
    "a" : { "required" : True, "position" : 0 },
    "b" : { "required" : True, "position" : 1 },
    "c" : { "position" : 2 }
}

single_key_schema = {
    "a" : { "type" : "keyword", "required" : True }
}
multi_key_schema = {
    "a" : { "type" : "keyword", "required" : True, "position" : 0 },
    "b" : { "type" : "keyword", "required" : True },
    "c" : { "type" : "keyword" }
}

single_var_schema = {
    "a" : { "type" : "variable", "required" : True }
}
multi_var_schema = {
    "a" : { "type" : "variable", "required" : True, "position" : 0 },
    "b" : { "type" : "variable", "required" : True },
    "c" : { "type" : "variable"}
}

current_schema=None
def test_parsing(args, expected={}, success=True):
    try:
        result = parse_inputs(args.split(" "), current_schema)
        if result != expected:
            raise Exception("Test '%s' with %s failed!\nGot: '%s' Expected: '%s'" % (args, current_schema.name, result, expected))
    except CommandFailure as e:
        if success:
            raise Exception("Test '%s' with %s failed!\n%s" % (args, current_schema.name,e))

basic_three_var_res = {'a': ['x'], 'b': ['y'], 'c':['z']}
repeat_three_var_res = {'a': ['x'], 'b': ['x'], 'c':['x']}
basic_two_var_res = {'a': ['x'], 'b': ['y']}

current_schema = single_val_schema
test_parsing("x", {'a': ['x']})
test_parsing("-a=x", {'a': ['-a=x']})

test_parsing("", success=False)
test_parsing("a x", success=False)

# current_schema = multi_val_schema
# test_parsing("x y z", basic_three_var_res)
# test_parsing("x x x", repeat_three_var_res)
# test_parsing("x y", basic_two_var_res)

# test_parsing("x", success=False)
# test_parsing("", success=False)

# current_schema = single_var_schema
# test_parsing("-a=x", {'a': ['x']})
# test_parsing("-a=", {'a': [None]})
# test_parsing("-a", {'a': [None]})

# test_parsing("-a=x -a=x", success=False)
# test_parsing("-", success=False)
# test_parsing("-b=x", success=False)
# test_parsing("-a = x", success=False)

# current_schema = multi_var_schema
# test_parsing("-a=x -b=y -c=z", basic_three_var_res)
# test_parsing("-a=x -c=z -b=y", basic_three_var_res)
# test_parsing("-a=x -c=x -b=x", repeat_three_var_res)
# test_parsing("-a=x -b=y", basic_two_var_res)

# test_parsing("-a=x -a=x -b=y -c=z", success=False)
# test_parsing("-b=y -a=x -c=z", success=False)
# test_parsing("-b=y -a=x", success=False)
# test_parsing("-b=y", success=False)
# test_parsing("", success=False)
# test_parsing("x", success=False)
# test_parsing("a x", success=False)

# current_schema = single_key_schema
# test_parsing("a x", {'a': ['x']})

# test_parsing("a x a x", success=False)
# test_parsing("a", success=False)
# test_parsing("b", success=False)
# test_parsing("", success=False)

# current_schema = multi_key_schema
# test_parsing("a x b y c z",  basic_three_var_res)
# test_parsing("a x b x c x", repeat_three_var_res)
# test_parsing("a x b y", basic_two_var_res)

# test_parsing("b y c z a x", success=False)
# test_parsing("b y a x", success=False)
# test_parsing("a x", success=False)
# test_parsing("", success=False)
# test_parsing("x", success=False)
# test_parsing("-a=x", success=False)



