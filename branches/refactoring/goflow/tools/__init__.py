import os, sys
from os.path import dirname, abspath

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



def djangopath(up=1, settings=None):
    '''easily sets the sys.path and django_settings

    :param up: how many directories up from current __file__ where the
               djangopath function is called.
    :type up: integer
    :param settings: <djangoapp>.settings
    :type: settings: string

    usage::

        djangopath(up=3, settings='demo.settings')

    '''
    # here's the magic
    path = abspath(sys._getframe(1).f_code.co_filename)
    for i in range(up):
        path = dirname(path)
    sys.path.insert(0, path)
    os.environ['DJANGO_SETTINGS_MODULE'] = settings


def admin_register(admin, namespace):
    '''convenience function to easily register admin classes
    
    :param admin: result of 'from django.contrib import admin'
    :param namespace: must take a locally called globals

    usage::
        
        # should be at the end of the file and globals 
        # must be called locally as below
        admin_register(admin, namespace=globals())
    
    '''
    for name, model_admin in namespace.copy().iteritems():
        if name.endswith("Admin"):
            model = namespace[name[:-5]]
            admin.site.register(model, model_admin)



