from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from leave.admin import admin as leave_admin
from goflow.instances.admin import admin as instances_admin
from goflow.workflow.admin import admin as workflow_admin


from leave.forms import StartRequestForm, RequesterForm, CheckRequestForm

from os.path import join, dirname
_dir = join(dirname(__file__))

urlpatterns = patterns('',
    # FOR DEBUG AND TEST ONLY
    (r'^.*/accounts/login.*switch/(?P<username>.*)/(?P<password>.*)/$', 'goflow.workflow.views.debug_switch_user', {'redirect':'/leave/'}),
    (r'^.*/switch/(?P<username>.*)/(?P<password>.*)/$', 'goflow.workflow.views.debug_switch_user'),
    # user connection
    (r'^.*/logout/$', 'django.contrib.auth.views.logout'),
    (r'^.*/accounts/login/$', 'django.contrib.auth.views.login', {'template_name':'goflow/login.html'}),
    (r'^.*/password_change/$', 'django.contrib.auth.views.password_change'),
    
    # static
    (r'^images/(?P<path>.*)$', 'django.views.static.serve', {'document_root': join(_dir, 'media/img'), 'show_indexes': True}),
    (r'^files/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    
    # home redirection
    (r'^.*/home/$', 'django.views.generic.simple.redirect_to', {'url':'/leave/'}),
 
    # home page
    (r'^leave/$', 'django.views.generic.simple.direct_to_template', {'template':'leave.html'}),
    
    # starting application
    (r'^leave/start/$', 'goflow.workflow.applications.start_application', {'process_name':'leave',
                                                                           'form_class':StartRequestForm,
                                                                           'template':'start_leave.html'}),
    
    # applications
    (r'^leave/checkstatus/(?P<id>.*)/$', 'goflow.workflow.applications.edit_model', {'form_class':CheckRequestForm,
                                                                                     'template':'checkstatus.html'}),
    (r'^leave/checkstatus_auto/$', 'leavedemo.leave.views.checkstatus_auto', {'notif_user':True}),
    (r'^leave/refine/(?P<id>.*)/$', 'goflow.workflow.applications.edit_model', {'form_class':RequesterForm,
                                                                                'template':'refine.html'}),
    (r'^leave/approvalform/(?P<id>.*)/$', 'goflow.workflow.applications.edit_model', {'form_class':CheckRequestForm,
                                                                                      'template':'approval.html'}),
    (r'^leave/hrform/(?P<id>.*)/$', 'goflow.workflow.applications.view_application', {'template':'hrform.html'}),
    (r'^leave/hr_auto/$', 'leavedemo.leave.auto.update_hr'),
    (r'^leave/finalinfo/(?P<id>.*)/$', 'goflow.workflow.applications.view_application', {'template':'finalinfo.html'}),
    
     # administration
    (r'^leave/admin/workflow/', include('goflow.urls_admin')),
    (r'^leave/admin/graphics/', include('goflow.graphics.urls_admin')),
    (r'^leave/admin/(.*)', leave_admin.site.root),
    (r'^leave/admin/(.*)', instances_admin.site.root),
    (r'^leave/admin/(.*)', workflow_admin.site.root),
    
    # Goflow pages
    (r'^leave/', include('goflow.urls')),

    (r'^leave/send_mail/$', 'goflow.workflow.notification.send_mail'),
    
)
