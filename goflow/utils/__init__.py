
def get_class(modpath, class_name=None):
    '''dynamic module importer
    '''
    module = __import__(modpath, globals(), locals(), fromlist=['*'])
    if class_name:
        return getattr(module, class_name)
    else:
        return module

