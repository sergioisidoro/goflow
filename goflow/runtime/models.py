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
from goflow.common import get_obj, safe_eval


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

    usage::

        >>> # first get or create a user
        >>> user = User.objects.get(username='primus')
        >>> ctype = ContentType.objects.get_for_model(User)
        >>> pi = ProcessInstance(title='proc_instance1', user=user,
        ...                      content_type=ctype, object_id=user.id)
        >>> pi.save()

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
    creation_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='instances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='initiated')
    old_status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                  null=True, blank=True)
    condition = models.CharField(max_length=50, null=True, blank=True)

    # application date object (accessed as obj.content_object)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # add Manager
    objects = ProcessInstanceManager()

    def __unicode__(self):
        return self.title

    def set_status(self, status):
        if not status in [x for (x, y) in ProcessInstance.STATUS_CHOICES]:
            raise error('incorrect_pinstance_status', status=status)
        self.old_status = self.status
        self.status = status
        self.save()

class WorkItem(models.Model):
    """A workitem object represents an activity you are performing.

    An Activity object defines the activity, while the workitem object
    represents that you are performing this activity. A workitem is therfore
    an "instance" of the activity.

    usage::

        >>> from goflow.workflow.models import *
        >>> proc = Process.objects.create(title="myprocess", description="desc")
        >>> a1 = Activity.objects.create(title='activity1', process=proc)
        >>> user = User.objects.get(username='primus')
        >>> pi = ProcessInstance.objects.add(user, 'test proc_instance', user)
        >>> WorkItem.objects.create(user=user, instance=pi, activity=a1)
        <WorkItem: test proc_instance-activity1 (myprocess)-1>
    """
    STATUS_CHOICES = (
                      ('blocked', 'blocked'),
                      ('inactive', 'inactive'),
                      ('active', 'active'),
                      ('suspended', 'suspended'),
                      ('fallout', 'fallout'),
                      ('complete', 'complete'),
                      )
    date = models.DateTimeField(auto_now=True)
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
        return '%s-%s-%s' % (
            unicode(self.instance), self.activity, str(self.id))


    def forward_to_activity(self, target_activity):
        '''
        Passes the process instance embedded in this workitem
        to a new workitem that is associated with the destination activity.

        :type target_activity: Activity
        :param target_activity: the activity instance to this workitem
                                should be forwarded
        :rtype: WorkItem
        :return: a workitem that has been passed on to the next
                 activity (and next user)
        '''
        instance = self.instance
        wi = WorkItem.objects.create(instance=instance, user=None,
                                     activity=target_activity)
        log.event('created by %s' % self.user.username, wi)
        log.event('forwarded to %s' % target_activity.title, self)
        wi.workitem_from = self
        if target_activity.autostart:
            log.info('run auto activity %s workitem %s',
                target_activity.title, str(wi))
            try:
                auto_user = User.objects.get(username=settings.WF_USER_AUTO)
            except Exception:
                raise error('no_auto_user')
            wi.activate(actor=auto_user)
            if wi.exec_application():
                wi.complete(actor=auto_user)
            return wi

        if target_activity.push_application:
            target_user = wi.exec_push_application()
            log.info('application pushed to user %s', target_user.username)
            wi.user = target_user
            wi.save()
            log.event('assigned to %s' % target_user.username, wi)
            #notify_if_needed(user=target_user)
        else:
            wi.pull_roles = wi.activity.roles.all()
            wi.save()
            #notify_if_needed(roles=wi.pull_roles)
        return wi


    def forward_to_activities(self, with_timeout=False, subprocess_workitem=None):
        '''
        Forward this workitem to all valid destination activities.

        :type with_timeout: bool
        :param with_timeout: apply time_out during forwarding
        :type: subprocess_workitem: WorkItem
        :param subprocess_workitem: a workitem associated with a subprocess
        '''
        log.info(self)
        if not with_timeout:
            if self.status != 'complete':
                return
        if self.has_workitems_to() and not subprocess_workitem:
            log.debug('forwarding canceled for'+ str(self))
            return

        if with_timeout:
            log.event('timout forwarding', self)

        for target in self.get_target_activities(with_timeout):
            self.forward_to_activity(target)

    def get_target_activities(self, with_timeout=False):
        '''
        Return list of destination activities that meet the
        conditions of each transition

        :type with_timeout: bool
        :param with_timeout: apply timout during forwarding
        :rtype: [Activity]
        :return: list of destination activities.
        '''
        transitions = models.get_model('workflow', 'Transition'
                                      ).objects.filter(input=self.activity)
        if with_timeout:
            transitions = transitions.filter(condition__contains='workitem.timeout')
        target_activities = []
        for transition in transitions:
            if self.eval_transition_condition(transition):
                target_activities.append(transition.output)
        return target_activities


    def exec_push_application(self):
        '''
        Execute push application on workitem

        :rtype: User
        :returns: an instance of User that is obtained from
                  the push_application function or class.
        '''
        if not self.activity.process.enabled:
            raise error('process_disabled', workitem=self)
        appname = self.activity.push_application.url
        params = self.activity.pushapp_param

        try:
            # 1st try std pushapps:
            modpath = 'goflow.workflow.pushapps'
            routing_func = get_obj(modpath, appname)
        except (ImportError, AttributeError), e:
            # prefix specified in settings
            modpath = settings.WF_PUSH_APPS_PREFIX
            routing_func = get_obj(modpath, appname)
        try:
            if params:
                # safe_eval return a functor
                params = safe_eval(params)()
                result = routing_func(self, **params)
            else:
                result = routing_func(self)
        except Exception, e:
            log.error(e)
            result = None
            self.fallout()
        return result




    def activate(self, actor):
        '''
        changes this workitem's status to 'active' and logs event & activator

        :type actor: User
        :param actor: a valid User instance
        '''
        self.check_conditions_for_user(actor, status=('inactive', 'active'))
        if self.status == 'active':
            log.warning('actor:%s workitem:%s already active',
                actor.username, str(self))
            return
        self.status = 'active'
        self.user = actor
        self.save()
        log.event('activated by '+actor.username, workitem=self)


    def complete(self, actor):
        '''
        changes status of this workitem to 'complete' and logs event & activator

        :type actor: User
        :param actor: a valid User instance
        '''
        self.check_conditions_for_user(actor, status='active')
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
            # first test subprocess
            lwi = WorkItem.objects.filter(activity__subprocess=self.instance.process,
                                          status='blocked',
                                          instance=self.instance)
            if lwi.count() > 0:
                log.info('parent process for subprocess %s' % self.instance.process.title)
                workitem0 = lwi[0]
                workitem0.instance.process = workitem0.activity.process
                workitem0.instance.save()
                log.info('process change for instance %s' % workitem0.instance.title)
                workitem0.status = 'complete'
                workitem0.save()
                workitem0.forward_to_activities(subprocess_workitem=self)
            else:
                self.instance.set_status('complete')


    def exec_application(self):
        '''
        executes the activity application or if one doesn't exist
        creates a test auto application for activities that don't
        yet have applications

        :rtype: bool
        :return: True if application is successfully executed
        :raises: Exception otherwise
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
                params_dict = safe_eval(params)()
                kwargs.update(params_dict)
            func(workitem=self , **kwargs)
            return True
        except Exception, e:
            log.error('execution wi %s:%s', self, e)
        return False


    def start_subprocess(self, actor):
        '''
        starts subprocess and blocks passed in workitem

        :type actor: User
        :param actor: a valid User instance
        '''
        subprocess_begin_activity = self.activity.subprocess.begin
        instance = self.instance
        instance.process = self.activity.subprocess
        instance.save()
        self.status = 'blocked'
        self.blocked = True
        self.save()

        sub_workitem = self.forward_to_activity(subprocess_begin_activity)
        return sub_workitem

    def eval_transition_condition(self, transition):
        '''safely evaluate the condition of a transition

        :type transition: Transition
        :param transition: evaluates transition.condition
        :rtype: bool
        :returns: True or False depending on the evaluation
        :raises: Exception which then compares current
                 instance.condition and transition.condition
        '''
        # the absence of a condition implies a True value
        if not transition.condition:
            return True
        try:
            # safe boolean expression evaluation
            result = safe_eval(transition.condition,
                          workitem=self, instance=self.instance)()
            #if bool type:
            if type(result) == type(True):
                return result
            #if string type:
            if type(result) == type(''):
                return (self.instance.condition==result)
        except (NameError, SyntaxError), e:
            return (self.instance.condition==transition.condition)
        # otherwise
        return False

    def check_conditions_for_user(self, user, status=('inactive','active')):
        '''function to check for a given user that conditions are met

        checks for the following:
            - process is enabled
            - user can take workitem
            - workitem status is correct

        :type user: User
        :param user: a valid User instance

        '''
        if type(status)==type(''):
            status = (status,)

        if not self.activity.process.enabled:
            raise error('process_disabled', log=log, workitem=self)

        if not self.check_user(user):
            self.fallout()
            raise error('invalid_user_for_workitem', log=log,
                user=user, workitem=self)

        if not self.status in status:
            raise error('incorrect_workitem_status', log=log, workitem=self)

        return

    def has_workitems_to(self):
        '''checks that workitems_to.count > 0
        :rtype: bool
        '''
        return ( self.workitems_to.count() > 0 )

    def check_user(self, user):
        """return True if authorized, False if not.
        :type user: User
        :param User: a valid User instance

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
        '''affect user if he has a role authorized for activity.
        Has an important side-effect of saving the workitem is user
        is authorized

        (TODO: this may have to change, as it is not atomic enough)
        return True if authorized, False if not (workitem then falls out)

        :type user: User
        :param User: a valid User instance
        :type commit: bool
        :param commit: save (workitem) self if true (default)
        '''
        if self.check_user(user):
            self.user = user
            if commit:
                self.save()
            return True
        else:
            self.fallout()
            return False

    def fallout(self):
        '''changes status of workitem to 'fallout'
        '''
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
        if self.status == 'inactive':
            url='activate/%d/' % self.id
        if self.status == 'active':
            url='complete/%d/' % self.id
        if self.status == 'complete':
            raise Exception('no action for completed workitems')
        return '<a href=%s>' % (url)

    def timeout(self, delay, unit='days'):
        '''return True if timeout reached

          :param delay: number of units
          :type delay: string
          :param unit: 'weeks' | 'days' | 'hours' ... (see timedelta)
          :type unit: string
          :rtype: bool
        '''
        tdelta = timedelta(**{unit:delay})
        now = datetime.now()
        return (now > (self.date + tdelta))


class Event(models.Model):
    """Events are changes that happen to workitems.
    """
    date = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=50)
    workitem = models.ForeignKey('WorkItem', related_name='events')


class DefaultAppModel(models.Model):
    """Default implementation object class for process instances.

    When a process instance starts, the instance has to carry an
    implementation object that contains the application data.

    This model is used in process simulations: you don't have to define
    application in activities for this; the DefaultAppModel is used
    to keep workflow history for displaying to users.

    usage::

        >>> test = DefaultAppModel.objects.create(history="my history", comment='...')
        >>> test
        <DefaultAppModel: simulation model 1>

    """
    history = models.TextField(editable=False, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return 'simulation model %s' % str(self.id)

    class Meta:
        verbose_name='Simulation object'
