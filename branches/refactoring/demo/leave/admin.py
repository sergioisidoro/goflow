#!/usr/bin/env python

from django.contrib import admin
from demo.leave.models import LeaveRequest, Manager, Account
from goflow.tools import admin_register

class LeaveRequestAdmin(admin.ModelAdmin):
    fieldsets = (
              (None, {'fields':(('day_start', 'day_end'), 'type', 'requester',
                      'reason', 'reason_denial')}),
              )
    list_display = ('type', 'date', 'day_start', 'day_end', 'requester')
    list_filter = ('type', 'requester')

class ManagerAdmin(admin.ModelAdmin):
    pass

class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'days')

# register admin classes
admin_register(admin, globals())