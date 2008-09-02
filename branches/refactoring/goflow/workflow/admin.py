#!/usr/bin/env python
from django.contrib import admin
from goflow.workflow.models import (Activity, Process, Application,
                                    PushApplication, Transition, UserProfile,
                                    ProcessInstance, WorkItem, Event,
                                    DefaultAppModel)
from goflow.tools import admin_register

class ActivityAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('title', 'description', 'kind', 'application', 'join_mode',
                    'split_mode', 'autostart', 'autofinish', 'process')
    list_filter = ('process', 'kind')

class TransitionInline(admin.TabularInline):
    model = Transition
    extra=1

class ProcessAdmin(admin.ModelAdmin):
    list_display = ('title', 'action', 'enabled', 'description')
    inlines = [TransitionInline]

class ApplicationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('url','test')

class PushApplicationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('url','test')

class TransitionAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'input', 'output', 'condition', 'description',
                    'process')
    list_filter = ('process',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'web_host', 'notified', 'last_notif',
                    'nb_wi_notif', 'notif_delay')
    list_filter = ('web_host', 'notified')

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

# register admin classes
admin_register(admin, globals())






