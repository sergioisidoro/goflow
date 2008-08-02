

def get_safe_builtins():
    '''returns a safe for eval local dict of functions from __builtins__
    and the math module. 
    '''
    safe_builtins=[
        'False', 'None', 'True', 'abs', 'all', 'any', 'apply', 'basestring',
        'bool', 'dict', 'enumerate', 'filter', 'float', 'frozenset', 'getattr', 'hasattr',
        'hash', 'int', 'iter', 'len', 'list', 'long', 'map', 'max','min', 'pow', 'range', 
        'reduce', 'repr', 'reversed', 'round', 'set','setattr', 'slice', 'sorted', 'str', 
        'sum', 'tuple', 'unicode', 'xrange', 'zip'
    ]
    import math
    _locals = {}
    for name in safe_builtins:
        _locals[name] = __builtins__.get(name)
    for name in [func for func in dir(math) if not func.startswith('_')]:
        _locals[name] = getattr(math, name)
    return _locals

_locals = get_safe_builtins()

def safe_eval(cond, **kwds):
    '''safe deferred evaluation of python expressions
    
       note: must be used in combination with safe_builtins
    '''
    globals = {"__builtins__": None}
    _locals.update(kwds)
    locals = _locals
    return lambda: eval(cond, globals, locals)

def get_obj(modpath, obj=None):
    '''dynamic module importer
    '''
    module = __import__(modpath, globals(), locals(), fromlist=['*'])
    if obj:
        return getattr(module, obj)
    else:
        return module

