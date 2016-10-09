#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

class OctopusCloudDatenbank(db.Model):
    user = db.UserProperty(required=True)
    #input = db.IntegerProperty()
    regionname = db.StringProperty()
    endpointurl = db.StringProperty()
    port = db.StringProperty()
    eucalyptusname = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...
    accesskey = db.StringProperty(required=True)
    secretaccesskey = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

class OctopusCloudDatenbankAktiveZone(db.Model):
    user = db.UserProperty(required=True)
    aktivezone = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...

class OctopusCloudDatenbankSprache(db.Model):
    user = db.UserProperty(required=True)
    sprache = db.StringProperty()
