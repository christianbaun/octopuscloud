#!/usr/bin/env python

import os
import re
import hmac, sha
# this is needed for the encyption
import base64
# Configuration file


from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten
from library import endpointurl_erhalten
from library import port_erhalten
from library import get_second_list


from dateutil.parser import *

from error_messages import error_messages

# this is needed for the encyption
from itertools import izip, cycle

from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('simple.cfg')




class S3(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
       
        # Get username
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Get error messages if any exist
        message = self.request.get('message')

        # Datastore query that checks if any credentials for this user exist
        testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
            
        # How many entries of this user exist?
        anzahl = testen.count()     
            
        # Get the result of your datastore query    
        results = testen.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Datastore query that checks if credentials for Amazon S3 exist
          testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Amazon")
          # Get the result of your datastore query 
          results = testen.fetch(100)
          if results:
            # If credentials for Amazon S3 exist
            aktuellezone = "Amazon"
            eucalyptusname = "Amazon"
          else:
            # No credentials for Amazon S3 exist
            # Datastore query that checks if credentials for a Walrus (Eucalyptus) Private Cloud exist
            testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Eucalyptus")
            # Get the result of your datastore query 
            results = testen.fetch(100)
             
            if results:
              # If credentials for an Walrus (Eucalyptus) Private Cloud exist
              aktuellezone = "Eucalyptus"
              # Get the credentials for the Walrus (Eucalyptus) Private Cloud
              anzahl = testen.count()   
              for test in results:
                eucalyptusname = str(test.eucalyptusname)
                
            else:
              # If no Walrus (Eucalyptus) credentials are given, we jump back to the root window
              self.redirect('/')
          

          
          # Get the language of the user
          sprache = aktuelle_sprache(username)
          # Generate the navigations bar
          navigations_bar = navigations_bar_funktion(sprache)



          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          # If the language is not set to german, it is set here to english
          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # If no error messages exist, the result here is "None".
          if input_error_message == None:
            input_error_message = ""

          # These error messages are formated in green...
          if message in ("111", "118", "120"):
            # This helper function formats in green
            input_error_message = format_error_message_green(input_error_message)
          # These error messages are formated in red...
          elif message in ("112", "119", "121"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""


          # Get Access Kkey for storage service that is used to display the list of keys 
          AWSAccessKeyId = aws_access_key_erhalten(username,eucalyptusname)
          # Get Secret Access Key for storage service that is used to display the list of keys
          AWSSecretAccessKeyId = aws_secret_access_key_erhalten(username,eucalyptusname)
        
          
          # Connect with storage service
          conn_s3, regionname = logins3(username, aktuellezone)
          
          
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

          
          # If we have more than one storage services, we need to compare the MD5 checksums
          if anzahl > 1:
            # If we have keys inside the bucket, we need to create a list that contains the MD5 checksums
            if laenge_liste_keys == 0:
              # Create an empty List
              Main_Liste = []
              # Length of the List
              Main_Liste_laenge = len(Main_Liste)  
              Second_list = get_second_list(username, aktuellezone, eucalyptusname)
              Second_list_laenge = len(Second_list)
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
              # Length of the List
              Main_Liste_laenge = len(Main_Liste)    
              Second_list = get_second_list(username, aktuellezone, eucalyptusname)
              Second_list_laenge = len(Second_list)

              
#              self.response.out.write(Main_Liste)
#              self.response.out.write(Main_Liste_laenge)                  
#              self.response.out.write(Second_list)
#              self.response.out.write(Second_list_laenge)  

                
          if laenge_liste_keys == 0:
            # No keys have been imported yet!
            if sprache == "de":
              bucket_keys_tabelle = 'Sie haben noch keine Dateien importiert.'
            else:
              bucket_keys_tabelle = 'No keys have been imported yet.'
          else:
            # There are keys in the bucket
            bucket_keys_tabelle = ''
            bucket_keys_tabelle = bucket_keys_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
            bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
            bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;&nbsp;&nbsp;</th>'
            bucket_keys_tabelle = bucket_keys_tabelle + '<th>&nbsp;&nbsp;&nbsp;</th>'
            if sprache == "de":
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Keys</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Dateigr&ouml;&szlig;e</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Letzte &Auml;nderung</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Zugriffsberechtigung</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Pr&uuml;fsumme (MD5)</th>'
            else:
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="left">Keys</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Filesize</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Last Modified</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">Access Control List</th>'
              bucket_keys_tabelle = bucket_keys_tabelle + '<th align="center">MD5</th>'
            bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'

            for i in range(laenge_liste_keys):
                bucket_keys_tabelle = bucket_keys_tabelle + '<tr>'
                if liste_keys[i].name == None and aktuellezone != "Amazon":
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/bucketkeyentfernen?md5hash='
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].etag).replace('"','')
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                if liste_keys[i].name == None and aktuellezone != "Amazon":
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>&nbsp;</td>'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                  if sprache == "de":
                    bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                  else:
                    bucket_keys_tabelle = bucket_keys_tabelle + '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                  bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<a href="'
                bucket_keys_tabelle = bucket_keys_tabelle + liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=False).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                bucket_keys_tabelle = bucket_keys_tabelle + '">'
                bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                bucket_keys_tabelle = bucket_keys_tabelle + '</a>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                bucket_keys_tabelle = bucket_keys_tabelle + '<td align="right">'
                if liste_keys[i].name == None and aktuellezone != "Amazon":
                  bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].size)
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                bucket_keys_tabelle = bucket_keys_tabelle + '<td>'
                # Format ISO8601 timestring for better looking.
                if liste_keys[i].name == None and aktuellezone != "Amazon":
                  bucket_keys_tabelle = bucket_keys_tabelle + '&nbsp;'
                else:
                  datum_der_letzten_aenderung = parse(liste_keys[i].last_modified)
                  bucket_keys_tabelle = bucket_keys_tabelle + str(datum_der_letzten_aenderung.strftime("%Y-%m-%d  %H:%M:%S"))
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'

                bucket_keys_tabelle = bucket_keys_tabelle + '<td align="center">'
                bucket_keys_tabelle = bucket_keys_tabelle + '<a href="/acl_einsehen?key='
                bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].name)
                bucket_keys_tabelle = bucket_keys_tabelle + '&amp;md5hash='
                bucket_keys_tabelle = bucket_keys_tabelle + str(liste_keys[i].etag).replace('"','')
                if sprache == "de":
                  bucket_keys_tabelle = bucket_keys_tabelle + '" title="ACL einsehen/&auml;ndern">ACL einsehen/&auml;ndern</a>'
                else:
                  bucket_keys_tabelle = bucket_keys_tabelle + '" title="view/edit ACL">view/edit ACL</a>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '<td align="center">'
                bucket_keys_tabelle = bucket_keys_tabelle + '<tt>'+str(liste_keys[i].etag).replace('"','')+'</tt>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</td>'
                bucket_keys_tabelle = bucket_keys_tabelle + '</tr>'
            bucket_keys_tabelle = bucket_keys_tabelle + '</table>'


          #Documentation about howto upload keys into S3
          #http://docs.amazonwebservices.com/AmazonS3/latest/index.html?HTTPPOSTForms.html
          #http://doc.s3.amazonaws.com/proposals/post.html
          #http://developer.amazonwebservices.com/connect/entry.jspa?externalID=1434
          #http://s3.amazonaws.com/doc/s3-example-code/post/post_sample.html

          # Create the policy dokument
          # expiration date is specified in ISO 8601 format.
          policy_document = ''
          policy_document = policy_document + '{'
          policy_document = policy_document + '"expiration": "2100-01-01T00:00:00Z",'
          policy_document = policy_document + '"conditions": ['
          policy_document = policy_document + '{"bucket": "'+bucketname+'"}, '
          policy_document = policy_document + '["starts-with", "$acl", ""],'          
          policy_document = policy_document + '{"success_action_redirect": "http://cloudoctopus.appspot.com/S3"},'         
          policy_document = policy_document + '["starts-with", "$key", ""],'
          policy_document = policy_document + '["starts-with", "$Content-Type", ""]'
          policy_document = policy_document + ']'
          policy_document = policy_document + '}'

          # Encode the policy document using Base64
          policy = base64.b64encode(policy_document)

          # Calculate the signature with the Secret Access Key and the policy
          signature = base64.b64encode(hmac.new(AWSSecretAccessKeyId, policy, sha).digest())

          

          # This is done all before.
          # !!! Silly programming !!!
          
          # Get data out of the DB
          alledaten = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
          # How many entries for this user exist?
          alledaten_clount = alledaten.count()     
          # Get all data of user
          alledaten_ergebnisse = alledaten.fetch(100) 
          i = 0
          # Walk through every line of the user in the DB 
          for alledatendurchlauf in alledaten_ergebnisse:
            i = i + 1
            if i == 1:
              regionname1 = str(alledatendurchlauf.regionname)
              endpointurl1 = str(alledatendurchlauf.endpointurl)
              accesskey1 = str(alledatendurchlauf.accesskey)
              zugangstyp1 = str(alledatendurchlauf.zugangstyp)
              eucalyptusname1 = str(alledatendurchlauf.eucalyptusname)
              port1 = str(alledatendurchlauf.port)
              ziel_adresse_upload1 = endpointurl1 + '/'
              
              AWSSecretAccessKeyId1 = aws_secret_access_key_erhalten(username,eucalyptusname1)
              signature1 = base64.b64encode(hmac.new(AWSSecretAccessKeyId1, policy, sha).digest())
            else:
              regionname2 = str(alledatendurchlauf.regionname)
              endpointurl2 = str(alledatendurchlauf.endpointurl)
              accesskey2 = str(alledatendurchlauf.accesskey)
              zugangstyp2 = str(alledatendurchlauf.zugangstyp)
              eucalyptusname2 = str(alledatendurchlauf.eucalyptusname)
              port2 = str(alledatendurchlauf.port)
              ziel_adresse_upload2 = endpointurl2 + '/'

              AWSSecretAccessKeyId2 = aws_secret_access_key_erhalten(username,eucalyptusname2)
              signature2 = base64.b64encode(hmac.new(AWSSecretAccessKeyId2, policy, sha).digest())

#              self.response.out.write(regionname1 + '<BR>')            
#              self.response.out.write(zugangstyp1 + '<BR>')
#              self.response.out.write(eucalyptusname1 + '<BR>')
#              self.response.out.write(accesskey1 + '<BR>')
#              self.response.out.write(AWSSecretAccessKeyId1 + '<BR>')
#              self.response.out.write(ziel_adresse_upload1+bucketname + '<BR>')
#              
#              self.response.out.write(regionname2 + '<BR>')
#              self.response.out.write(zugangstyp2 + '<BR>')
#              self.response.out.write(eucalyptusname2 + '<BR>')
#              self.response.out.write(accesskey2 + '<BR>')
#              self.response.out.write(AWSSecretAccessKeyId2 + '<BR>')
#              self.response.out.write(ziel_adresse_upload2+bucketname + '<BR>')
                
        
          ajax_formular = '' 
          ajax_formular = ajax_formular + '<script type="text/javascript" src="jquery.min.js"></script>\n'
          ajax_formular = ajax_formular + '<script type="text/javascript" src="upload.js"></script>\n'
          ajax_formular = ajax_formular + '<script type="text/javascript" src="jquery.blockUI.js"></script>\n'
        
          ajax_formular = ajax_formular + '<script type="text/javascript">'
          if anzahl == 1:           

#            if aktuellezone == "Eucalyptus":
#              endpointurl = endpointurl_erhalten(username,eucalyptusname)
#              port = port_erhalten(username,eucalyptusname) 
#              ziel_adresse =  str(endpointurl) + ':' + str(port) + '/services/Walrus/'
            if aktuellezone == "GoogleStorage":
              ziel_adresse =  'commondatastorage.googleapis.com/'
            else:
              # aktuellezone == "Amazon":
              ziel_adresse = 's3.amazonaws.com/'
            
            ajax_formular = ajax_formular + 'var data = ['
            ajax_formular = ajax_formular + '{sUrl:"http://'+ziel_adresse+bucketname+'",'
            ajax_formular = ajax_formular + ' success_action_redirect:"http://cloudoctopus.appspot.com/S3",'
            ajax_formular = ajax_formular + ' AWSAccessKeyId:"'+AWSAccessKeyId+'",'
            ajax_formular = ajax_formular + ' policy:"'+policy+'",'
            ajax_formular = ajax_formular + ' signature:"'+signature+'"}'
            ajax_formular = ajax_formular + '];'
          else:
            ajax_formular = ajax_formular + 'var data = ['
            ajax_formular = ajax_formular + '{sUrl:"http://'+ziel_adresse_upload1+bucketname+'",'
            ajax_formular = ajax_formular + ' success_action_redirect:"http://cloudoctopus.appspot.com/S3",'
            ajax_formular = ajax_formular + ' AWSAccessKeyId:"'+accesskey1+'",'
            ajax_formular = ajax_formular + ' policy:"'+policy+'",'
            ajax_formular = ajax_formular + ' signature:"'+signature1+'"}'
            ajax_formular = ajax_formular + ' ,'
            ajax_formular = ajax_formular + ' {sUrl:"http://'+ziel_adresse_upload2+bucketname+'",'
            ajax_formular = ajax_formular + ' success_action_redirect:"http://cloudoctopus.appspot.com/S3",'
            ajax_formular = ajax_formular + ' AWSAccessKeyId:"'+accesskey2+'",'
            ajax_formular = ajax_formular + ' policy:"'+policy+'",'
            ajax_formular = ajax_formular + ' signature:"'+signature2+'"}'
            ajax_formular = ajax_formular + '];'
          ajax_formular = ajax_formular + '</script>\n'




 
          
          keys_upload_formular = '<p>&nbsp;</p>\n'       
          keys_upload_formular = keys_upload_formular + '<form target="frame1" id="form1" action="" method="post" enctype="multipart/form-data">\n'
          keys_upload_formular = keys_upload_formular + '<table border="0" cellspacing="0" cellpadding="5">'
          keys_upload_formular = keys_upload_formular + '<tr>'
          keys_upload_formular = keys_upload_formular + '<td>'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" name="key" value="${filename}">\n'
          keys_upload_formular = keys_upload_formular + '<select name="acl" size="1">\n'
          keys_upload_formular = keys_upload_formular + '<option selected="selected">public-read</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>private</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>public-read-write</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>authenticated-read</option>\n'
          keys_upload_formular = keys_upload_formular + '</select>\n'
          keys_upload_formular = keys_upload_formular + '<select name="Content-Type" size="1">\n'
          keys_upload_formular = keys_upload_formular + '<option selected="selected">application/octet-stream</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>application/pdf</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>application/zip</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/mp4</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/mpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/ogg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>audio/vorbis</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/gif</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/jpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/png</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>image/tiff</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>text/html</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>text/plain</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/mp4</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/mpeg</option>\n'
          keys_upload_formular = keys_upload_formular + '<option>video/ogg</option>\n'
          keys_upload_formular = keys_upload_formular + '</select>\n'
          keys_upload_formular = keys_upload_formular + '</td>\n'
          keys_upload_formular = keys_upload_formular + '</tr>\n'
          keys_upload_formular = keys_upload_formular + '<tr>\n'
          keys_upload_formular = keys_upload_formular + '<td>\n'

          
          keys_upload_formular = keys_upload_formular + '<input type="hidden" id="success_action_redirect" name="success_action_redirect" value="">\n'        
          keys_upload_formular = keys_upload_formular + '<input type="hidden" id="AWSAccessKeyId" name="AWSAccessKeyId" value="">\n'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" id="policy" name="policy" value="">\n'
          keys_upload_formular = keys_upload_formular + '<input type="hidden" id="signature" name="signature" value="">\n'
          
          #keys_upload_formular = keys_upload_formular + '<input type="hidden" id="submit" name="submit" value="submit">\n'
         
          keys_upload_formular = keys_upload_formular + '</td>\n'
          keys_upload_formular = keys_upload_formular + '</tr>\n'
          keys_upload_formular = keys_upload_formular + '<tr>\n'
          keys_upload_formular = keys_upload_formular + '<td>\n'
          keys_upload_formular = keys_upload_formular + '<input type="file" name="file" size="80">\n'
          keys_upload_formular = keys_upload_formular + '</td>\n'
          keys_upload_formular = keys_upload_formular + '</tr>\n'

          # Traditional Way to upload a Key into S3
          keys_upload_formular = keys_upload_formular + '<tr>'
          keys_upload_formular = keys_upload_formular + '<td>'
          if sprache == "de":
            keys_upload_formular = keys_upload_formular + '<input type="submit" style="display:none" id="button2" name="submit" value="Datei hochladen">\n'
          else:
            keys_upload_formular = keys_upload_formular + '<input type="submit" style="display:none" id="button2" name="submit" value="upload file">\n'
          keys_upload_formular = keys_upload_formular + '</td>'
          keys_upload_formular = keys_upload_formular + '</tr>'
          
          keys_upload_formular = keys_upload_formular + '</table>\n'
          keys_upload_formular = keys_upload_formular + '</form>'
          keys_upload_formular = keys_upload_formular + '\n'
          keys_upload_formular = keys_upload_formular + '<div id="statustext"></div>'
          keys_upload_formular = keys_upload_formular + '<div style="border:1px solid black;width:200px;height:20px"><div id="statusbar" style="background-color:black;width:1px;height:20px">&nbsp;</div></div>'
          
          
          if sprache == "de":
            keys_upload_formular = keys_upload_formular + '<button id="button1">Datei hochladen</button>'
          else:
            keys_upload_formular = keys_upload_formular + '<button id="button1">upload file</button>'


          iframe = '<iframe id="frame1" name="frame1" style="display:none"></iframe>'
           
      
          if laenge_liste_keys != 0:
            alle_keys_loeschen_button = '<p>&nbsp;</p>\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<form action="/alle_keys_loeschen" method="get">\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="hidden" name="s3_ansicht" value="pur"> \n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="hidden" name="bucket_name" value="'+bucketname+'"> \n'
            if sprache == "de":
              alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="submit" value="Alle Keys l&ouml;schen">\n'
            else:
              alle_keys_loeschen_button = alle_keys_loeschen_button + '<input type="submit" value="Erase all keys">\n'
            alle_keys_loeschen_button = alle_keys_loeschen_button + '</form>\n'
          else:
            alle_keys_loeschen_button = ''

          
          if anzahl == 1:
            if sprache == "de":
              redundanz_warnung = 'Sie nutzen aktuell nur einen Cloud-basierten Speicher-Dienst. '
              redundanz_warnung = redundanz_warnung + 'Somit ist keine Redundanz m&ouml;glich!'
              redundanz_warnung = redundanz_warnung + '<p>&nbsp;</p>'
            else:
              redundanz_warnung = 'You use just a single cloud-based storage service. '
              redundanz_warnung = redundanz_warnung + 'Therefore, the data is not stored in a redundant way!'
              redundanz_warnung = redundanz_warnung + '<p>&nbsp;</p>'
          elif anzahl >= 1:            
            if sprache == "de":
              redundanz_warnung = 'Sie nutzen aktuell ' + str(anzahl) + ' Cloud-basierte Speicher-Dienste. '
              redundanz_warnung = redundanz_warnung + 'Somit ist Redundanz m&ouml;glich!'
              redundanz_warnung = redundanz_warnung + '<p>&nbsp;</p>'
            else:       
              redundanz_warnung = 'You use ' + str(anzahl) + ' cloud-based storage services. '
              redundanz_warnung = redundanz_warnung + 'Therefore, the data can be stored in a redundant way!'
              redundanz_warnung = redundanz_warnung + '<p>&nbsp;</p>'
          else:
            redundanz_warnung = ''
            
          
          
          if anzahl == 1:
            # If the number of storage services is 1, the data is always syncron
            synchron_warnung = ''
          else:
            # If there are more than one storage service, check if data is synchron
            # Check here for synchronicity
            if Main_Liste == Second_list:
              # If both Lists are equal
              if sprache == "de":
                synchron_warnung = '<font color="green">Ihre Daten sind synchron</font>'
                synchron_warnung = synchron_warnung + '<p>&nbsp;</p>'
              else:
                synchron_warnung = '<font color="green">Your data are synchron</font>'
                synchron_warnung = synchron_warnung + '<p>&nbsp;</p>'
            else:
              # If both Lists are not equal
              if sprache == "de":
                synchron_warnung = '<font color="red">Ihre Daten sind nicht synchron!</font>'
                synchron_warnung = synchron_warnung + '<p>&nbsp;</p>'
              else:
                synchron_warnung = '<font color="red">The synchronicity of your data is broken!</font>'
                synchron_warnung = synchron_warnung + '<p>&nbsp;</p>'
 

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'bucket_keys_tabelle': bucket_keys_tabelle,
          'input_error_message': input_error_message,
          'keys_upload_formular': keys_upload_formular,
          'alle_keys_loeschen_button': alle_keys_loeschen_button,
          'redundanz_warnung': redundanz_warnung,
          'ajax_formular': ajax_formular,
          'iframe': iframe,
          'synchron_warnung': synchron_warnung
          }

          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "s3.html")
          self.response.out.write(template.render(path,template_values))

