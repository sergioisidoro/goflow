import logging
from django.conf import settings
from django.db.models import get_model

try:
    _file_log = settings.LOGGING_FILE
    _LOG_FILE_NOTSET = False
except AttributeError, e:
    _LOG_FILE_NOTSET = True
    _file_log = 'workflow.log'

if settings.DEBUG:
    level=logging.DEBUG
else:
    level=logging.INFO

log_format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
# log_format='%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s'

logging.basicConfig(
    filename=_file_log,
    level=level, 
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger('goflow.utils')
if _LOG_FILE_NOTSET:
     log.warning('settings.LOGGING_FILE not set; default is workflow.log')


class Log(object):
    def __init__(self, module):
        self.log = logging.getLogger(module)
        # self._event = get_model('instances', 'Event').objects

    def __getattr__(self, name):
        try:
            return getattr(self.log, name)
        except AttributeError, e:
            return getattr(self, name)

    def __call__(self, *args):
        if len(args) == 0: 
            return
        elif len(args) == 1:
            self.log.info(args[0] )
        else:
            self.log.info(" ".join([str(i) for i in args]))

    def event(self, msg, workitem):
        # self._event.create(name=msg, workitem=workitem)
        self.log.info('EVENT: [%s] %s' % (workitem, msg))

from django.contrib import admin

def register_admin(module_name, model_class_names):
    module = __import__(module_name, {}, {}, [''])
    for model_class_name in model_class_names:
        model = getattr(module, model_class_name)
        admin_class = getattr(module, model_class_name+'Admin', None)
        admin.site.register(model, admin_class)

