import logging
from django.conf import settings

# log_format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
# logging.basicConfig( level=logging.DEBUG, format=log_format)
# _log = logging.getLogger('workflow.log')

try:
    _file_log = settings.LOGGING_FILE
    _LOG_FILE_NOTSET = False
except AttributeError, e:
    _LOG_FILE_NOTSET = True
    _file_log = 'workflow.log'
    
_hdlr = logging.FileHandler(_file_log)
# log_format = '%(asctime)s %(levelname)s %(message)s'
log_format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
_formatter = logging.Formatter()
_hdlr.setFormatter(_formatter)
logging.basicConfig(level=logging.DEBUG, format=log_format)
log = logging.getLogger('goflow')
log.addHandler(_hdlr)
if settings.DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

if _LOG_FILE_NOTSET:
     log.warning('settings.LOGGING_FILE not set; default is workflow.log')

def logmaker(kind, Class):
    def _func(msg, workitem):
        Class.objects.create(name=msg, workitem=workitem)
        import logging
        log = logging.getLogger('goflow')
        getattr(log, kind)(msg)
    return _func

# warn = logmaker('warn')
# error = logmaker('error')