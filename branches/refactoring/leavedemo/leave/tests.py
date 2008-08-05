#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client

class Test(TestCase):
    def test_home_anonymous(self):
        client = Client()
        response = client.get('/leave/')
        self.failUnlessEqual(response.status_code, 200)
        
    def test_otherswork_anonymous(self):
        "TODO: should be also be tested with proper authentication!"
        client = Client()
        response = client.get('/leave/otherswork/', {'worker':'primus'})
        self.failUnlessEqual(response.status_code, 302)
        response = client.get('/leave/otherswork/', {'worker':'secundus'})
        self.failUnlessEqual(response.status_code, 302)
        response = client.get('/leave/otherswork/', {'worker':'tertius'})
        self.failUnlessEqual(response.status_code, 302)
 
    def test_details(self):
        client = Client()
        ok = client.login(username='primus', password='bad_passwd')
        self.assertFalse(ok, 'authentication not ok')
        ok = client.login(username='primus', password='p')
        self.assertTrue(ok, 'authentication ok')
        
        ok = client.login(username='admin', password='open')
        self.assertTrue(ok, 'authentication ok')
        response = client.get('/leave/admin/')
        self.failUnlessEqual(response.status_code, 200)
        client.logout()
  