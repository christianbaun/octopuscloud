#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from internal.Sprache import *
from internal.Datastore import *

class PersoenlicheDatanLoeschen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        aktivezone = db.GqlQuery("SELECT * FROM OctopusCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = aktivezone.fetch(100)
        for result in results:
          result.delete()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        sprache = db.GqlQuery("SELECT * FROM OctopusCloudDatenbankSprache WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = sprache.fetch(100)
        for result in results:
          result.delete()

        # Überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        self.redirect('/')