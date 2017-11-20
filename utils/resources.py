
class Resource():
    def __init__(self, validators, grammar, permissions=None):
        self.validators = validators
        self.grammar = grammar
        self.permissions = permissions or []
        
    