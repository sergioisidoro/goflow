#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from goflow.utils.logger import Log; log = Log('goflow.workflow.pushapps')

def route_to_requester(workitem):
    return workitem.instance.user

def route_to_superuser(workitem, username='admin'):
    user = User.objects.get(username=username)
    if user.is_superuser:
        return user
    log.warning('this user is not a super-user:', username)
    return None

def to_current_superuser(workitem, user_pushed):
    '''Should be used in all push applications for testing purposes.
      
        usage:
            return to_current_superuser(workitem, user_pushed)
    '''
    return None

def route_to_user(workitem, username):
    return User.objects.get(username=username)
