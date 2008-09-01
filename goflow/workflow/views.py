#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.models import Group

from goflow.workflow.models import (Process, Activity, Transition, Application,
                                    DefaultAppModel, ProcessInstance, WorkItem)
from goflow.workflow.forms import ContentTypeForm
from goflow.tools.decorators import login_required


def index(request, template='workflow/index.html'):
    """workflow dashboard handler.

    template context contains following objects:
    user, processes, roles, obinstances.
    """
    me = request.user
    roles = Group.objects.all()
    processes = Process.objects.all()
    obinstances = DefaultAppModel.objects.all()

    return render_to_response(template, {'user':me,
                                         'processes':processes,
                                         'roles':roles,
                                         'obinstances':obinstances})


@login_required
def mywork(request, template='goflow/mywork.html'):
    me = request.user
    workitems = WorkItem.objects.get_all_by(user=me, notstatus='complete', noauto=True)
    return render_to_response(template, {'user':me, 'workitems':workitems})

@login_required
def otherswork(request, template='goflow/otherswork.html'):
    worker = request.GET['worker']
    workitems = WorkItem.objects.get_all_by(username=worker, notstatus='complete', noauto=False)
    return render_to_response(template, {'worker':worker, 'workitems':workitems})

@login_required
def instancehistory(request, template='goflow/instancehistory.html'):
    id = int(request.GET['id'])
    instance = ProcessInstance.objects.get(id=id)
    return render_to_response(template, {'instance':instance})

@login_required
def myrequests(request, template='goflow/myrequests.html'):
    instances = ProcessInstance.objects.filter(user=request.user)
    return render_to_response(template, {'user':request.user, 'instances':instances})

@login_required
def activate(request, id):
    workitem = WorkItem.objects.get_by(id=int(id), user=request.user)
    workitem.activate(request.user)
    return _app_response(workitem)

@login_required
def complete(request, id):
    workitem = WorkItem.objects.get_by(id=int(id), user=request.user)
    return _app_response(workitem)

def _app_response(workitem):
    activity = workitem.activity
    if not activity.process.enabled:
        return HttpResponse('process %s disabled.' % activity.process.title)

    if activity.kind == 'subprocess':
        sub_workitem = workitem.start_subprocess(workitem.user)
        return _app_response(sub_workitem)

    # no application: default_app
    if not activity.application:
        url = '../../../default_app'
        return HttpResponseRedirect('%s/%d/' % (url, workitem.id))

    if activity.kind == 'standard':
        # standard activity
        return HttpResponseRedirect(activity.application.get_app_url(workitem))
    
    # TODO: this is not a very informative error
    return HttpResponse('completion page.')


def debug_switch_user(request, username, password, redirect=None):
    """fast user switch for test purpose.

    see template tag switch_users.
    """
    logout(request)
    #return HttpResponseRedirect(redirect)
    if not redirect:
        redirect = request.META['HTTP_REFERER']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponseRedirect(redirect)
        else:
            return HttpResponse('user is not active')
    else:
        return HttpResponse('authentication failed')

def userlist(request, template):
    return HttpResponse('user page.')


def process_dot(request, id, template='goflow/process.dot'):
    """graphviz generator (**Work In Progress**).


    id process id
    template graphviz template

    context provides: process, roles, activities
    """
    process = Process.objects.get(id=int(id))
    context = {
               'process': process,
               'roles': ({'name':'role1', 'color':'red'},),
               'activities': Activity.objects.filter(process=process)
               }
    return render_to_response(template, context)

def cron(request=None):
    """(**Work In Progress**)
    """
    for t in Transition.objects.filter(condition__contains='workitem.timeout'):
        workitems = WorkItem.objects.filter(
            activity=t.input).exclude(status='complete')
        for wi in workitems:
            wi.forward_to_activities(with_timeout=True)

    if request:
        request.user.message_set.create(message="cron has run.")
        if request.META.has_key('HTTP_REFERER'):
            url = request.META['HTTP_REFERER']
        else:
            url = 'home/'
        return HttpResponseRedirect(url)


def app_env(request, action, id, template=None):
    """creates/removes unit test environment for applications.

    a process named "test_[app]" with one activity
    a group with appropriate permission
    """
    app = Application.objects.get(id=int(id))
    rep = 'Nothing done.'
    if action == 'create':
        app.create_test_env(user=request.user)
        rep = 'test env created for app %s' % app.url
    if action == 'remove':
        app.remove_test_env()
        rep = 'test env removed for app %s' % app.url

    rep += '<hr><p><b><a href=../../../>return</a></b>'
    return HttpResponse(rep)

def test_start(request, id, template='goflow/test_start.html'):
    """starts test instances.

    for a given application, with its unit test environment, the user
    choose a content-type then generates unit test process instances
    by cloning existing content-type objects (**Work In Progress**).
    """
    app = Application.objects.get(id=int(id))
    context = {}
    if request.method == 'POST':
        submit_value = request.POST['action']
        if submit_value == 'Create':
            ctype = ContentType.objects.get(id=int(request.POST['ctype']))
            model = ctype.model_class()
            for inst in model.objects.all():
                # just objects without link to a workflow instance
                if ProcessInstance.objects.filter(
                    content_type__pk=ctype.id,
                    object_id=inst.id
                ).count() > 0:
                    continue
                inst.id = None
                inst.save()
                # start the process
                ProcessInstance.objects.start(
                            process_name='test_%s' % app.url,
                            user=request.user, item=inst,
                            title="%s test instance for app %s" % (
                                ctype.name, app.url
                            ))
            request.user.message_set.create(message='test instances created')
        return HttpResponseRedirect('../..')
    form = ContentTypeForm()
    context['form'] = form
    return render_to_response(template, context)
