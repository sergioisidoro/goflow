#!/usr/bin/env python
from django.contrib import admin
from goflow.workflow.models import (Activity, Process, Application,
                                    PushApplication, Transition, UserProfile,
                                    ProcessInstance, WorkItem, Event,
                                    DefaultAppModel)

class ActivityAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('title', 'description', 'kind', 'application', 'join_mode',
                    'split_mode', 'autostart', 'autofinish', 'process')
    list_filter = ('process', 'kind')
admin.site.register(Activity, ActivityAdmin)

class TransitionInline(admin.TabularInline):
    model = Transition
    extra=1

class ProcessAdmin(admin.ModelAdmin):
    list_display = ('title', 'action', 'enabled', 'description')
    inlines = [TransitionInline]
admin.site.register(Process, ProcessAdmin)

class ApplicationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('url','test')
admin.site.register(Application, ApplicationAdmin)

class PushApplicationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('url','test')
admin.site.register(PushApplication, PushApplicationAdmin)

class TransitionAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'input', 'output', 'condition', 'description',
                    'process')
    list_filter = ('process',)
admin.site.register(Transition, TransitionAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'web_host', 'notified', 'last_notif',
                    'nb_wi_notif', 'notif_delay')
    list_filter = ('web_host', 'notified')
admin.site.register(UserProfile, UserProfileAdmin)

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


