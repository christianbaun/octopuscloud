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

class Regionen(webapp.RequestHandler):
    def get(self):
        message = self.request.get('message')
        neuerzugang = self.request.get('neuerzugang')
        # Den Usernamen erfahren
        # Get the username
        username = users.get_current_user()
        # self.response.out.write('posted!')

        # Wir müssen das so machen, weil wir sonst nicht weiterkommen,
        # wenn ein Benutzer noch keinen Zugang eingerichtet hat.
        if users.get_current_user():
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache)

            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'


            if sprache != "de":
              sprache = "en"

            input_error_message = error_messages.get(message, {}).get(sprache)

            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""

            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("127", "128", "129"):
              input_error_message = format_error_message_green(input_error_message)
            elif message in ("89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"):
              # Ansonsten wird die Nachricht rot formatiert
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
            

            Amazon_vorhanden = "false"
            Eucalyptus_vorhanden = "false"
            GoogleStorage_vorhanden = "false"

            # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
            testen = db.GqlQuery("SELECT * FROM OctopusCloudDatenbank WHERE user = :username_db", username_db=username)
            # Wie viele Einträge des Benutzers sind schon vorhanden?
            anzahl = testen.count()     
            # Alle Einträge des Benutzers holen?
            results = testen.fetch(100) 

            if anzahl:
              # wenn schon Einträge für den Benutzer vorhanden sind...
              tabelle_logins = ''
              tabelle_logins = tabelle_logins + '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_logins = tabelle_logins + '<tr>'
              tabelle_logins = tabelle_logins + '<th>&nbsp;</th>'
              if sprache == "de":
                tabelle_logins = tabelle_logins + '<th align="center">Speicherdienst</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Adresse (URL)</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Access Key</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Name (Beschreibung)</th>'
              else:
                tabelle_logins = tabelle_logins + '<th align="center">Storage Service</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Endpoint URL</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Access Key</th>'
                tabelle_logins = tabelle_logins + '<th align="center">Name (Description)</th>'
              tabelle_logins = tabelle_logins + '</tr>'
              for test in results:
                tabelle_logins = tabelle_logins + '<tr>'
                tabelle_logins = tabelle_logins + '<td>'
                tabelle_logins = tabelle_logins + '<a href="/zugangentfernen?region='
                tabelle_logins = tabelle_logins + str(test.regionname)
                tabelle_logins = tabelle_logins + '&amp;endpointurl='
                tabelle_logins = tabelle_logins + str(test.endpointurl)
                tabelle_logins = tabelle_logins + '&amp;accesskey='
                tabelle_logins = tabelle_logins + str(test.accesskey)
                if sprache == "de":
                  tabelle_logins = tabelle_logins + '" title="Zugang l&ouml;schen'
                else:
                  tabelle_logins = tabelle_logins + '" title="erase credentials'
                tabelle_logins = tabelle_logins + '"><img src="bilder/delete.png" width="16" height="16" border="0"'
                if sprache == "de":
                  tabelle_logins = tabelle_logins + ' alt="Zugang l&ouml;schen"></a>'
                else:
                  tabelle_logins = tabelle_logins + ' alt="erase credentials"></a>'
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="center">'
                tabelle_logins = tabelle_logins + str(test.zugangstyp)
                
                if str(test.zugangstyp) == "Amazon": 
                  Amazon_vorhanden = "true"
                if str(test.zugangstyp) == "Eucalyptus": 
                  Eucalyptus_vorhanden = "true"
                if str(test.zugangstyp) == "GoogleStorage": 
                  Eucalyptus_vorhanden = "true"
                  
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="center">'
                tabelle_logins = tabelle_logins + str(test.endpointurl)
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="left">'
                tabelle_logins = tabelle_logins + str(test.accesskey)
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '<td align="left">'
                tabelle_logins = tabelle_logins + test.eucalyptusname
                tabelle_logins = tabelle_logins + '</td>'
                tabelle_logins = tabelle_logins + '</tr>'
              tabelle_logins = tabelle_logins + '</table>'
            else:
              # wenn noch keine Einträge für den Benutzer vorhanden sind...
              if sprache == "de":
                tabelle_logins = 'Sie haben noch keine Login-Daten eingegeben'
              else:
                tabelle_logins = 'No credentials available'
              tabelle_logins = tabelle_logins + '<p>&nbsp;</p>'

            if neuerzugang == "eucalyptus":
              if Eucalyptus_vorhanden != "true":
                eingabefelder = '<p>&nbsp;</p>'
                eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
                eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="eucalyptus">'
                eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '  <td></td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td><font color="green">Der Name ist nur zur Unterscheidung</font></td>'
                else:
                  eingabefelder = eingabefelder + '    <td><font color="green">Choose one you like</font></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Name:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="nameregion" value="">'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '  <td></td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td><font color="green">Nur die IP oder DNS ohne <tt>/services/Eucalyptus</tt></font></td>'
                else:
                  eingabefelder = eingabefelder + '    <td><font color="green">Just the IP or DNS without <tt>/services/Eucalyptus</tt></font></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Endpoint URL:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="endpointurl" value="">'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '  <td></td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine akzeptiert nur diese Ports</font></td>'
                else:
                  eingabefelder = eingabefelder + '    <td><font color="green">Google App Engine accepts only these ports</font></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Port:</td>'
                #eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="5" maxlength="5" name="port" value=""></td>'
                eingabefelder = eingabefelder + '    <td colspan="2">'
                eingabefelder = eingabefelder + '      <select name="port" size="1">'
                eingabefelder = eingabefelder + '        <option>80</option>'
                eingabefelder = eingabefelder + '        <option>443</option>'
                eingabefelder = eingabefelder + '        <option>4443</option>'
                eingabefelder = eingabefelder + '        <option>8080</option>'
                eingabefelder = eingabefelder + '        <option>8081</option>'
                eingabefelder = eingabefelder + '        <option>8082</option>'
                eingabefelder = eingabefelder + '        <option>8083</option>'
                eingabefelder = eingabefelder + '        <option>8084</option>'
                eingabefelder = eingabefelder + '        <option>8085</option>'
                eingabefelder = eingabefelder + '        <option>8086</option>'
                eingabefelder = eingabefelder + '        <option>8087</option>'
                eingabefelder = eingabefelder + '        <option>8088</option>'
                eingabefelder = eingabefelder + '        <option>8089</option>'
                eingabefelder = eingabefelder + '        <option selected="selected">8188</option>'
  #              eingabefelder = eingabefelder + '        <option>8442</option>' ####### weg damit!!! ###
                eingabefelder = eingabefelder + '        <option>8444</option>'
                eingabefelder = eingabefelder + '        <option>8990</option>'
                eingabefelder = eingabefelder + '      </select>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
                else:
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '</table>'
                eingabefelder = eingabefelder + '</form>'
              else:
                # Eucalyptus_vorhanden is "true"
                if sprache == "de":
                  eingabefelder = '<font color="red">Sie k&ouml;nnen keine weiteren Zugansdaten f&uuml;r Eucalyptus importieren</font>'
                else:
                  eingabefelder = '<font color="red">You cannot add more Eucalyptus credentials</font>'         
            elif neuerzugang == "ec2":
              if Amazon_vorhanden == "false":
                eingabefelder = '<p>&nbsp;</p>'
                eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
                eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="ec2">'
                eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
                else:
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '</table>'
                eingabefelder = eingabefelder + '</form>'
              else:
                # Amazon_vorhanden is "true":
                if sprache == "de":
                  eingabefelder = '<font color="red">Sie k&ouml;nnen keine weiteren Zugansdaten f&uuml;r S3 importieren</font>'
                else:
                  eingabefelder = '<font color="red">You cannot add more S3 credentials</font>'      
            elif neuerzugang == "googlestorage":
              if GoogleStorage_vorhanden == "false":
                eingabefelder = '<p>&nbsp;</p>'
                eingabefelder = eingabefelder + '<form action="/zugangeinrichten" method="post" accept-charset="utf-8">'
                eingabefelder = eingabefelder + '<input type="hidden" name="typ" value="googlestorage">'
                eingabefelder = eingabefelder + '<table border="0" cellspacing="5" cellpadding="5">'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="accesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td align="right">Secret Access Key:</td>'
                eingabefelder = eingabefelder + '    <td colspan="2"><input type="text" size="40" name="secretaccesskey" value=""></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '  <tr>'
                eingabefelder = eingabefelder + '    <td>&nbsp;</td>'
                if sprache == "de":
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="Zugang einrichten"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="L&ouml;schen"></td>'
                else:
                  eingabefelder = eingabefelder + '    <td align="center"><input type="submit" value="send"></td>'
                  eingabefelder = eingabefelder + '    <td align="center"><input type="reset" value="erase"></td>'
                eingabefelder = eingabefelder + '  </tr>'
                eingabefelder = eingabefelder + '</table>'
                eingabefelder = eingabefelder + '</form>'
              else:
                # Amazon_vorhanden is "true":
                if sprache == "de":
                  eingabefelder = '<font color="red">Sie k&ouml;nnen keine weiteren Zugansdaten f&uuml;r Google Storage importieren</font>'
                else:
                  eingabefelder = '<font color="red">You cannot add more Google Storage credentials</font>'      

            else:
              eingabefelder = ''


            if neuerzugang == "eucalyptus" and Eucalyptus_vorhanden != "true":
              port_warnung = '<p>&nbsp;</p>\n'
              if sprache == "de":
                port_warnung = port_warnung + 'Die Google App Engine akzeptiert nur wenige Ports. '
                port_warnung = port_warnung + 'Leider ist der Standard-Port von Eucalyputs (8773) nicht dabei. '
                port_warnung = port_warnung + 'Es empfiehlt sich darum, einen anderen Port auf den Eucalyptus-Port umzuleiten. '
                port_warnung = port_warnung + 'Ein Beispiel:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -I INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -I PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8773</tt> '
              else:
                port_warnung = port_warnung + 'The Google App Engine accepts only a few number of ports '
                port_warnung = port_warnung + 'and the default port of Eucalyptus (8773) is not included. '
                port_warnung = port_warnung + 'Because of this fact, you have to route another port to the Eucayptus port. '
                port_warnung = port_warnung + 'For example:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -I INPUT -p tcp --dport 8188 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -I PREROUTING -t nat -i eth0 -p tcp --dport 8188 -j REDIRECT --to-port 8773</tt> '
            elif neuerzugang == "nimbus":
              port_warnung = '<p>&nbsp;</p>\n'
              if sprache == "de":
                port_warnung = port_warnung + 'Die Google App Engine akzeptiert nur wenige Ports. '
                port_warnung = port_warnung + 'Wenn Cumulus (Nimbus) keinen unterst&uuml;tzten Port (z.B. 8888) verwendet, '
                port_warnung = port_warnung + 'empfiehlt es sich, einen unterst&uuml;tzten Port auf den Port von Cumulus (Nimbus) umzuleiten. '
                port_warnung = port_warnung + 'Ein Beispiel:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -I INPUT -p tcp --dport 8990 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -I PREROUTING -t nat -i eth0 -p tcp --dport 8990 -j REDIRECT --to-port 8888</tt> '
              else:
                port_warnung = port_warnung + 'The Google App Engine accepts only a few number of ports. '
                port_warnung = port_warnung + 'If the Cumulus (Nimbus) you want to access, has a non accepted port (e.g. 8888), you have to route an accepted port to the port of the Cumulus. '
                port_warnung = port_warnung + 'For example:<br> \n'
                port_warnung = port_warnung + '<tt>iptables -I INPUT -p tcp --dport 8990 -j ACCEPT</tt><br>\n '
                port_warnung = port_warnung + '<tt>iptables -I PREROUTING -t nat -i eth0 -p tcp --dport 8990 -j REDIRECT --to-port 8888</tt> '
            else:
              port_warnung = '<p>&nbsp;</p>'


            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'eingabefelder': eingabefelder,
            'input_error_message': input_error_message,
            'tabelle_logins': tabelle_logins,
            'port_warnung': port_warnung
            }

            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "index.html")
            self.response.out.write(template.render(path,template_values))
        else:
            self.redirect('/')

