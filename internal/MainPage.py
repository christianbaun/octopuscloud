#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import logins3
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import format_error_message_green
from library import format_error_message_red

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *

class MainPage(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        if users.get_current_user():
            hint = '&nbsp;'     

            # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
            # See if a language has already been chosen 
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache)
            
            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'
            
            # Nachsehen, ob schon Zugansdaten eingegeben wurden
            zugansdaten_vorhanden = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
            results = zugansdaten_vorhanden.fetch(100)
            if not results:
              # If the user has still no credentials for cloud storage services
              if sprache == "de":
                hint = '<font color="red"><b>Sie m&uuml;ssen nun ihre Zugangsdaten einrichten</b></font>'            
              else:
                hint = '<font color="red"><b>Now, you need to configure your Credentials</b></font>'     
            else:
              hint = ''

        else:
            # If the user is not logged in or has no account yet...
            sprache = "en"
            navigations_bar = navigations_bar_funktion(sprache)
            url = users.create_login_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Login'
            
            hint = '<font color="red"><b><=== You need to login first with your Google account!</b></font>'

        template_values = {
        'navigations_bar': navigations_bar,
        'url': url,
        'url_linktext': url_linktext,
        'hint': hint,
        }

        path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "start.html")
        self.response.out.write(template.render(path,template_values))

