#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp


class ZugangEntfernen(webapp.RequestHandler):
    def get(self):
        region = self.request.get('region')
        endpointurl = self.request.get('endpointurl')
        accesskey = self.request.get('accesskey')
        # Den Usernamen erfahren
        username = users.get_current_user()

      
        testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND endpointurl = :endpointurl_db AND accesskey = :accesskey_db", username_db=username, regionname_db=region, endpointurl_db=endpointurl, accesskey_db=accesskey)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        self.redirect('/regionen')
        