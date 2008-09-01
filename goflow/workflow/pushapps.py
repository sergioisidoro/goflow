#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from goflow.tools.logger import Log; log = Log('goflow.workflow.pushapps')

def route_to_requester(workitem):
    '''Simplest possible pushapp
    '''
    return workitem.instance.user

def route_to_user(workitem, username):
    '''Route to user given a username
    '''
    return User.objects.get(username=username)

def route_to_superuser(workitem, username='admin'):
    '''Route to the superuser
    '''
    user = User.objects.get(username=username)
    if user.is_superuser:
        return user
    else:
        log.warning('this user is not a super-user:', username)
        return None

# Alternative class based pushapps 
# ---------------------------------
# class route_to_requester(object):
#     def __init__(self, workitem):
#         self.workitem = workitem
#     def __call__(self):
#         return self.workitem.instance.user
#
#
