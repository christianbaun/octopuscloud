#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from internal.Datastore import *

class RegionWechseln(webapp.RequestHandler):
    def post(self):
        # Zum Testen, ob das "post" geklappt hat
        #self.response.out.write('posted!')
        # Die ausgewählte Region holen
        regionen = self.request.get('regionen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        suchen = ""
        if 'US East' in regionen:
          zone = "us-east-1"
          zugangstyp = "Amazon"
        elif 'US West' in regionen:
          zone = "us-west-1"
          zugangstyp = "Amazon"
        elif 'EU West' in regionen:
          zone = "eu-west-1"
          zugangstyp = "Amazon"
        elif 'Asia Pacific' in regionen:
          zone = "ap-southeast-1"
          zugangstyp = "Amazon"
        else:
          zone = regionen
          zugangstyp = "keinAmazon"

        # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        if zugangstyp == "keinAmazon":
          testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionen_db", username_db=username, regionen_db=regionen)
          results = testen.fetch(100) # Einträge holen

          for result in results:
            zugangstyp = result.zugangstyp


        logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=zone,
                                                   user=username,
                                                   zugangstyp=zugangstyp)

        try:
          # In den Datastore schreiben
          # Write into the Datastore
          logindaten.put()
        except:
          # Wenn es nicht klappt...
          # It it didn't work...
          self.redirect('/')
        else:
          # Wenn es geklappt hat...
          # If it worked...
          self.redirect('/')

