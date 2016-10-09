#!/usr/bin/env python

# Copyright 2009,2010 Christian Baun

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import decimal
import wsgiref.handlers
import os
import sys
import cgi
import time
import re



from s3.AlleKeysLoeschenDefinitiv import *
from s3.ACL_Aendern import *
from s3.AlleKeysLoeschenFrage import *
from s3.BucketKeyEntfernen import *
from s3.ACL_einsehen import *
from s3.S3 import *

from internal.ZugangEntfernen import *
from internal.Sprache import *
from internal.Datastore import *
from internal.PersoenlicheDatanLoeschen import *
from internal.ZugangEinrichten import *
from internal.RegionWechseln import *
from internal.Regionen import *
from internal.Login import *
from internal.MainPage import *


from library import xor_crypt_string
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten
from library import get_second_list

from error_messages import error_messages

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




def main():
    application = webapp.WSGIApplication([('/', MainPage),
                                          ('/regionen', Regionen),
                                          ('/login', Login),
                                          ('/sprache', Sprache),
                                          ('/info', MainPage),
                                          ('/zugangeinrichten', ZugangEinrichten),
                                          ('/zugangentfernen', ZugangEntfernen),
                                          ('/regionwechseln', RegionWechseln),
                                          ('/persoenliche_datan_loeschen', PersoenlicheDatanLoeschen),
                                          ('/s3', S3),
                                          ('/bucketkeyentfernen', BucketKeyEntfernen),
                                          ('/acl_einsehen', ACL_einsehen),
                                          ('/acl_aendern', ACL_Aendern),
                                          ('/alle_keys_loeschen', AlleKeysLoeschenFrage),
                                          ('/alle_keys_loeschen_definitiv', AlleKeysLoeschenDefinitiv)],
                                          debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()





