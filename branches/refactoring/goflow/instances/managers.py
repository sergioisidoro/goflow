#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import Group, User
from goflow.common.logger import Log; log = Log('goflow.instances.managers')

class ProcessInstanceManager(models.Manager):
    '''Custom model manager for ProcessInstance
    '''

    def add(self, user, title, obj_instance):
        '''
        Returns a newly saved ProcessInstance instance.

        :type user: User
        :param user: an instance of `django.contrib.auth.models.User`,
                     typically retrieved through a request object.
        :type title: string
        :param title: the title of the new ProcessInstance instance.
        :type obj_instance: ContentType
        :param obj_instance: an instance of ContentType, which is typically
                             associated with a django Model.
        :rtype: ProcessInstance
        :returns: a new (saved) ProcessInstance instance.

        usage::

            >>> # get a user
            >>> user = User.objects.get(username='primus')
            >>> # obj_instance can be any instance of a Model (we will reuse user here)
            >>> ProcessInstance.objects.add(user, "test title", user)
            <ProcessInstance: test title>

        '''
        instance = self.create(user=user, title=title, content_object=obj_instance)
        return instance


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
