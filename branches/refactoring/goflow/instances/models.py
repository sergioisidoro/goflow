#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Group, User
from datetime import timedelta, datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from managers import ProcessInstanceManager, WorkItemManager

import logging; _log = logging.getLogger('workflow.log')

class ProcessInstance(models.Model):
    """ This is a process instance.
    
    A process instance is created when someone decides to do something,
    and doing this thing means start using a process defined in GoFlow.
    That's why it is called "process instance". The process is a class
    (=the definition of the process), and each time you want to
    "do what is defined in this process", that means you want to create
    an INSTANCE of this process.
    
    So from this point of view, an instance represents your dynamic
    part of a process. While the process definition contains the map
    of the workflow, the instance stores your usage, your history,
    your state of this process.
    
    The ProcessInstance will collect and handle workitems (see definition)
    to be passed from activity to activity in the process.
    
    Each instance can have more than one workitem depending on the
    number of split actions encountered in the process flow.
    That means that an instance is actually the collection of all of
    the instance "pieces" (workitems) that we get from splits of the
    same original process instance.
    
    Each ProcessInstance keeps track of its history through a graph.
    Each node of the graph represents an activity the instance has
    gone through (normal graph nodes) or an activity the instance is
    now pending on (a graph leaf node). Tracking the ProcessInstance history
    can be very useful for the ProcessInstance monitoring.
    
    When a process instance starts, the instance has to carry an
    implementation object that contains the application data. The
    specifications for the implementation class is:
    
    (nothing: now managed by generic relation)
    
    From the instance, the implementation object is reached as following:
      obj = instance.content_object (or instance.wfobject()).
    In a template, a field date1 will be displayed like this:
      {{ instance.wfobject.date1 }} or {{ instance.content_object.date1 }}
      
    From the object, instances may be reached with the reverse generic relation:
    the following can be added to the model:
    wfinstances = generic.GenericRelation(ProcessInstance)
  

    """
    STATUS_CHOICES = (
                      ('initiated', 'initiated'),
                      ('running', 'running'),
                      ('active', 'active'),
                      ('complete', 'complete'),
                      ('terminated', 'terminated'),
                      ('suspended', 'suspended'),
                      )
    title = models.CharField(max_length=100)
    process = models.ForeignKey('workflow.Process', related_name='instances', null=True, blank=True)
    creationTime = models.DateTimeField(auto_now_add=True, core=True)
    user = models.ForeignKey(User, related_name='instances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='initiated')
    old_status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    condition = models.CharField(max_length=50, null=True, blank=True)
    
    # refactoring
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    # add Manager
    objects = ProcessInstanceManager()
    #objects =
    # TODO: is this really required?
    def wfobject(self):
        return self.content_object
        
    def __str__(self):
        return self.title
    
    def __unicode__(self):
        return self.title
    
    def set_status(self, status):
        if not status in [x for x,y in ProcessInstance.STATUS_CHOICES]:
            raise Exception('instance status incorrect :%s' % status)
        self.old_status = self.status
        self.status = status
        self.save()
    
    class Admin:
        date_hierarchy = 'creationTime'
        list_display = ('title', 'process', 'user', 'creationTime', 'status')
        list_filter = ('process', 'user')

class WorkItem(models.Model):
    """A workitem object represents an activity you are performing.
    
    An Activity object defines the activity, while the workitem object
    represents that you are performing this activity. So workitem is
    an "instance" of the activity.
    """
    STATUS_CHOICES = (
                      ('blocked', 'blocked'),
                      ('inactive', 'inactive'),
                      ('active', 'active'),
                      ('suspended', 'suspended'),
                      ('fallout', 'fallout'),
                      ('complete', 'complete'),
                      )
    date = models.DateTimeField(auto_now=True, core=True)
    user = models.ForeignKey(User, related_name='workitems', null=True, blank=True)
    instance = models.ForeignKey(ProcessInstance, related_name='workitems')
    activity = models.ForeignKey('workflow.Activity', related_name='workitems')
    workitem_from = models.ForeignKey('self', related_name='workitems_to', null=True, blank=True)
    push_roles = models.ManyToManyField(Group, related_name='push_workitems', null=True, blank=True)
    pull_roles = models.ManyToManyField(Group, related_name='pull_workitems', null=True, blank=True)
    blocked = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')

    # set to the new WorkItemManager
    objects = WorkItemManager()

    def forward(self, timeout_forwarding=False, subflow_workitem=None):
        '''
        Forward this workitem to all valid destination activities.
        
        @type timeoutForwarding: bool
        @param timeoutForwarding: ??
        @type: subflow_workitem: WorkItem
        @param subflow_workitem: a workitem associated with a subflow ??
        
        '''
        _log.info('forward_workitem %s', str(self))
        if not timeout_forwarding:
            if self.status != 'complete':
                return
        if self.has_workitems_to() and not subflow_workitem:
            _log.debug('forward_workitem canceled for %s: ' 
                       'workitem.has_workitem_to()', str(self))
            return
        
        if timeout_forwarding:
            _log.info('timeout forwarding')
            Event.objects.create(name='timeout', workitem=self)
        
        for destination in self.get_destinations(timeout_forwarding):
            self._forward_self_to_activity(destination)


    def get_destinations(self, timeout_forwarding=False):
        '''
        Return list of destination activities that meet the conditions of each transition
        
        @type timeout_forwarding: bool
        @param timeout_forwarding: a workitem with a time-delay??
        @rtype: [Activity]
        @return: list of destination activities.
        '''
        activity = self.activity
        transitions = models.get_model('workflow', 'Transition').objects.filter(input=activity)
        if timeout_forwarding:
            transitions = transitions.filter(condition__contains='workitem.time_out')
        destinations = []
        for transition in transitions:
            if self.eval_transition_condition(transition):
                destinations.append(transition.output)
        return destinations

    def _forward_self_to_activity(self, target_activity):
        '''
        Passes the process instance embedded in this workitem 
        to a new workitem that is associated with the destination activity.
        
        @type target_activity: Activity
        @param target_activity: the activity instance to this workitem 
                                should be forwarded
        @rtype: WorkItem
        @return: a workitem that has been passed on to the next 
                 activity (and next user)
        '''
        instance = self.instance
        wi = WorkItem.objects.create(instance=instance, user=None, activity=target_activity)
        _log.info('forwarded to %s', target_activity.title)
        Event.objects.create(name='creation by %s' % self.user.username, workitem=wi)
        Event.objects.create(name='forwarded to %s' % target_activity.title, workitem=self)
        wi.workitem_from = self
        if target_activity.autostart:
            _log.info('run auto activity %s workitem %s', target_activity.title, str(wi))
            try:
                auto_user = User.objects.get(username=settings.WF_USER_AUTO)
            except Exception:
                error = 'a user named %s (settings.WF_USER_AUTO) must be defined for auto activities'
                raise Exception(error % settings.WF_USER_AUTO)
            wi.activate(actor=auto_user)
            #if exec_auto_application(wi):
            if wi.exec_auto_application():
                wi.complete(actor=auto_user)
                #complete_workitem(wi, actor=auto_user)
            return wi
        
        if target_activity.push_application:
            target_user = wi.exec_push_application()
            _log.info('application pushed to user %s', target_user.username)
            wi.user = target_user
            wi.save()
            Event.objects.create(name='assigned to %s' % target_user.username, workitem=wi)
            notify_if_needed(user=target_user)
        else:
            wi.pull_roles = wi.activity.roles.all()
            wi.save()
            notify_if_needed(roles=wi.pull_roles)
        return wi

    def exec_push_application(self):
        '''
        Execute push application for this workitem
        '''
        if not self.activity.process.enabled:
            raise Exception('process %s disabled.' % self.activity.process.title)
        appname = self.activity.push_application.url
        params = self.activity.pushapp_param
        # try std pushapps:
        from goflow.workflow import pushapps
        if appname in dir(pushapps):
            print 'appname', appname
            try:
                kwargs = ''
                if params:
                    kwargs = ',**%s' % params
                result = eval('pushapps.%s(workitem%s)' % (appname, kwargs))
            except Exception, v:
                _log.error('exec_push_application %s', v)
                result = None
                self.fallout()
            return result
        
        try:
            prefix = settings.WF_PUSH_APPS_PREFIX
            # dyn import
            exec 'import %s' % prefix
            
            appname = '%s.%s' % (prefix, appname)
            result = eval('%s(workitem)' % appname)
        except Exception, v:
            _log.error('exec_push_application %s', v)
            result = None
            self.fallout()
        return result

    def activate(self, actor):
        '''
        changes this workitem's status to 'active' and logs event & activator
        '''
        
        self._check_all_for(actor, status=('inactive', 'active'))
        if self.status == 'active':
            _log.warning('activate_workitem actor %s workitem %s already active', 
                actor.username, str(self))
            return
        self.status = 'active'
        self.user = actor
        self.save()
        _log.info('activate_workitem actor %s workitem %s', 
            actor.username, str(self))
        Event.objects.create(name='activated by %s' % actor.username, workitem=self)


    def complete(self, actor):
        '''
        changes status of this workitem to 'complete' and logs event & activator
        '''
        self._check_all_for(actor, status='active')
        self.status = 'complete'
        self.user = actor
        self.save()
        _log.info('complete_workitem actor %s workitem %s', actor.username, str(self))
        Event.objects.create(name='completed by %s' % actor.username, workitem=self)
        
        if self.activity.autofinish:
            _log.debug('activity autofinish: forward')
            self.forward()
        
        # if end activity, instance is complete
        if self.instance.process.end == self.activity:
            _log.info('activity end process %s' % self.instance.process.title)
            # first test subflow
            lwi = WorkItem.objects.filter(activity__subflow=self.instance.process,
                                          status='blocked',
                                          instance=self.instance)
            if lwi.count() > 0:
                _log.info('parent process for subflow %s' % self.instance.process.title)
                workitem0 = lwi[0]
                workitem0.instance.process = workitem0.activity.process
                workitem0.instance.save()
                _log.info('process change for instance %s' % workitem0.instance.title)
                workitem0.status = 'complete'
                workitem0.save()
                workitem0.forward(subflow_workitem=self)
            else:
                self.instance.set_status('complete')


    def exec_auto_application(self):
        '''
        creates a test auto application for activities that don't yet have applications
        @type workitem: WorkItem
        @rtype: bool
        '''
        try:
            if not self.activity.process.enabled:
                raise Exception('process %s disabled.' % self.activity.process.title)
            # no application: default auto app
            if not self.activity.application:
                return self.default_auto_app()
            
            func, args, kwargs = resolve(self.activity.application.get_app_url())
            params = self.activity.app_param
            # params values defined in activity override those defined in urls.py
            if params:
                params = eval('{'+params.lstrip('{').rstrip('}')+'}')
                kwargs.update(params)
            func(workitem=self , **kwargs)
            return True
        except Exception, v:
            _log.error('execution wi %s:%s', self, v)
        return False

    def default_auto_app(self):
        '''
        retrieves wfobject, logs info to it saves
        
        @rtype: bool
        @return: always returns True
        '''
        obj = self.instance.wfobject()
        obj.history += '\n>>> execute auto activity: [%s]' % self.activity.title
        obj.save()
        return True

    def start_subflow(self, actor):
        '''
        starts subflow and blocks passed in workitem
        '''
        subflow_begin_activity = self.activity.subflow.begin
        instance = self.instance
        instance.process = self.activity.subflow
        instance.save()
        self.status = 'blocked'
        self.blocked = True
        self.save()
        
        sub_workitem = self._forward_self_to_activity(subflow_begin_activity)
        return sub_workitem

    def eval_transition_condition(self, transition):
        '''
        evaluate the condition of a transition
        '''
        if not transition.condition:
            return True
        workitem = self # HACK!!! there's a dependency on 'workitem' in eval
                        # created a really perplexing bug for me )-:
        instance = self.instance
        try:
            result = eval(transition.condition)
            
            # boolean expr
            if type(result) == type(True):
                return result
            if type(result) == type(''):
                return (instance.condition==result)
        except Exception, v:
            return (instance.condition==transition.condition)

        return False

    def _check_all_for(self, user, status=('inactive','active')):
        # may be renamed to _check_conditions_for(user)
        '''
        helper function to check for a given user that:
            - process is enabled
            - user can take workitem
            - workitem status is correct
        
        '''
        if type(status)==type(''):
            status = (status,)
            
        if not self.activity.process.enabled:
            error = 'process %s disabled.' % self.activity.process.title
            _log.error('workflow.models.WorkItem._check_all: %s' % error)
            raise Exception(error)
            
        if not self.check_user(user):
            error = 'user %s cannot take workitem %d.' % (user.username, self.id)
            _log.error('workflow.models.WorkItem._check_all %s' % error)
            self.fallout()
            raise Exception(error)
            
        if not self.status in status:
            error = 'workitem %d has not a correct status (%s/%s).' % (
                self.id, self.status, str(status))
            _log.error('workflow.models.WorkItem._check_all: %s' % error)
            raise Exception(error)
    
        return
     
    def __unicode__(self):
        return '%s-%s-%s' % (unicode(self.instance), self.activity, str(self.id))
    
    def has_workitems_to(self):
        b = ( self.workitems_to.count() > 0 )
        return b
    
    def check_user(self, user):
        """return True if authorized, False if not.
        """
        if user and self.user and self.user != user:
            return False
        ugroups = user.groups.all()
        agroups = self.activity.roles.all()
        authorized = False
        if agroups and len(agroups) > 0:
            for g in ugroups:
                if g in agroups:
                    authorized = True
                    break
        else:
            authorized = True
        return authorized
            
    def set_user(self, user, commit=True):
        """affect user if he has a role authorized for activity.
        
        return True if authorized, False if not (workitem then falls out)
        """
        if self.check_user(user):
            self.user = user
            if commit: self.save()
            return True
        self.fallOut()
        return False
    
    def fallout(self):
        self.status = 'fallout'
        self.save()
        Event.objects.create(name='fallout', workitem=self)
    
    def html_action(self):
        label = 'action'
        if self.status == 'inactive':
            label = 'activate'
            url='activate/%d/' % self.id
        if self.status == 'active':
            label = 'complete'
            url='complete/%d/' % self.id
        if self.status == 'complete':
            return 'completed'
        return '<a href=%s>%s</a>' % (url, label)
    
    def html_action_link(self):
        #label = 'action'
        if self.status == 'inactive':
            #label = 'activate'
            url='activate/%d/' % self.id
        if self.status == 'active':
            #label = 'complete'
            url='complete/%d/' % self.id
        if self.status == 'complete':
            raise Exception('no action for completed workitems')
        return '<a href=%s>' % (url)
    
    def time_out(self, delay, unit='days'):
        '''
        return True if timeout reached
          delay:    nb units
          unit: 'weeks' | 'days' | 'hours' ... (see timedelta)
        '''
        tdelta = eval('timedelta('+unit+'=delay)')
        now = datetime.now()
        return (now > (self.date + tdelta))
        
    class Admin:
        date_hierarchy = 'date'
        list_display = ('date', 'user', 'instance', 'activity', 'status')
        list_filter = ('user', 'activity', 'status')

class Event(models.Model):
    """Event are changes that happens on workitems.
    """
    date = models.DateTimeField(auto_now=True, core=True)
    name = models.CharField(max_length=50, core=True)
    workitem = models.ForeignKey(WorkItem, related_name='events', edit_inline=True)
    class Admin:
        date_hierarchy = 'date'
        list_display = ('date', 'name', 'workitem')


class DefaultAppModel(models.Model):
    """Default implementation object class  for process instances.
    
    When a process instance starts, the instance has to carry an
    implementation object that contains the application data. The
    specifications for the implementation class is:
    
    (nothing: now managed by generic relation)
    
    This model is used in process simulations: you don't have to define
    application in activities for this; the DefaultAppModel is used
    to keep workflow history for displaying to users.
    """
    history = models.TextField(editable=False, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        return 'simulation model %s' % str(self.id)
    class Admin:
        list_display = ('__unicode__',)
    class Meta:
        verbose_name='Simulation object'
