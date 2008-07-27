#!/usr/bin/env python

from django.contrib import admin
from leavedemo.leave.models import LeaveRequest, Manager, Account

#from goflow.utils.logger import register_admin

#_models = ['LeaveRequest', 'Manager', 'Account']

class LeaveRequestAdmin(admin.ModelAdmin):
    fieldsets = (
              (None, {'fields':(('day_start', 'day_end'), 'type', 'requester',
                      'reason', 'reason_denial')}),
              )
    list_display = ('type', 'date', 'day_start', 'day_end', 'requester')
    list_filter = ('type', 'requester')
admin.site.register(LeaveRequest, LeaveRequestAdmin)

class ManagerAdmin(admin.ModelAdmin):
    pass
admin.site.register(Manager, ManagerAdmin)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'days')
admin.site.register(Account, AccountAdmin)

#for model in _models:    
#    register_admin('leavedemo.leave.models', model)
    