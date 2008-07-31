#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Group, User
from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.core.urlresolvers import resolve

#from goflow.workflow.notification import notify_if_needed
from goflow.runtime.managers import ProcessInstanceManager, WorkItemManager
from goflow.common.logger import Log; log = Log('goflow.runtime.models')
from goflow.common.errors import error
from goflow.common import get_class
import yaml


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
    implementation object that contains the application data.
    
    From the instance, the implementation object is reached as follows::
    
        obj = instance.content_object

    In a template, a field date1 will be displayed like this::
      
        {{ instance.content_object.date1 }}
      
    From the object, instances may be reached with the reverse generic relation,
    the following can be added to the model::
    
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
    process = models.ForeignKey('workflow.Process', related_name='instances', 
                                null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, core=True)
    user = models.ForeignKey(User, related_name='instances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              default='initiated')
    old_status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                                  null=True, blank=True)
    condition = models.CharField(max_length=50, null=True, blank=True)
    
    # refactoring
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    # add Manager
    objects = ProcessInstanceManager()

    def __unicode__(self):
        return self.title
    
    def set_status(self, status):
        if not status in [x for (x, y) in ProcessInstance.STATUS_CHOICES]:
            raise error('incorrect_status', status=status)            
            #raise Exception('instance status incorrect :%s' % status)
        self.old_status = self.status
        self.status = status
        self.save()
    
class WorkItem(models.Model):
    """A workitem object represents an activity you are performing.
    
    An Activity object defines the activity, while the workitem object
    represents that you are performing this activity. A workitem is therfore
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
    user = models.ForeignKey(User, related_name='workitems', 
                             null=True, blank=True)
    instance = models.ForeignKey(ProcessInstance, related_name='workitems')
    activity = models.ForeignKey('workflow.Activity', related_name='workitems')
    workitem_from = models.ForeignKey('self', related_name='workitems_to', 
        null=True, blank=True)
    push_roles = models.ManyToManyField(Group, related_name='push_workitems', 
        null=True, blank=True)
    pull_roles = models.ManyToManyField(Group, related_name='pull_workitems', 
        null=True, blank=True)
    blocked = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, 
                              default='inactive')

    # set to the new WorkItemManager
    objects = WorkItemManager()

    def __unicode__(self):
        return '%s-%s-%s' % (unicode(self.instance), self.activity, str(self.id))

    def get_destinations(self, with_timeout=False):
        '''
        Return list of destination activities that meet the 
        conditions of each transition
        
        :type with_timeout: bool
        :param with_timeout: only retrieve activities with_timeout delays
        :rtype: [Activity]
        :return: list of destination activities.
        '''
        transitions = models.get_model('workflow', 'Transition'
                                      ).objects.filter(input=self.activity)
        if with_timeout:
            transitions = transitions.filter(condition__contains='workitem.timeout')
        destinations = []
        for transition in transitions:
            if self.eval_transition_condition(transition):
                destinations.append(transition.output)
        return destinations

    def forward_to_activities(self, with_timeout=False, subflow_workitem=None):
        '''
        Forward this workitem to all valid destination activities.
        
        :type with_timeout: bool
        :param with_timeout: forward to all desinations with timeout
        :type: subflow_workitem: WorkItem
        :param subflow_workitem: a workitem associated with a subflow   
        '''
        
        if self.has_workitems_to() and not subflow_workitem:
            log.debug('forwarding canceled for'+ str(self))
            return
        
        if not with_timeout:
            if self.status != 'complete':
                return
        else:
            log.event('with timout forwarding', self)
                
        for activity in self.get_destinations(with_timeout):
            self.forward_to_activity(activity)

    def run_activity_app(self, **kwds):
        '''
        Runs the current activity application or creates a test auto application for activities 
        that don't yet have applications. Returns True or False based upon success.
        
        :type workitem: WorkItem
        :rtype: bool
        '''
        try:
            if not self.activity.process.enabled:
                raise error('process_disabled', workitem=self)

            # no application: default auto app
            if not self.activity.application:
                obj = self.instance.content_object
                obj.history += '\n>>> execute auto activity: [%s]' % self.activity.title
                obj.save()
                return True
            
            func, args, kwargs = resolve(self.activity.application.get_app_url())
            params = self.activity.app_param
            # params values defined in activity override those defined in urls.py
            if params:
                params = yaml.load(params)
                #params = eval('{'+params.lstrip('{').rstrip('}')+'}')
                kwargs.update(params)
            if kwds:
                kwargs.update(kwds)
            
            # what kind of function is this?
            func(workitem=self , **kwargs)
            return True
        except Exception, v:
            log.error('execution wi %s:%s', self, v)
        return False

    def forward_to_activity(self, activity):
        '''
        Passes the process instance embedded in this workitem 
        to a new workitem that is associated with the destination activity.
        
        :type activity: Activity
        :param activity: the activity instance to this workitem 
                                should be forwarded
        :rtype: WorkItem
        :return: a workitem that has been passed on to the next 
                 activity (and next user)
        '''
        # create a new workitem
        workitem = WorkItem.objects.create(instance=self.instance, user=None, 
                                     activity=activity)
        log.event('created by %s' % self.user.username, self)
        log.event('forwarded to %s' % activity.title, workitem)
        
        # it's been sent from here
        workitem.workitem_from = self
        
        if activity.autostart:
            log('run auto activity: %s workitem: %s', activity.title, workitem)
            try:
                auto_user = User.objects.get(username=settings.WF_USER_AUTO)
            except Exception:
                raise error('no_auto_user')
            # activate it
            workitem.activate(actor=auto_user)
            
            if workitem.run_activity_app():
                workitem.complete(actor=auto_user)
#            else:
                # autotest not run correctly
#                return
            return workitem
        
        if activity.push_application:
            user = workitem.push_to_next_user()
            log('application pushed to user %s', user.username)
            workitem.user = user
            workitem.save()
            log.event('assigned to %s' % user.username, workitem)
            #notify_if_needed(user=user)
        else:
            workitem.pull_roles = workitem.activity.roles.all()
            workitem.save()
            #notify_if_needed(roles=workitem.pull_roles)
        return workitem

    def push_to_next_user(self):
        '''run pushappplication on self (workitem)
        
        This replaces exec_push_application and provides
        the same functionality without eval
        
        examples are::

            class route_to_requester(PushApp):
                def __init__(self, workitem):
                    self.workitem = workitem
                def __call__(self):
                    return self.workitem.instance.user
            
            class route_to_user(PushApp):
                def __init__(self, workitem, username):
                    self.workitem = workitem
                    self.username = username
                def __call__(self):
                    return self.workitem.instance.user
                    
            
        a parameter would look like this is yaml notation::
                        
            username: admin
            delay: 10    
            
        '''
        if not self.activity.process.enabled:
            raise error('process_disabled', name=self.activity.process.title)
        #TODO: this should be by pushapp.name not by pushapp.url
        # e.g: appname = self.activity.pushapp.name
        
        appname = self.activity.push_application.url
        params_yaml = self.activity.pushapp_param
        
        # first try standard pushapps in goflow.workflow.pushapps        
        modpath = 'goflow.workflow.pushapps'
        try:
            Router = get_class(modpath, appname)
            # everything is ok, so return user
            if params_yaml:
                params = yaml.load(params)
                user = Router(workitem=self, **params)()
                return user
            else:
                user = Router(workitem=self)()
                return user
        except (ImportError, AttributeError):
            pass
        
        try:
            modpath = settings.WF_PUSH_APPS_PREFIX+'.'+appname
            Router = get_class(modpath, appname)
            # everything is ok, so return user
            if params_yaml:
                params = yaml.load(params)
                user = Router(workitem=self, **params)()
                return user
            else:
                user = Router(workitem=self)()
                return user
        except (ImportError, AttributeError), e:
            self.fallout()
            log.error(e)
        

    def activate(self, actor):
        '''
        changes this workitem's status to 'active' and logs event & activator
        '''        
        self._check_conditions_for_user(actor, status=('inactive', 'active'))
        if self.status == 'active':
            log.warning('actor:%s workitem:%s already active', actor.username, str(self))
            return
        self.status = 'active'
        self.user = actor
        self.save()
        log.event('activated by '+actor.username, workitem=self)

    def complete(self, actor):
        '''
        changes status of this workitem to 'complete' and logs event & activator
        '''
        self._check_conditions_for_user(actor, status='active')
        self.status = 'complete'
        self.user = actor
        self.save()
        log.event('completed by %s' % actor.username, self)
        
        if self.activity.autofinish:
            log.debug('activity autofinish: forward')
            self.forward_to_activities()
        
        # if end activity, instance is complete
        if self.instance.process.end == self.activity:
            log.info('activity end process %s' % self.instance.process.title)
            # first test subflow
            lwi = WorkItem.objects.filter(activity__subflow=self.instance.process,
                                          status='blocked',
                                          instance=self.instance)
            if lwi.count() > 0:
                log.info('parent process for subflow %s' % self.instance.process.title)
                workitem0 = lwi[0]
                workitem0.instance.process = workitem0.activity.process
                workitem0.instance.save()
                log.info('process change for instance %s' % workitem0.instance.title)
                workitem0.status = 'complete'
                workitem0.save()
                workitem0.forward_to_activities(subflow_workitem=self)
            else:
                self.instance.set_status('complete')

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
        
        sub_workitem = self.forward_to_activity(subflow_begin_activity)
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

    def _check_conditions_for_user(self, user, status=('inactive','active')):
        # may be renamed to _check_conditions_for_user(user)
        '''
        helper function to check for a given user that:
            - process is enabled
            - user can take workitem
            - workitem status is correct
        
        '''
        if type(status)==type(''):
            status = (status,)
            
        if not self.activity.process.enabled:
            raise error('process_disabled', log=log, workitem=self)
            
        if not self.check_user(user):
            self.fallout()
            raise error('invalid_user_for_workitem', log=log, user=user, workitem=self)
            
        if not self.status in status:
            raise error('incorrect_workitem_status', log=log, workitem=self)
    
        return
         
    def has_workitems_to(self):
        return ( self.workitems_to.count() > 0 )

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
            if commit: 
                self.save()
            return True
        self.fallout()
        return False
    
    def fallout(self):
        self.status = 'fallout'
        self.save()
        log.event('fallout', self)
    
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
    
    def timeout(self, delay, unit='days'):
        '''
        return True if timeout reached
          delay:    nb units
          unit: 'weeks' | 'days' | 'hours' ... (see timedelta)
        '''
        tdelta = timedelta(**{unit:delay})
        now = datetime.now()
        return (now > (self.date + tdelta))

class Event(models.Model):
    """Events are changes that happen to workitems.
    """
    date = models.DateTimeField(auto_now=True, core=True)
    name = models.CharField(max_length=50, core=True)
    workitem = models.ForeignKey('WorkItem', 
        related_name='events', edit_inline=True)

class DefaultAppModel(models.Model):
    """Default implementation object class for process instances.
    
    When a process instance starts, the instance has to carry an
    implementation object that contains the application data. 

    This model is used in process simulations: you don't have to define
    application in activities for this; the DefaultAppModel is used
    to keep workflow history for displaying to users.
    """
    history = models.TextField(editable=False, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    
    def __unicode__(self):
        return 'simulation model %s' % str(self.id)
    class Meta:
        verbose_name='Simulation object'
