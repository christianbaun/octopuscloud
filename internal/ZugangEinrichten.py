#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from library import logins3
from library import xor_crypt_string

from internal.Datastore import *

from boto.ec2.connection import *

from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('simple.cfg')

class ZugangEinrichten(webapp.RequestHandler):
    def post(self):
        nameregion = self.request.get('nameregion')
        endpointurl = self.request.get('endpointurl')
        port = self.request.get('port')
        accesskey = self.request.get('accesskey')
        secretaccesskey = self.request.get('secretaccesskey')
        typ = self.request.get('typ')
        # Den Usernamen erfahren
        username = users.get_current_user()
        # self.response.out.write('posted!')

        if users.get_current_user():

          # Wenn ein EC2-Zugang angelegt werden soll
          if typ == "ec2":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              # Prüfen, ob die Zugangsdaten für EC2 korrekt sind
              try:
                # Zugangsdaten testen
                connection_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                                  aws_secret_access_key=secretaccesskey,
                                                  is_secure=False,
                                                  host="s3.amazonaws.com",
                                                  calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                                  path="/")
                # Wenn man die Liste der Buckets anfordern kann, dann waren die Zugangsdaten korrekt
                liste_buckets = connection_s3.get_all_buckets()
                
                
              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für S3 korrekt sind, dann wird hier weiter gemacht...

                # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
                laenge_liste_buckets = len(liste_buckets)

                # Get values from the config file
                # The name of the bucket that is used      
                # The character "@" cannot be used. Therefore we use "at".  
                bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at').replace('.', '-')
    
                # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
                schon_vorhanden = 0
                for i in range(laenge_liste_buckets):
                  # Bucket-Namen in einen String umwandeln
                  vergleich = str(liste_buckets[i].name)
                  # Vergleichen
                  if vergleich == bucketname:
                    # Bucket-Name existiert schon!
                    schon_vorhanden = 1
    
                if schon_vorhanden == 0:
                  # Wenn man noch keinen Bucket mit dem eingegebenen Namen besitzt...
                  try:
                    # Versuch den Bucket anzulegen
                    connection_s3.create_bucket(bucketname)
                  except:
                    fehlermeldung = "127"
                    # Wenn es nicht klappt...
                    self.redirect('/regionen?message='+fehlermeldung)
                  else:

                    # Wenn es geklappt hat...
                    
                    # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                    testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="Amazon")
                    # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                    results = testen.fetch(100)
                    for result in results:
                      result.delete()
    
                    secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                    secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                    logindaten = OctopusCloudDatenbank(regionname="Amazon",
                                                    eucalyptusname="Amazon",
                                                    accesskey=accesskey,
                                                    endpointurl="s3.amazonaws.com",
                                                    zugangstyp="Amazon",
                                                    secretaccesskey=secretaccesskey_base64encoded,
                                                    port=None,
                                                    user=username)
                    # In den Datastore schreiben
                    logindaten.put()
                    
                    fehlermeldung = "128"
                    self.redirect('/regionen?message='+fehlermeldung)
                    
                else:
                  # Wenn man schon einen Bucket mit dem eingegeben Namen hat...

                  testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="Amazon")
                  # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                  results = testen.fetch(100)
                  for result in results:
                    result.delete()
  
                  secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                  secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                  logindaten = OctopusCloudDatenbank(regionname="Amazon",
                                                  eucalyptusname="Amazon",
                                                  accesskey=accesskey,
                                                  endpointurl="s3.amazonaws.com",
                                                  zugangstyp="Amazon",
                                                  secretaccesskey=secretaccesskey_base64encoded,
                                                  port=None,
                                                  user=username)
                  # In den Datastore schreiben
                  logindaten.put()
                                    
                  fehlermeldung = "129"
                  self.redirect('/regionen?message='+fehlermeldung)


                #self.redirect('/regionen')














          # Wenn ein GoogleStorage-Zugang angelegt werden soll
          if typ == "googlestorage":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              # Prüfen, ob die Zugangsdaten für EC2 korrekt sind
              try:
                # Zugangsdaten testen
                connection_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                                  aws_secret_access_key=secretaccesskey,
                                                  is_secure=False,
                                                  host="commondatastorage.googleapis.com",
                                                  calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                                  path="/")
                # Wenn man die Liste der Buckets anfordern kann, dann waren die Zugangsdaten korrekt
                liste_buckets = connection_s3.get_all_buckets()
                
                
              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für S3 korrekt sind, dann wird hier weiter gemacht...

                # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
                laenge_liste_buckets = len(liste_buckets)

                # Get values from the config file
                # The name of the bucket that is used      
                # The character "@" cannot be used. Therefore we use "at".  
                bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at').replace('.', '-')
    
                # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
                schon_vorhanden = 0
                for i in range(laenge_liste_buckets):
                  # Bucket-Namen in einen String umwandeln
                  vergleich = str(liste_buckets[i].name)
                  # Vergleichen
                  if vergleich == bucketname:
                    # Bucket-Name existiert schon!
                    schon_vorhanden = 1
    
                if schon_vorhanden == 0:
                  # Wenn man noch keinen Bucket mit dem eingegebenen Namen besitzt...
#                  try:
#                    # Versuch den Bucket anzulegen
#                    connection_s3.create_bucket(bucketname)
#                  except:
#                    fehlermeldung = "127"
#                    # Wenn es nicht klappt...
#                    self.redirect('/regionen?message='+fehlermeldung)
#                  else:

                    # Versuch den Bucket anzulegen
                    connection_s3.create_bucket(bucketname)
                    
                    # Wenn es geklappt hat...
                    
                    # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                    testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="GoogleStorage")
                    # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                    results = testen.fetch(100)
                    for result in results:
                      result.delete()
    
                    secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                    secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                    logindaten = OctopusCloudDatenbank(regionname="GoogleStorage",
                                                eucalyptusname="GoogleStorage",
                                                accesskey=accesskey,
                                                endpointurl="commondatastorage.googleapis.com",
                                                zugangstyp="GoogleStorage",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
    
                    # In den Datastore schreiben
                    logindaten.put()
                    
                    fehlermeldung = "128"
                    self.redirect('/regionen?message='+fehlermeldung)
                    
                else:
                  # Wenn man schon einen Bucket mit dem eingegeben Namen hat...

                  testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="GoogleStorage")
                  # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                  results = testen.fetch(100)
                  for result in results:
                    result.delete()
  
                  secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                  secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                  logindaten = OctopusCloudDatenbank(regionname="GoogleStorage",
                                                  eucalyptusname="GoogleStorage",
                                                  accesskey=accesskey,
                                                  endpointurl="commondatastorage.googleapis.com",
                                                  zugangstyp="GoogleStorage",
                                                  secretaccesskey=secretaccesskey_base64encoded,
                                                  port=None,
                                                  user=username)
                  # In den Datastore schreiben
                  logindaten.put()
                                    
                  fehlermeldung = "129"
                  self.redirect('/regionen?message='+fehlermeldung)


                #self.redirect('/regionen')













          # Wenn ein Eucalyptus-Zugang angelegt werden soll
          else:
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                region = RegionInfo(name=nameregion, endpoint=endpointurl)
                connection_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        host=endpointurl,
                                        port=int(port),
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                        path="/services/Walrus")

                # Wenn man die Liste der Buckets anfordern kann, dann waren die Zugangsdaten korrekt
                liste_buckets = connection_s3.get_all_buckets()
                 
              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Walrus (Eucalyptus) korrekt sind, dann wird hier weiter gemacht...

                laenge_liste_buckets = len(liste_buckets)

                # Get values from the config file
                # The name of the bucket that is used      
                # The character "@" cannot be used. Therefore we use "at".  
                bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at').replace('.', '-')
    
                # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
                schon_vorhanden = 0
                for i in range(laenge_liste_buckets):
                  # Bucket-Namen in einen String umwandeln
                  vergleich = str(liste_buckets[i].name)
                  # Vergleichen
                  if vergleich == bucketname:
                    # Bucket-Name existiert schon!
                    schon_vorhanden = 1
    
                if schon_vorhanden == 0:
                  # Wenn man noch keinen Bucket mit dem eingegebenen Namen besitzt...
                  try:
                    # Versuch den Bucket anzulegen
                    connection_s3.create_bucket(bucketname)
                  except:
                    fehlermeldung = "127"
                    # Wenn es nicht klappt...
                    self.redirect('/regionen?message='+fehlermeldung)
                  else:

                    # Wenn es geklappt hat...
       
                    # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                    testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="eucalyptus", eucalyptusname_db=nameregion)
                    # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                    results = testen.fetch(100)
                    for result in results:
                      result.delete()
    
                    secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                    secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                    logindaten = OctopusCloudDatenbank(regionname="Eucalyptus",
                                                    eucalyptusname=nameregion,
                                                    accesskey=accesskey,
                                                    endpointurl=endpointurl,
                                                    zugangstyp="Eucalyptus",
                                                    secretaccesskey=secretaccesskey_base64encoded,
                                                    port=str(port),
                                                    user=username)
                    # In den Datastore schreiben
                    logindaten.put()
    
                    fehlermeldung = "128"
                    self.redirect('/regionen?message='+fehlermeldung)
                    
                else:
                  # Wenn man schon einen Bucket mit dem eingegeben Namen hat...

                  testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="eucalyptus", eucalyptusname_db=nameregion)
                  # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                  results = testen.fetch(100)
                  for result in results:
                    result.delete()
  
                  secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                  secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                  logindaten = OctopusCloudDatenbank(regionname="Eucalyptus",
                                                    eucalyptusname=nameregion,
                                                    accesskey=accesskey,
                                                    endpointurl=endpointurl,
                                                    zugangstyp="Eucalyptus",
                                                    secretaccesskey=secretaccesskey_base64encoded,
                                                    port=str(port),
                                                    user=username)
                  # In den Datastore schreiben
                  logindaten.put()
                                    
                  fehlermeldung = "129"
                  self.redirect('/regionen?message='+fehlermeldung)
                

                
        else:
            self.redirect('/')