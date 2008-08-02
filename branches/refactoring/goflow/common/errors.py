from django.template import Template, Context

class Base(Exception): pass
class AuthenticationError(Base): pass
class SettingsError(Base): pass
class StatusError(Base): pass
class ProcessError(Base): pass
class AssignmentError(Base): pass

errors = {
    #code                   exception        error_msg    
    'authentication': (AuthenticationError, '{{user}} is not authorized'),
    'incorrect_process_instance_status': (NotImplementedError, 'process instance status:{{status}} not implemented'),
    'no_auto_user': (SettingsError, 'settings.WF_USER_AUTO (e.g auto) must be defined ',
                                    'for auto activities'),
    'process_disabled': (ProcessError, 'process {{workitem.activity.process.title}} is not enabled'),
    'invalid_user_for_workitem': (AssignmentError, '{{user.username}} cannot take {{workitem.id}}'),
    'incorrect_workitem_status': (StatusError, 'workitem {{workitem.id}} with status {{workitem.status}} '
                                               'does not have correct status'),
}


def error(code, error_msg=None, log=None, **kwds):
    error_class, _error_msg = errors[code]
    if error_msg:
        _error_msg = error_msg
    msg = Template(_error_msg).render(Context(kwds))
    if log:
        log.error(msg)
    return error_class(msg, "ERROR: "+code)

