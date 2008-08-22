#!/usr/bin/env python
from django.contrib import admin
from goflow.workflow.models import (Activity, Process, Application,
                                    PushApplication, Transition, UserProfile)

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

# register models for admin
for m in [Activity, Process, Application, PushApplication, Transition, UserProfile]:
    admin.site.register(m)

