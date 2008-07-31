#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from goflow.common.logger import Log; log = Log('goflow.workflow.pushapps')

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
    log.warning('this user is not a super-user:', username)
    return None

def to_current_superuser(workitem, user_pushed):
    '''Should be used in all push applications for testing purposes.
    
        (**NOT IMPLEMENTED**)
      
        usage::
        
            return to_current_superuser(workitem, user_pushed)
    '''
    return None

# 
# class route_to_requester(object):
#     def __init__(self, workitem):
#         self.workitem = workitem
#     def __call__(self):
#         return self.workitem.instance.user
# 
# 
# class route_to_user(object):
#     '''Route to user given a username
#     '''
#     def __init__(self, workitem, username):
#         self.workitem = workitem
#         self.username = username
#     def __call__(self):
#         return User.objects.get(username=username)
# 
# 
# class route_to_superuser(object):
#     '''Route to the superuser
#     '''
#     def __init__(self, workitem, username='admin'):
#         self.workitem = workitem
#         self.username = username
#     def __call__(self):
#         if user.is_superuser:
#             return user
#         log.warning('this user is not a super-user:', username)
#         return None
# 
