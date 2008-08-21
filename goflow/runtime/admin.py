#!/usr/bin/env python

from django.contrib import admin
from goflow.runtime.models import (ProcessInstance, WorkItem, Event,
                                    DefaultAppModel)


class ProcessInstanceAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_time'
    list_display = ('title', 'process', 'user', 'creation_time', 'status')
    list_filter = ('process', 'user')
admin.site.register(ProcessInstance, ProcessInstanceAdmin)

class WorkItemAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'user', 'instance', 'activity', 'status')
    list_filter = ('user', 'activity', 'status')
admin.site.register(WorkItem, WorkItemAdmin)

class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'name', 'workitem')
admin.site.register(Event, EventAdmin)


class DefaultAppModelAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',)
admin.site.register(DefaultAppModel, DefaultAppModelAdmin)


