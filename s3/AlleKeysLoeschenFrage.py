#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import format_error_message_green
from library import format_error_message_red

from dateutil.parser import *

from error_messages import error_messages

class AlleKeysLoeschenFrage(webapp.RequestHandler):
    def get(self):
        # Get the username
        username = users.get_current_user()
        if not username:
          # If no user is logged in, jump back to root
          self.redirect('/')

        # Datastore query that checks if any credentials for this user exist
        testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
            
        results = testen.fetch(100)

        if not results:
          # If no credentials exist, jump back to root
          self.redirect('/')
        else:
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'


          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          }

          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "alle_keys_loeschen_frage.html")
          self.response.out.write(template.render(path,template_values))

