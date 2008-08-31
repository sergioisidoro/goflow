#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType

from goflow.common.decorators import allow_tags
from datetime import datetime, timedelta

class Activity(models.Model):
    """Activities represent any kind of action an employee might want to do on an instance.

    The action might want to change the object instance, or simply
    route the instance on a given path. Activities are the places
    where any of these action are resolved by employees.

    usage::

        >>> # first get or create a process
        >>> p1 = Process.objects.new(title="test process", description="desc")
        >>> activity = Activity(title="myactivity", process=p1)
        >>> activity.save()

    """
    KIND_CHOICES = (
                    ('standard', 'standard'),
                    ('dummy', 'dummy'),
                    ('subprocess', 'subprocess'),
                    )
    COMP_CHOICES = (
                    ('and', 'and'),
                    ('xor', 'xor'),
                    )
    title = models.CharField(max_length=100)
    kind =  models.CharField(max_length=10, choices=KIND_CHOICES, verbose_name='type', default='standard')
    process = models.ForeignKey('Process', related_name='activities', verbose_name='process')
    push_application = models.ForeignKey('PushApplication', verbose_name='push application',
                                         related_name='push_activities', null=True, blank=True)
    pushapp_param = models.CharField(max_length=100, null=True, blank=True,
                                verbose_name='push application parameters',
                                help_text="parameters as python dictionary will be safely evaluated")
    application = models.ForeignKey('Application', related_name='activities',
                                    verbose_name='application url', null=True, blank=True,
                                    help_text='leave it blank for prototyping the process without coding')
    app_param = models.CharField(max_length=100, verbose_name='application parameters', null=True,
                                 blank=True,
                                 help_text='parameters as python dictionary will be safely evaluated')
    subprocess = models.ForeignKey('Process', verbose_name='subprocess process',
                                related_name='parent_activities', null=True, blank=True)
    roles = models.ManyToManyField(Group, related_name='activities', null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    autostart = models.BooleanField(default=False)
    autofinish = models.BooleanField(default=True)
    join_mode =  models.CharField(max_length=3, choices=COMP_CHOICES,
                                  verbose_name='join mode', default='xor')
    split_mode =  models.CharField(max_length=3, choices=COMP_CHOICES,
                                   verbose_name='split mode', default='and')

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.process.title)

    class Meta:
        unique_together = (("title", "process"),)
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

class ProcessManager(models.Manager):
    '''Custom model manager for Process
    '''

    def new(self, title, description='', start='Start', end='End'):
        '''
        Creates, saves, and returns a new Process instance
        and adds a start and end activity to it.

        :type title: string
        :param title: the title of the new Process instance.
        :type description: string
        :param description: an optional description of the new Process instance.
        :type start: string
        :param start: title of initial Activity
        :type end: string
        :param end: title of final Activity
        :rtype: Process
        :return: a new (saved) Process instance.

        usage::

            process1 = Process.objects.new(title='process1')
        '''
        process = self.create(title=title, description=description)
        process.begin = Activity.objects.create(title=start, process=process)
        process.end = Activity.objects.create(title=end, process=process)
        process.save()
        return process

class Process(models.Model):
    """A process holds the map that describes the flow of work.

    The process map is made of activities and transitions.
    The instances you create on the map will begin the flow in
    the configured begin activity. Instances can be moved
    forward from activity to activity, going through transitions,
    until they reach the End activity.

    There are three ways to create a process instance::

        >>> # (1) using the manager
        >>> process = Process.objects.create(title="request_vacation",
        ... description="description", enabled=True, priority=0)
        >>> process
        <Process: request_vacation>

        >>> # (2) using the model class
        >>> process = Process(title='request_holiday', description='desc2')
        >>> process.save()
        >>> process
        <Process: request_holiday>

        >>> # (3) using the manager class new method (creates start & end activities)
        >>> process = Process.objects.new(title='request_report', description='desc2')
        >>> process
        <Process: request_report>

    """
    enabled = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    begin = models.ForeignKey('Activity', related_name='bprocess',
                              verbose_name='initial activity', null=True, blank=True)
    end = models.ForeignKey('Activity', related_name='eprocess',
                            verbose_name='final activity', null=True, blank=True,
                            help_text='a default end activity will be created if blank')
    priority = models.IntegerField(default=0)

    # add new ProcessManager
    objects = ProcessManager()

    class Meta:
        verbose_name_plural = 'Processes'
        permissions = (
            ("can_instantiate", "Can instantiate"),
            ("can_browse", "Can browse"),
        )

    def __unicode__(self):
        return self.title

    @allow_tags
    def action(self):
        return ('add <a href=../activity/add/>a new activity</a> or '
                '<a href=../activity/>copy</a> an activity from another process')


    def can_start(self, user):
        '''
        Checks whether a process is enabled and whether the user has permission
        to instantiate it; raises exceptions if not the case, returns None otherwise.

        :type user: User
        :param user: an instance of django.contrib.auth.models.User,
                     typically retrieved through a request object.
        :rtype:
        :return: passes silently if checks are met,
                 raises exceptions otherwise.

        usage::

            process.can_start(user=admin)

        '''
        if not self.enabled:
            raise Exception('process %s disabled.' % process_name)

        if user.has_perm("workflow.can_instantiate"):
            lst = user.groups.filter(name=self.title)
            if lst.count()==0 or \
               (lst[0].permissions.filter(codename='can_instantiate').count() == 0):
                raise Exception('permission needed to instantiate process %s.' % self.title)
        else:
            raise Exception('permission needed.')
        return



    def add_activity(self, name):
        '''Add an activity to the process

        :type name: string
        :param name: name of activity (get or created)
        '''
        a, created = Activity.objects.get_or_create(title=name, process=self,
                                                    defaults={'description':'(add description)'})
        return a

    def add_transition(self, name, activity_out, activity_in):
        '''Add an transition to the process

        :type name: string
        :param name: name of activity (get or created)
        :type activity_out: Activity
        :param activity_out: the 'to' or output Activity
        :type activity_in: Activity
        :param activity_in: the 'from' or input Activity
        '''

        t, created = Transition.objects.get_or_create(name=name, process=self,
                                             output=activity_out,
                                             defaults={'input':activity_in})
        return t


class Application(models.Model):
    """ An application is a python view that can be called by URL.

        Activities can call applications.
        A commmon prefix may be defined: see settings.WF_APPS_PREFIX

        usage::

            >>> app = Application(url="check_validity", suffix="w")
            >>> app.save()

    """
    url = models.CharField(max_length=255, unique=True,
                           help_text='relative to prefix in settings.WF_APPS_PREFIX')
    # TODO: drop abbreviations (perhaps here not so necessary to ??
    SUFF_CHOICES = (
                    ('w', 'workitem.id'),
                    ('i', 'instance.id'),
                    ('o', 'object.id'),
                    )
    suffix =  models.CharField(max_length=1, choices=SUFF_CHOICES, verbose_name='suffix', null=True, blank=True,
                               help_text='http://[host]/[settings.WF_APPS_PREFIX/][url]/[suffix]')
    def __unicode__(self):
        return self.url

    def get_app_url(self, workitem=None, extern_for_user=None):
        from django.conf import settings
        path = '%s/%s/' % (settings.WF_APPS_PREFIX, self.url)
        if workitem:
            if self.suffix:
                if self.suffix == 'w': path = '%s%d/' % (path, workitem.id)
                if self.suffix == 'i': path = '%s%d/' % (path, workitem.instance.id)
                if self.suffix == 'o': path = '%s%d/' % (path, workitem.instance.content_object.id)
            else:
                path = '%s?workitem_id=%d' % (path, workitem.id)
        if extern_for_user:
            path = 'http://%s%s' % (extern_for_user.get_profile().web_host, path)
        return path

    def has_test_env(self):
        if Process.objects.filter(title='test_%s' % self.url).count() > 0:
            return True
        return False

    def create_test_env(self, user=None):
        if self.has_test_env():
            return

        g = Group.objects.create(name='test_%s' % self.url)
        ptype = ContentType.objects.get_for_model(Process)
        cip = Permission.objects.get(content_type=ptype, codename='can_instantiate')
        g.permissions.add(cip)
        # group added to current user
        if user:
            user.groups.add(g)

        p = Process.objects.create(title='test_%s' % self.url, description='unit test process')
        p.begin = p.end
        p.begin.autostart = False
        p.begin.title = "test_activity"
        p.begin.kind = 'standard'
        p.begin.application = self
        p.begin.description = 'test activity for application %s' % self.url
        p.begin.save()

        p.begin.roles.add(g)

        p.save()

    def remove_test_env(self):
        if not self.has_test_env(): return
        Process.objects.filter(title='test_%s' % self.url).delete()
        Group.objects.filter(name='test_%s' % self.url).delete()

    @allow_tags
    def test(self):
        if self.has_test_env():
            return ('<a href=teststart/%d/>start test instances</a> | '
                    '<a href=testenv/remove/%d/>remove unit test env</a>') % (self.id, self.id)
        else:
            return '<a href=testenv/create/%d/>create unit test env</a>' % self.id


class Parameter(models.Model):
    """A parameter is a definition of what goes into workflow application or routing
    function

    usage::

        >>> param = Parameter(name="age", type="integer", direction="in")
        >>> param.save()

    """
    PARAMETER_TYPES = (
                    ('string', 'string'),
                    ('integer', 'integer'),
                    ('decimal', 'decimal'),
                    ('datetime', 'datatime')
    )
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=PARAMETER_TYPES)
    direction = models.CharField(max_length=2, choices=[('in','in'),('out','out')])
    def __unicode__(self):
        return self.name


class PushApplication(models.Model):
    """A push application routes a workitem to a specific user.
    It is a python function with the same prototype as the built-in
    one below::

        def route_to_requester(workitem):
            return workitem.instance.user

    Other parameters may be added (see Activity.pushapp_param field).
    Built-in push applications are implemented in pushapps module.
    A commmon prefix may be defined: see settings.WF_PUSH_APPS_PREFIX

    usage::

        >>> pushapp = PushApplication(url="route_to_finance")
        >>> pushapp.save()

    """
    # name = models.CharField(max_length=50, unique=True)
    url = models.CharField(max_length=255, unique=True)
    def __unicode__(self):
        return self.url

    @allow_tags
    def test(self):
        return '<a href=#>test (not yet implemented)</a>'


class Transition(models.Model):
    """ A Transition connects two Activities: a From and a To activity.

    Since the transition is oriented you can think at it as being a
    link starting from the From and ending in the To activity.
    Linking the activities in your process you will be able to draw
    the map.

    Each transition is associated to a condition that will be tested
    each time an instance has to choose which path to follow.
    If the only transition whose condition is evaluated to true will
    be the transition choosen for the forwarding of the instance.

    usage::

        >>> # first get or create process
        >>> p = Process.objects.new(title='test proc1', description="desc")
        >>> a1 = Activity.objects.create(title="activity_in", process=p)
        >>> a2 = Activity.objects.create(title="activity_out", process=p)
        >>> t = Transition(name='send_to_employee', process=p, input=a1, output=a2,
        ...                condition="OK")
        >>> t.save()
    """
    name = models.CharField(max_length=50, null=True, blank=True)
    process = models.ForeignKey(Process, related_name='transitions')
    input = models.ForeignKey(Activity, related_name='transition_inputs')
    condition = models.CharField(max_length=200, null=True, blank=True,
                                 help_text='ex: instance.condition=="OK" | OK')
    output = models.ForeignKey(Activity, related_name='transition_outputs')
    description = models.CharField(max_length=100, null=True, blank=True)

    def save(self):
        if self.input.process != self.process or self.output.process != self.process:
            raise Exception("a transition and its activities must be linked to the same process")
        models.Model.save(self)

    def __unicode__(self):
        return self.name or 't%d' % self.id

    class Meta:
        pass
        #unique_together = (("input", "condition"),)


class UserProfile(models.Model):
    """Contains workflow-specific user data.

    It has to be declared as auth profile module as following:
    settings.AUTH_PROFILE_MODULE = 'workflow.userprofile'

    If your application have its own profile module, you must
    add to it the workflow.UserProfile fields.
    """
    user = models.ForeignKey(User, unique=True)
    web_host = models.CharField(max_length=100, default='localhost:8000')
    notified = models.BooleanField(default=True, verbose_name='notification by email')
    last_notif = models.DateTimeField(default=datetime.now())
    nb_wi_notif = models.IntegerField(default=1, verbose_name='items before notification',
                                      help_text='notification if the number of items waiting is reached')

    notif_delay = models.IntegerField(default=1, verbose_name='Notification delay', help_text='in days')

    def save(self):
        if not self.last_notif: self.last_notif = datetime.now()
        models.Model.save(self)

    def check_notif_to_send(self):
        now = datetime.now()
        if now > self.last_notif + timedelta(days=self.notif_delay or 1):
            return True
        return False

    def notif_sent(self):
        now = datetime.now()
        self.last_notif = now
        self.save()

    class Meta:
        verbose_name='Workflow user profile'
        verbose_name_plural='Workflow users profiles'
