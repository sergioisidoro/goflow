#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from models import Manager
from goflow.utils.logger import Log; log = Log('leavedemo.leave.pushapplications')


def route_to_secretary(workitem):
    user = workitem.instance.user
    mgr_secretary = Manager.objects.get(category='secretary', users=user)
    return mgr_secretary.user

def route_to_supervisor(workitem):
    user = workitem.instance.user
    mgr_supervisor = Manager.objects.get(category='supervisor', users=user)
    log.debug('user:%s supervisor:%s', user, mgr_supervisor.user)
    return mgr_supervisor.user



# class route_to_secretary(object):
#     def __init__(self, workitem):
#         user = workitem.instance.user
#         self.mgr_secretary = Manager.objects.get(category='secretary', users=user)
#     def __call__(self):
#         return self.mgr_secretary.user
# 
# class route_to_supervisor(object):
#     def __init__(self, workitem):
#         user = workitem.instance.user
#         self.mgr_supervisor = Manager.objects.get(category='supervisor', users=user)
#         log.debug('user:%s supervisor:%s', user, self.mgr_supervisor.user)
#     def __call__(self):
#         return self.mgr_supervisor.user



