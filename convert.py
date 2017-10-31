# ========= HELPERS =========
def _to_boolean(value, default):
    if value == None or len(value) == 0:
        return default
    return value

def _to_enum(value, enum):
    return enum[value]
    
# ========= CONVERTERS =========
def to_enum(enum):
    return lambda v : _to_enum(v, enum)

def to_float(value):
    return float(value)
    
def to_boolean(default):
    return lambda v: _to_boolean(v, default)
    
