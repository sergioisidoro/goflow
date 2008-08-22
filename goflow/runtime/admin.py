#!/usr/bin/env python

from django.contrib import admin
from goflow.runtime.models import (ProcessInstance, WorkItem, Event,
                                    DefaultAppModel)


class ProcessInstanceAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_time'
    list_display = ('title', 'process', 'user', 'creation_time', 'status')
    list_filter = ('process', 'user')

class WorkItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'user', 'instance', 'activity', 'status')
    list_filter = ('user', 'activity', 'status')

class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'name', 'workitem')

class DefaultAppModelAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',)


# register models for admin
for m in [ProcessInstance, WorkItem, Event, DefaultAppModel]:
    admin.site.register(m)

