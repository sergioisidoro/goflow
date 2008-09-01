#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Group, User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.core.urlresolvers import resolve

#from goflow.workflow.notification import notify_if_needed
from goflow.tools.errors import error
from goflow.tools import get_obj, safe_eval
from goflow.tools.decorators import allow_tags
from goflow.tools.logger import Log; log = Log('goflow.workflow.models')

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
            raise Exception('process %s disabled.' % self.title)

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

class ProcessInstanceManager(models.Manager):
    '''Custom model manager for ProcessInstance
    '''

    def start(self, process_name, user, item, title=None):
        '''
        Returns a workitem given the name of a preexisting enabled Process
        instance, while passing in the id of the user, the contenttype
        object and the title.

        :type process_name: string
        :param process_name: a name of a process. e.g. 'leave'
        :type user: User
        :param user: an instance of django.contrib.auth.models.User,
                     typically retrieved through a request object.
        :type item: ContentType
        :param item: a content_type object e.g. an instance of LeaveRequest
        :type: title: string
        :param title: title of new ProcessInstance instance (optional)
        :rtype: WorkItem
        :return: a newly configured workitem sent to auto_user,
                 a target_user, or ?? (roles).

        usage::

            wi = ProcessInstance.objects.start(process_name='leave',
                                       user=admin, item=leaverequest1)

        '''
        process = Process.objects.get(title=process_name, enabled=True)
        if not title or (title=='instance'):
            title = '%s %s' % (process_name, str(item))
        instance = self.create(user=user, title=title, content_object=item)
        instance.process = process
        # instance running
        instance.set_status('running')
        instance.save()

        workitem = WorkItem.objects.create(instance=instance, user=user,
                                           activity=process.begin)
        log.event('created by ' + user.username, workitem)
        log('process:', process_name, 'user:', user.username, 'item:', item)

        if process.begin.autostart:
            log('run auto activity', process.begin.title, 'workitem:', workitem)
            auto_user = User.objects.get(username=settings.WF_USER_AUTO)
            workitem.activate(actor=auto_user)

            if workitem.run_activity_app():
                log('workitem.run_activity_app:', workitem)
                workitem.complete(actor=auto_user)
            return workitem

        if process.begin.push_application:
            target_user = workitem.exec_push_application()
            #target_user = workitem.push()
            log('application pushed to user', target_user.username)
            workitem.user = target_user
            workitem.save()
            log.event('assigned to '+target_user.username, workitem)
            #notify_if_needed(user=target_user)
        else:
            # set pull roles; useful (in activity too)?
            workitem.pull_roles = workitem.activity.roles.all()
            workitem.save()
            #notify_if_needed(roles=workitem.pull_roles)

        return workitem


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



class WorkItemManager(models.Manager):
    '''Custom model manager for WorkItem
    '''
    def get_by(self, id, user=None, enabled_only=False, status=('inactive','active')):
        '''
        Safely retrieves a single WorkItem instance for a user given its id

        Valid workitems must be either activate or inactive to be retrieved.

        :type id: int
        :param id: the id of the WorkItem instance
        :type user: User
        :param user: an instance of django.contrib.auth.models.User,
                     typically retrieved through a request object.
        :type enabled_only: bool
        :param enabled_only: implies that only enabled processes should be queried
        :type status: tuple or string
        :param status: ensure that workitem has one of the given set of statuses
        :raises: AssignmentError if user is not authorized to get the workitem instance

        usage::

            workitem = WorkItem.objects.get_by(id, user=request.user)

        '''
        if enabled_only:
            workitem = self.get(id=id, activity__process__enabled=True)
        else:
            workitem = self.get(id=id)
        workitem.check_conditions_for_user(user, status)
        return workitem

    def get_all_by(self, user=None, username=None, activity=None, status=None,
                      notstatus=('blocked','suspended','fallout','complete'), noauto=True):
        """
        Retrieve list of workitems (in order to display a task list for example).

        :type user: User
        :param user: filter on instance of django.contrib.auth.models.User (default=all)
        :type username: string
        :param username: filter on username of django.contrib.auth.models.User (default=all)
        :type activity: Activity
        :param activity: filter on instance of goflow.workflow.models.Activity (default=all)
        :type status: string
        :param status: filter on status (default=all)
        :type notstatus: string or tuple
        :param notstatus: list of status to exclude (default: [blocked, suspended, fallout, complete])
        :type noauto: bool
        :param noauto: if True (default) auto activities are excluded.

        usage::

            workitems = WorkItem.objects.get_all_by(user=me, notstatus='complete', noauto=True)

        """
        groups = Group.objects.all()
        if user:
            query = self.filter(user=user, activity__process__enabled=True)
            groups = user.groups.all()
        else:
            if username:
                query = self.filter(
                        user__username=username,
                        activity__process__enabled=True
                )
                groups = User.objects.get(username=username).groups.all()
            else:
                query = None
        if query:
            if status:
                query = query.filter(status=status)

            if notstatus:
                query = query.exclude(status=notstatus)
            else:
                for status in notstatus:
                    query = query.exclude(status=status)

            if noauto:
                query = query.exclude(activity__autostart=True)

            if activity:
                #TODO: this is not used...??
                sq = query.filter(activity=activity)

            query = list(query)
        else:
            query = []

        # search pullable workitems
        for role in groups:
            pullables = self.filter(pull_roles=role, activity__process__enabled=True)
            if status:
                pullables = pullables.filter(status=status)

            if notstatus:
                pullables = pullables.exclude(status=notstatus)
            else:
                for status in notstatus:
                    pullables = pullables.exclude(status=status)

            if noauto:
                pullables = pullables.exclude(activity__autostart=True)

            if activity:
                pullables = pullables.filter(activity=activity)

            if user:
                pp = pullables.filter(user__isnull=True) # tricky
                pullables = pullables.exclude(user=user)
                query.extend(list(pp))

            if username:
                pullables = pullables.exclude(user__username=username)

            log.debug('pullables workitems role %s: %s', role, str(pullables))
            query.extend(list(pullables))

        return query



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
        >>> # ctype can be any django model (we will use arbitrarily use User here)
        >>> ctype = ContentType.objects.get_for_model(User)
        >>> pi = ProcessInstance.objects.create(title='proc_instance', user=user,
        ...                      content_type=ctype, object_id=user.id)
        >>> WorkItem.objects.create(user=user, instance=pi, activity=a1)
        <WorkItem: proc_instance-activity1 (myprocess)-1>
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

