#Using the following Python script I am able to use the username and password of a Plex user to obtain a token.

# https://forums.plex.tv/t/how-to-request-a-x-plex-token-token-for-your-app/84551/6

import sys
from base64 import b64encode
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
import json

import ImportUtils

configuration = ImportUtils.get_configuration()

loginURL = 'https://plex.tv/users/sign_in.json'
plexAccount = configuration.get('Plex', 'plexAccount')

PASSWORD = input("Password for Plex account %s:\n" % plexAccount)

#we need to base 64 encode it
#and then decode it to acsii as python 3 stores it as a byte string
BASE64STRING = b64encode(bytes('%s:%s' % (plexAccount, PASSWORD), 'utf-8')).decode("ascii")
HEADERS = {
'X-Plex-Client-Identifier': "iTunes import script",
'X-Plex-Product': "iTunes import script suite",
'X-Plex-Version': "1.1"}

POST_FIELDS = {
'user[login]': plexAccount,
'user[password]': PASSWORD}

request = Request(loginURL, data=urlencode(POST_FIELDS).encode(), headers=HEADERS, method='POST')
#(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)

print("plexToken: %s" % json.loads(urlopen(request).read())['user']['authToken'])
