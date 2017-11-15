from textx.metamodel import metamodel_from_file
from pprint import pprint


hello_meta = metamodel_from_file('grammars/economy/transfer.tx')
example_hello_model = hello_meta.model_from_str('20 herp to asd')

pprint(example_hello_model.__dict__)
