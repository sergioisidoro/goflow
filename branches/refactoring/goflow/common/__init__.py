

def get_safe_builtins():
    '''returns a safe for eval local dict of functions from __builtins__
    and the math module.
    
    >>> sorted(get_safe_builtins().keys())
    ['False', 'None', 'True', 'abs', 'acos', 'all', 'any', 'apply', 'asin', 'atan', 
     'atan2', 'basestring', 'bool', 'ceil', 'cos', 'cosh', 'degrees', 'dict', 'e', 
     'enumerate', 'exp', 'fabs', 'filter', 'float', 'floor', 'fmod', 'frexp', 
     'frozenset', 'getattr', 'hasattr', 'hash', 'hypot', 'int', 'iter', 'ldexp', 
     'len', 'list', 'log', 'log10', 'long', 'map', 'max', 'min', 'modf', 'pi', 'pow', 
     'radians', 'range', 'reduce', 'repr', 'reversed', 'round', 'set', 'setattr', 
     'sin', 'sinh', 'slice', 'sorted', 'sqrt', 'str', 'sum', 'tan', 'tanh', 'tuple',
      'unicode', 'xrange', 'zip']

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
    
    (note: must be used in combination with safe_builtins)
       
    usage::
       
        >>> age = 10
        >>> safe_eval('age > 5', age=age)()
        True
    '''
    globals = {"__builtins__": None}
    _locals.update(kwds)
    locals = _locals
    return lambda: eval(cond, globals, locals)

def get_obj(modpath, obj=None):
    '''dynamic module/class/object importer
    
    usage::
    
        >>> join = get_obj('os.path', 'join')
        >>> join('a', 'b')
        'a/b'

    '''
    module = __import__(modpath, globals(), locals(), fromlist=['*'])
    if obj:
        return getattr(module, obj)
    else:
        return module

