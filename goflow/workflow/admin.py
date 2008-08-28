#!/usr/bin/env python
from django.contrib import admin
from goflow.workflow.models import (Activity, Process, Application,
                                    PushApplication, Transition, UserProfile)

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

