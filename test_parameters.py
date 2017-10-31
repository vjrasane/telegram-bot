from utils import CommandFailure
from parameters import parse_inputs, Schema, param, arg

single_param_schema = Schema(
    [param("a", position=0)],
    name = "Single Variable Schema"
)
multi_param_schema = Schema([
    param("a", position=0),
    param("b", position=1),
    param("c", position=2, required=False)],
    name = "Single Parameter Schema"
)

single_arg_schema = Schema(
    [arg("a")],
    name = "Single Argument Schema"
)
multi_arg_schema = Schema(
    [arg("a", positions=[0]),
    arg("b", prefix="allowed", positions=[1]),
    arg("c", prefix="disallowed", required=False)],
    name = "Multi-Argument Schema"
)
interchange_arg_chema = Schema([
    arg("a", arity=(1, 2), positions=[0,1]),
    arg("b", arity=(1, 2), positions=[0,1])],
    name = "Interchange Argument Schema"
)
current_schema=None
def test_parsing(args, expected={}, success=True):
    try:
        data, non_data = parse_inputs(args.split(" "), current_schema)
        result = dict(data.items() + non_data.items())
        if result != expected:
            raise Exception("Test '%s' with %s failed!\nGot: '%s' Expected: '%s'" % (args, current_schema.name, result, expected))
    except CommandFailure as e:
        if success:
            raise Exception("Test '%s' with %s failed!\n%s" % (args, current_schema.name,e))

basic_three_res = {'a': 'x', 'b': 'y', 'c':'z'}
repeat_three_res = {'a': 'x', 'b': 'x', 'c':'x'}
basic_two_res = {'a': 'x', 'b': 'y'}

current_schema = interchange_arg_chema
test_parsing("-a C -b E", {'a':'C', 'b':'E'})
test_parsing("-b E -a C", {'a':'C', 'b':'E'})

current_schema = single_param_schema
test_parsing("x", {'a': 'x'})
test_parsing("-a=x", {'a': '-a=x'})

test_parsing("", success=False)
test_parsing("a x", success=False)
test_parsing("-a x", success=False)

current_schema = multi_param_schema
test_parsing("x y z", basic_three_res)
test_parsing("x x x", repeat_three_res)
test_parsing("x y", basic_two_res)

test_parsing("x", success=False)
test_parsing("", success=False)

current_schema = single_arg_schema
test_parsing("-a x", {'a': 'x'})
test_parsing("-a", {'a': ''})

test_parsing("a x", success=False)
test_parsing("a", success=False)
test_parsing("-a x -a x", success=False)
test_parsing("-", success=False)
test_parsing("-b x", success=False)
test_parsing("-a = x", success=False)
test_parsing("-a=x", success=False)

current_schema = multi_arg_schema
test_parsing("-a x -b y c z", basic_three_res)
test_parsing("-a x b y c z", basic_three_res)
test_parsing("-a x c z -b y", basic_three_res)
test_parsing("-a x c x -b x", repeat_three_res)
test_parsing("-a x -b y", basic_two_res)

test_parsing("a x -b y c z", success=False)
test_parsing("-a x -b y -c z", success=False)
test_parsing("-a x -a x -b y c z", success=False)
test_parsing("-b y -a x c z", success=False)
test_parsing("-b y -a x", success=False)
test_parsing("-b y", success=False)
test_parsing("", success=False)
test_parsing("x", success=False)
test_parsing("a x", success=False)
