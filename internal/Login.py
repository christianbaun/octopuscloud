#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from internal.Datastore import *

class Login(webapp.RequestHandler):
    def post(self):
        cloud_region = self.request.get('cloud_region')
        endpointurl = self.request.get('endpointurl')
        accesskey = self.request.get('accesskey')
        secretaccesskey = self.request.get('secretaccesskey')
        if cloud_region == "Amazon EC2 EU West":
          regionname = "eu-west-1"
        if cloud_region == "Amazon EC2 US East":
          regionname = "us-east-1"
        if cloud_region == "Amazon EC2 US West":
          regionname = "us-west-1"
        if cloud_region == "Amazon EC2 Asia Pacific":
          regionname = "ap-southeast-1"
        if cloud_region == "Eucalyptus":
          regionname = "eucalyptus"


        if cloud_region == "Amazon EC2 EU West" or cloud_region == "Amazon EC2 US East" or cloud_region == "Amazon EC2 US West" or cloud_region == "Amazon EC2 Asia Pacific":
          conn_region = boto.ec2.connect_to_region(regionname,
                                                   aws_access_key_id=accesskey,
                                                   aws_secret_access_key=secretaccesskey,
                                                   is_secure = False)
#        if cloud_region == "Eualyptus":
#          conn_region = boto.connect_ec2(aws_access_key_id=accesskey,
#                                         aws_secret_access_key=secretaccesskey,
#                                         is_secure=False,
#                                         region=RegionInfo(name="eucalyptus", endpoint=endpointurl),
#                                         port=8773,
#                                         path="/services/Eucalyptus")
          




        # Den Usernamen erfahren
        username = users.get_current_user()

        # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
        testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db ", username_db=username, regionname_db=regionname)
        # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
        results = testen.fetch(100)
        for result in results:
          result.delete()

        # Festlegen, was in den Datastore geschrieben werden soll
        logindaten = KoalaCloudDatenbank(regionname=regionname,
                                         accesskey=accesskey,
                                         endpointurl=endpointurl,
                                         secretaccesskey=secretaccesskey,
                                         user=username)
        # In den Datastore schreiben
        logindaten.put()   

        self.redirect('/')
