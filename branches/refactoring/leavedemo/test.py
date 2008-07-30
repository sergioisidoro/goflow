#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
TODO: this needs to be rewritten completely

'''

import  os, sys
os.environ["DJANGO_SETTINGS_MODULE"]="leavedemo.settings"
dirname, join = os.path.dirname, os.path.join

sys.path.insert(0, join(dirname(__file__), '..'))

from goflow.workflow.models import WorkItem

user = User.objects.get(username='admin')

