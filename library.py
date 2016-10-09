#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from boto.ec2.connection import *
from boto.ec2 import *
from boto.s3.connection import *
from boto.s3 import *
from dateutil.parser import *
from dateutil.tz import *
from datetime import *
# this is needed for the encyption
from itertools import izip, cycle
import hmac, sha
# this is needed for the encyption
import base64


from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('simple.cfg')


from internal.Datastore import *





def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))


def aktuelle_sprache(username):
    # Is there an entry for the user that shows that he has already chosen a language?
    spracheanfrage = db.GqlQuery("SELECT * FROM OctopusCloudDatenbankSprache WHERE user = :username_db", username_db=username)
    ergebnisse = spracheanfrage.fetch(10)

    if not ergebnisse:
        logindaten = OctopusCloudDatenbankSprache(sprache="en",
                                              user=username)
        logindaten.put()   # Write into datastore
        spracheanfrage = db.GqlQuery("SELECT * FROM OctopusCloudDatenbankSprache WHERE user = :username_db", username_db=username)
        ergebnisse = spracheanfrage.fetch(10)

    for ergebnis in ergebnisse:
        if ergebnis.sprache == "en":
            sprache = "en"
        elif ergebnis.sprache == "de":
            sprache = "de"
        else:
            sprache = "en"

    return sprache
  
  
def navigations_bar_funktion(sprache):
  if sprache == "de":
      navigations_bar = '&nbsp; \n'
      navigations_bar = navigations_bar + '<a href="/regionen" title="Zugansdaten">Zugansdaten</a> | \n'
      navigations_bar = navigations_bar + '<a href="/s3" title="Ihre Daten">Ihre Daten</a> | \n'
      navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
  else:
      navigations_bar = '&nbsp; \n'
      navigations_bar = navigations_bar + '<a href="/regionen" title="Credentials">Credentials</a> | \n'
      navigations_bar = navigations_bar + '<a href="/s3" title="Your Data">Your Data</a> | \n'
      navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
  return navigations_bar


  
  

# Helper function for formating the error messages
def format_error_message_green(input_error_message):
    if input_error_message:
        return "<p>&nbsp;</p> <font color='green'>%s</font>" % (input_error_message)
    else:
        return ""

# Helper function for formating the error messages
def format_error_message_red(input_error_message):
    if input_error_message:
        return "<p>&nbsp;</p> <font color='red'>%s</font>" % (input_error_message)
    else:
        return ""
      

def logins3(username, aktuellezone):
  if aktuellezone == "Amazon":
    # Die Zugangsdaten des Benutzers holen
    zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Amazon")
    aktuellezone = "Amazon"
    regionname = "Amazon"

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      port = db_eintrag.port

    secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
    secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
    conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=True,
                                        host="s3.amazonaws.com",
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                        path="/")

  elif aktuellezone == "GoogleStorage":
    # Die Zugangsdaten des Benutzers holen
    zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="GoogleStorage")
    aktuellezone = "GoogleStorage"
    regionname = "GoogleStorage"

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      #port = db_eintrag.port

    secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
    secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
    conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=True,
                                        host="commondatastorage.googleapis.com",
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                        path="/")

  else:
  # aktuellezone == "Eucalyptus":
    zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Eucalyptus")
    aktuellezone = "Eucalyptus"
    regionname = "Eucalyptus"

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      port = db_eintrag.port

    secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
    secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
    conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        host=endpointurl,
                                        port=int(port),
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                        path="/services/Walrus")

  return conn_s3, regionname

def aws_access_key_erhalten(username,eucalyptusname):
  Anfrage_nach_AWSAccessKeyId = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user =  :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
  for db_eintrag in Anfrage_nach_AWSAccessKeyId:
    AWSAccessKeyId = db_eintrag.accesskey

  return AWSAccessKeyId

def aws_secret_access_key_erhalten(username,eucalyptusname):
  Anfrage_nach_AWSSecretAccessKeyId = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user =  :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
  for db_eintrag in Anfrage_nach_AWSSecretAccessKeyId:
    AWSSecretAccessKeyId = db_eintrag.secretaccesskey
    secretaccesskey_base64decoded = base64.b64decode(str(AWSSecretAccessKeyId))
    AWSSecretAccessKeyId = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))

  return AWSSecretAccessKeyId

def endpointurl_erhalten(username,eucalyptusname):
  Anfrage_nach_endpointurl = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
  for db_eintrag in Anfrage_nach_endpointurl:
    endpointurl = db_eintrag.endpointurl

  return endpointurl


def port_erhalten(username,eucalyptusname):
  Anfrage_nach_port = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
  for db_eintrag in Anfrage_nach_port:
    port = db_eintrag.port

  return port


def get_second_list(username,eucalyptusname,aktuellezone):
    if aktuellezone == "Amazon":
      # It is Amazon S3 ... so we need to connect with Google Storage
      Anfrage_nach_zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname != :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
      for db_eintrag in Anfrage_nach_zugangsdaten:
        accesskey = db_eintrag.accesskey
        secretaccesskey = db_eintrag.secretaccesskey
        endpointurl = db_eintrag.endpointurl
        port = db_eintrag.port
  
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                          aws_secret_access_key=secretaccesskey,
                                          is_secure=True,
                                          host="commondatastorage.googleapis.com",
                                          calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                          path="/")
      

      
      # Get values from the config file
      # The name of the bucket that is used      
      # The character "@" cannot be used. Therefore we use "at".  
      bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at').replace('.', '-')
      
      try:
        # Connect with bucket
        bucket_instance = conn_s3.get_bucket(bucketname)
      except:
        # When it didn't work
        if sprache == "de":
          bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
        else:
          bucket_keys_tabelle = '<font color="red">An error occured</font>'
        laenge_liste_keys = 0
      else:
        # When it worked...
        try:
          # Get a list of all keys inside the bucket
          liste_keys = bucket_instance.get_all_keys()
        except:
          # When it didn't work
          if sprache == "de":
            bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
          else:
            bucket_keys_tabelle = '<font color="red">An error occured</font>'
          laenge_liste_keys = 0
        else:
          # When it worked...
          # Number of keys inside the list
          laenge_liste_keys = len(liste_keys)
          
          # When using Walrus (Eucalyptus), we need to erase the stupid "None" entry.
#          if aktuellezone != "Amazon":
#            liste_keys2 = []
#            for i in range(laenge_liste_keys):
#              if str(liste_keys[i].name) != 'None':
#                liste_keys2.append(liste_keys[i])
#            laenge_liste_keys2 = len(liste_keys2)
#            laenge_liste_keys = laenge_liste_keys2
#            liste_keys = liste_keys2
            
          # If we have keys inside the bucket, we need to create a list that contains the MD5 checksums
          if laenge_liste_keys == 0:
            # Create an empty List
            Main_Liste = []
            Second_list = Main_Liste  
          else:
            # if laenge_liste_keys is not 0
            # Create an empty List
            Main_Liste = [] 
            # Walk through the list of keys
            for i in range(laenge_liste_keys):
              # In S3 each MD5 checksum is enclosed by double quotes. In Walrus they are not
              Main_Liste.append(str(liste_keys[i].etag).replace('"',''))
            # Sort the List
            Main_Liste.sort()
            Second_list = Main_Liste
            
            
    else:
      # It is Google Storage ... so we need to connect with Amazon S3
      Anfrage_nach_zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname != :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
      for db_eintrag in Anfrage_nach_zugangsdaten:
        accesskey = db_eintrag.accesskey
        secretaccesskey = db_eintrag.secretaccesskey
        endpointurl = db_eintrag.endpointurl
        port = db_eintrag.port   

      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=True,
                                        host="s3.amazonaws.com",
                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                        path="/")

      # The name of the bucket that is used      
      # The character "@" cannot be used. Therefore we use "at".  
      bucketname = 'octopus_storage_'+str(username).replace('@', 'at').replace('.', '-')
      
      try:
        # Connect with bucket
        bucket_instance = conn_s3.get_bucket(bucketname)
      except:
        # When it didn't work
        if sprache == "de":
          bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
        else:
          bucket_keys_tabelle = '<font color="red">An error occured</font>'
        laenge_liste_keys = 0
      else:
        # When it worked...
        try:
          # Get a list of all keys inside the bucket
          liste_keys = bucket_instance.get_all_keys()
        except:
          # When it didn't work
          if sprache == "de":
            bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
          else:
            bucket_keys_tabelle = '<font color="red">An error occured</font>'
          laenge_liste_keys = 0
        else:
          # When it worked...
          # Number of keys inside the list
          laenge_liste_keys = len(liste_keys)
      
          # When using Walrus (Eucalyptus), we need to erase the stupid "None" entry.
#          if aktuellezone != "Amazon":
#            liste_keys2 = []
#            for i in range(laenge_liste_keys):
#              if str(liste_keys[i].name) != 'None':
#                liste_keys2.append(liste_keys[i])
#            laenge_liste_keys2 = len(liste_keys2)
#            laenge_liste_keys = laenge_liste_keys2
#            liste_keys = liste_keys2
            
          # If we have keys inside the bucket, we need to create a list that contains the MD5 checksums
          if laenge_liste_keys == 0:
            # Create an empty List
            Main_Liste = []
            Second_list = Main_Liste  
          else:
            # if laenge_liste_keys is not 0
            # Create an empty List
            Main_Liste = [] 
            # Walk through the list of keys
            for i in range(laenge_liste_keys):
              # In S3 each MD5 checksum is enclosed by double quotes. In Walrus they are not
              Main_Liste.append(str(liste_keys[i].etag).replace('"',''))
            # Sort the List
            Main_Liste.sort()
            Second_list = Main_Liste
            
            
            
#    if aktuellezone == "Amazon":
#      # It is Amazon S3 ... so we need to connect with Walrus (Eucalyptus)
#      Anfrage_nach_zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname != :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
#      for db_eintrag in Anfrage_nach_zugangsdaten:
#        accesskey = db_eintrag.accesskey
#        secretaccesskey = db_eintrag.secretaccesskey
#        endpointurl = db_eintrag.endpointurl
#        port = db_eintrag.port
#  
#      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
#      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
#      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
#                                          aws_secret_access_key=secretaccesskey,
#                                          is_secure=False,
#                                          host=endpointurl,
#                                          port=int(port),
#                                          calling_format=boto.s3.connection.OrdinaryCallingFormat(),
#                                          path="/services/Walrus")
#      
#      # Get values from the config file
#      # The name of the bucket that is used      
#      # The character "@" cannot be used. Therefore we use "at".  
#      bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at')
#      
#      try:
#        # Connect with bucket
#        bucket_instance = conn_s3.get_bucket(bucketname)
#      except:
#        # When it didn't work
#        if sprache == "de":
#          bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
#        else:
#          bucket_keys_tabelle = '<font color="red">An error occured</font>'
#        laenge_liste_keys = 0
#      else:
#        # When it worked...
#        try:
#          # Get a list of all keys inside the bucket
#          liste_keys = bucket_instance.get_all_keys()
#        except:
#          # When it didn't work
#          if sprache == "de":
#            bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
#          else:
#            bucket_keys_tabelle = '<font color="red">An error occured</font>'
#          laenge_liste_keys = 0
#        else:
#          # When it worked...
#          # Number of keys inside the list
#          laenge_liste_keys = len(liste_keys)
#          
#          # When using Walrus (Eucalyptus), we need to erase the stupid "None" entry.
#          if aktuellezone != "Amazon":
#            liste_keys2 = []
#            for i in range(laenge_liste_keys):
#              if str(liste_keys[i].name) != 'None':
#                liste_keys2.append(liste_keys[i])
#            laenge_liste_keys2 = len(liste_keys2)
#            laenge_liste_keys = laenge_liste_keys2
#            liste_keys = liste_keys2
#            
#          # If we have keys inside the bucket, we need to create a list that contains the MD5 checksums
#          if laenge_liste_keys == 0:
#            # Create an empty List
#            Main_Liste = []
#            Second_list = Main_Liste  
#          else:
#            # if laenge_liste_keys is not 0
#            # Create an empty List
#            Main_Liste = [] 
#            # Walk through the list of keys
#            for i in range(laenge_liste_keys):
#              # In S3 each MD5 checksum is enclosed by double quotes. In Walrus they are not
#              Main_Liste.append(str(liste_keys[i].etag).replace('"',''))
#            # Sort the List
#            Main_Liste.sort()
#            Second_list = Main_Liste
            
#    else:
#      # It is Walrus (Eucalyptus) ... so we need to connect with Amazon S3
#      Anfrage_nach_zugangsdaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND eucalyptusname != :eucalyptusname_db", username_db=username, eucalyptusname_db=eucalyptusname)
#      for db_eintrag in Anfrage_nach_zugangsdaten:
#        accesskey = db_eintrag.accesskey
#        secretaccesskey = db_eintrag.secretaccesskey
#        endpointurl = db_eintrag.endpointurl
#        port = db_eintrag.port   
#
#      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
#      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
#      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
#                                        aws_secret_access_key=secretaccesskey,
#                                        is_secure=True,
#                                        host="s3.amazonaws.com",
#                                        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
#                                        path="/")
#
#      # The name of the bucket that is used      
#      # The character "@" cannot be used. Therefore we use "at".  
#      bucketname = 'octopus_storage_'+str(username).replace('@', 'at')
#      
#      try:
#        # Connect with bucket
#        bucket_instance = conn_s3.get_bucket(bucketname)
#      except:
#        # When it didn't work
#        if sprache == "de":
#          bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
#        else:
#          bucket_keys_tabelle = '<font color="red">An error occured</font>'
#        laenge_liste_keys = 0
#      else:
#        # When it worked...
#        try:
#          # Get a list of all keys inside the bucket
#          liste_keys = bucket_instance.get_all_keys()
#        except:
#          # When it didn't work
#          if sprache == "de":
#            bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
#          else:
#            bucket_keys_tabelle = '<font color="red">An error occured</font>'
#          laenge_liste_keys = 0
#        else:
#          # When it worked...
#          # Number of keys inside the list
#          laenge_liste_keys = len(liste_keys)
#      
#          # When using Walrus (Eucalyptus), we need to erase the stupid "None" entry.
#          if aktuellezone != "Amazon":
#            liste_keys2 = []
#            for i in range(laenge_liste_keys):
#              if str(liste_keys[i].name) != 'None':
#                liste_keys2.append(liste_keys[i])
#            laenge_liste_keys2 = len(liste_keys2)
#            laenge_liste_keys = laenge_liste_keys2
#            liste_keys = liste_keys2
#            
#          # If we have keys inside the bucket, we need to create a list that contains the MD5 checksums
#          if laenge_liste_keys == 0:
#            # Create an empty List
#            Main_Liste = []
#            Second_list = Main_Liste  
#          else:
#            # if laenge_liste_keys is not 0
#            # Create an empty List
#            Main_Liste = [] 
#            # Walk through the list of keys
#            for i in range(laenge_liste_keys):
#              # In S3 each MD5 checksum is enclosed by double quotes. In Walrus they are not
#              Main_Liste.append(str(liste_keys[i].etag).replace('"',''))
#            # Sort the List
#            Main_Liste.sort()
#            Second_list = Main_Liste
#            
    return Second_list