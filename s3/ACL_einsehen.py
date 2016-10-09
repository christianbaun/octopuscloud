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
from library import logins3

from dateutil.parser import *

from error_messages import error_messages

from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('simple.cfg')


class ACL_einsehen(webapp.RequestHandler):
    def get(self):
        # Namen des Keys holen, dessen ACL angezeigt wird
        keyname = self.request.get('key')
        # Get the MD5 hash of the key that need to be erased
        md5hash = self.request.get('md5hash')
        
        # Get the username
        username = users.get_current_user()
        if not username:
          self.redirect('/')
          
        # Nachsehen, ob Credentials von diesem Benutzer eingeneben wurden
        testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
            
        results = testen.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob Credentials für einen Amazon S3 Zugang eingegeben wurden
          testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Amazon")
          # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
          results = testen.fetch(100)
          if results:
            # Es gibt schon einen S3 Zugang
            aktuellezone = "Amazon"
            eucalyptusname = "Amazon"
          else:
            # Nachsehen, ob Credentials für einen Eucalyptus Zugang eingegeben wurden
            testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db AND zugangstyp = :zugangstyp_db", username_db=username, zugangstyp_db="Eucalyptus")
            results = testen.fetch(100)
             
            if results:
              # Es gibt einen Eucalyptus (Walrus) Zugang
              aktuellezone = "Eucalyptus"
              # Einen Eucalyptus-Zugang holen
              anzahl = testen.count()   
              for test in results:
                eucalyptusname = str(test.eucalyptusname)
                
            else:
              self.redirect('/')
              
            
        # Connect with storage service
        conn_s3, regionname = logins3(username, aktuellezone)
        
        # Get values from the config file
        # The name of the bucket that is used      
        # The character "@" cannot be used. Therefore we use "at".  
        bucketname = str(parser.get('bucket', 'bucketname'))+str(username).replace('@', 'at').replace('.', '-')
            
        bucket_instance = conn_s3.get_bucket(bucketname)

        

        # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
        sprache = aktuelle_sprache(username)
        navigations_bar = navigations_bar_funktion(sprache)



        url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
        url_linktext = 'Logout'



        key_instance = bucket_instance.get_acl(keyname)

        acl = bucket_instance.get_acl(key_name=keyname)
        

        AllUsersREAD  = ''
        AllUsersWRITE = ''
        AllUsersFULL  = ''
        AuthentUsersREAD   = ''
        AuthentUsersWRITE  = ''
        AuthentUsersFULL   = ''
        OwnerName   = ''
        OwnerREAD   = ''
        OwnerWRITE  = ''
        OwnerFULL   = ''

        for grant in acl.acl.grants:
          if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'READ':
            AllUsersREAD  = 'tick.png'
          if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'WRITE':
            AllUsersWRITE = 'tick.png'
          if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'FULL_CONTROL':
            AllUsersREAD  = 'tick.png'
            AllUsersWRITE = 'tick.png'
            AllUsersFULL  = 'tick.png'
          if str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'READ':
            AuthentUsersREAD  = 'tick.png'
          elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'WRITE':
            AuthentUsersWRITE = 'tick.png'
          elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'FULL_CONTROL':
            AuthentUsersFULL  = 'tick.png'
          # Wenn der Besitzer des Keys dieser Eintrag hier ist...
          if str(key_instance.owner.id) == str(grant.id):
            OwnerName = str(grant.display_name)
            if grant.permission == 'READ':
              OwnerREAD   = 'tick.png'
            if grant.permission == 'WRITE':
              OwnerWRITE  = 'tick.png'
            if grant.permission == 'FULL_CONTROL':
              OwnerREAD   = 'tick.png'
              OwnerWRITE  = 'tick.png'
              OwnerFull   = 'tick.png'

        if AllUsersREAD  == '': AllUsersREAD  = 'delete.png'
        if AllUsersWRITE == '': AllUsersWRITE = 'delete.png'
        if AllUsersFULL  == '': AllUsersFULL  = 'delete.png'
        if AuthentUsersREAD  == '': AuthentUsersREAD  = 'delete.png'
        if AuthentUsersWRITE == '': AuthentUsersWRITE = 'delete.png'
        if AuthentUsersFULL  == '': AuthentUsersFULL  = 'delete.png'
        if OwnerREAD  == '': OwnerREAD  = 'delete.png'
        if OwnerWRITE == '': OwnerWRITE = 'delete.png'
        if OwnerFull  == '': OwnerFull  = 'delete.png'

        acl_tabelle = '\n'
        acl_tabelle = acl_tabelle + '<table border="1" cellspacing="0" cellpadding="5"> \n'
        acl_tabelle = acl_tabelle + '<tr> \n'
        if sprache == "de": 
          acl_tabelle = acl_tabelle + '<th>Benutzer</th> \n'
          acl_tabelle = acl_tabelle + '<th>Lesen</th> \n'
          acl_tabelle = acl_tabelle + '<th>Schreiben</th> \n'
          acl_tabelle = acl_tabelle + '<th>Voller Zugriff</th> \n'
        else:
          acl_tabelle = acl_tabelle + '<th>User</th> \n'
          acl_tabelle = acl_tabelle + '<th>Read</th> \n'
          acl_tabelle = acl_tabelle + '<th>Write</th> \n'
          acl_tabelle = acl_tabelle + '<th>Full Control</th> \n'
        acl_tabelle = acl_tabelle + '</tr> \n'
        acl_tabelle = acl_tabelle + '<tr> \n'
        if sprache == "de": acl_tabelle = acl_tabelle + '<td>Alle</td> \n'
        else:               acl_tabelle = acl_tabelle + '<td>Everyone</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersREAD+'" width="24" height="24" border="0" alt="'+AllUsersREAD+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersWRITE+'" width="24" height="24" border="0" alt="'+AllUsersWRITE+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersFULL+'" width="24" height="24" border="0" alt="'+AllUsersFULL+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '</tr> \n'
        acl_tabelle = acl_tabelle + '<tr> \n'
        if sprache == "de": acl_tabelle = acl_tabelle + '<td>Authentifizierte Benutzer</td> \n'
        else:               acl_tabelle = acl_tabelle + '<td>Authenticated Users</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersREAD+'" width="24" height="24" border="0" alt="'+AuthentUsersREAD+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersWRITE+'" width="24" height="24" border="0" alt="'+AuthentUsersWRITE+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersFULL+'" width="24" height="24" border="0" alt="'+AuthentUsersFULL+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '</tr> \n'
        acl_tabelle = acl_tabelle + '<tr> \n'
        if sprache == "de": acl_tabelle = acl_tabelle + '<td>'+OwnerName+' (Besitzer)</td> \n'
        else:               acl_tabelle = acl_tabelle + '<td>'+OwnerName+' Owner</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerREAD+'" width="24" height="24" border="0" alt="'+OwnerREAD+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerWRITE+'" width="24" height="24" border="0" alt="'+OwnerWRITE+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '<td align="center"> \n'
        acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerFull+'" width="24" height="24" border="0" alt="'+OwnerFull+'"> \n'
        acl_tabelle = acl_tabelle + '</td> \n'
        acl_tabelle = acl_tabelle + '</tr> \n'
        acl_tabelle = acl_tabelle + '</table> \n'


        template_values = {
        'navigations_bar': navigations_bar,
        'url': url,
        'url_linktext': url_linktext,
        'keyname': keyname,
        'acl_tabelle': acl_tabelle,
        'md5hash': md5hash
        }


        path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "acl.html")
        self.response.out.write(template.render(path,template_values))


