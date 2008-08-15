'''
meant to be linked to a django app as follows::

    (r'^leave/', include('goflow.urls')),

'''

from django.conf.urls.defaults import patterns
from instances.forms import DefaultAppStartForm


urlpatterns = patterns('django.contrib.auth.views.',
    (r'^.*/logout/$', 'logout'),
    (r'^.*/accounts/login/$', 'login', {'template_name':'goflow/login.html'}),
)

urlpatterns += patterns('goflow.workflow.views',
    (r'^$', 'index'),
    (r'^process/dot/(?P<id>.*)$','process_dot'),
    (r'^cron/$','cron'),
)

urlpatterns += patterns('goflow.workflow.applications',
    (r'^default_app/(?P<id>.*)/$', 'default_app'),
    (r'^start/(?P<app_label>.*)/(?P<model_name>.*)/$', 'start_application'),
    (r'^start_proto/(?P<process_name>.*)/$', 'start_application',
        {'form_class':DefaultAppStartForm, 'template':'goflow/start_proto.html'}),
)

urlpatterns += patterns('goflow.instances.views',
    (r'^otherswork/$',                 'otherswork'),
    (r'^otherswork/instancehistory/$', 'instancehistory'),
    (r'^myrequests/$',                 'myrequests'),
    (r'^myrequests/instancehistory/$', 'instancehistory'),
    (r'^mywork/$',                     'mywork'),
    (r'^mywork/activate/(?P<id>.*)/$', 'activate'),
    (r'^mywork/complete/(?P<id>.*)/$', 'complete'),
)

urlpatterns += patterns('goflow.graphics.views',
    (r'^graph/(?P<id>.*)/save/$', 'graph_save'),
    (r'^graph/(?P<id>.*)/$', 'graph'),
)

