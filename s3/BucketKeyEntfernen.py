#!/usr/bin/env python

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api.urlfetch import DownloadError

from library import logins3

from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('simple.cfg')


class BucketKeyEntfernen(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Get the MD5 hash of the key that need to be erased
        md5hash = self.request.get('md5hash')
        
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
          # How many entries of this user exist?
          anzahl = testen.count()     
          
          # Walk though every entry (storage service credentials) of this user
          for i in results:
            regionname = str(i.regionname)
            endpointurl = str(i.endpointurl)
            accesskey = str(i.accesskey)
            zugangstyp = str(i.zugangstyp)
            eucalyptusname = str(i.eucalyptusname)

            if regionname == "Amazon":
              # If we are working with Amazon S3 now...
              aktuellezone = "Amazon"
            else:
              # If we are working with Walrus (Eucalyptus) now...
              aktuellezone = "Eucalyptus"
              
            # Connect with storage service
            conn_s3, regionname = logins3(username, aktuellezone)
            
            # Get values from the config file
            # The name of the bucket that is used      
            # The character "@" cannot be used. Therefore we use "at".  
            bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at')
            
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
            if aktuellezone != "Amazon":
              liste_keys2 = []
              for i in range(laenge_liste_keys):
                if str(liste_keys[i].name) != 'None':
                  liste_keys2.append(liste_keys[i])
              laenge_liste_keys2 = len(liste_keys2)
              laenge_liste_keys = laenge_liste_keys2
              liste_keys = liste_keys2
              
    
            for i in range(laenge_liste_keys):
              # Convert MD5 hash of the key that is checked now no a string and erase the double quotes
              if aktuellezone == "Amazon":     
                vergleich = str(liste_keys[i].etag).replace('"','')
              else:
                vergleich = str(liste_keys[i].etag)
                
              if vergleich == md5hash:
                # If the MD5 hash is equal to the key that is checked now...
                try:
                  # Try to erase the key
                  liste_keys[i].delete()
                except:
                  fehlermeldung = "112"
                  # If it didn't work ...
                  self.redirect('/s3?message='+fehlermeldung)
                else:
                  fehlermeldung = "111"
                  # It the key was erased...
                  self.redirect('/s3?message='+fehlermeldung)

