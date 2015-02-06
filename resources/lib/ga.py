"""""
Simple proof of concept code to push data to Google Analytics.
Related blog posts:
 * http://www.canb.net/2012/01/push-data-to-google-analytics-with.html
 * https://medium.com/python-programming-language/80eb9691d61f
"""

import sys, re

from Globals import *
from random import randint
from urllib import urlencode
from urllib2 import urlopen
from urlparse import urlunparse
from hashlib import sha1
from os import environ

# Set your proprty id via the environment or simply type it
# below
PROPERTY_ID = environ.get("GA_PROPERTY_ID", "UA-45979766-1")
 
# Generate the visitor identifier somehow. I get it from the
# environment, calculate the SHA1 sum of it, convert this from base 16
# to base 10 and get first 10 digits of this number.

bcts = ''
if REAL_SETTINGS.getSetting('bumpers') == '1':
    bcts += 'BL+'
elif REAL_SETTINGS.getSetting('bumpers') == '2':
    bcts += 'BI+'
    
if REAL_SETTINGS.getSetting('bumperratings') == 'true':
    bcts += 'R+'
    
if REAL_SETTINGS.getSetting('commercials') == '1':
    bcts += 'CL+'
elif REAL_SETTINGS.getSetting('commercials') == '2':
    bcts += 'CY+'
elif REAL_SETTINGS.getSetting('commercials') == '3':
    bcts += 'CI+'
    
if REAL_SETTINGS.getSetting('AsSeenOn') == 'true':
    bcts += 'A+'
    
if REAL_SETTINGS.getSetting('trailers') == '1':
    bcts += 'TL+'
elif REAL_SETTINGS.getSetting('trailers') == '2':
    bcts += 'TX+'
elif REAL_SETTINGS.getSetting('trailers') == '3':
    bcts += 'TY+'
elif REAL_SETTINGS.getSetting('trailers') == '4':
    bcts += 'TI+'
 
if REAL_SETTINGS.getSetting('Hub') == 'false':  
    HubEdition = 'False'
else:
    HubEdition = 'True'
    
if REAL_SETTINGS.getSetting('Donor_Enabled') == 'true':
    try:
        donor = REAL_SETTINGS.getSetting('Donor_UP')
        donor = donor.split(':')[0]
    except Exception,e:
        donor = 'Unknown'
else:
    donor = 'FreeUser'

if REAL_SETTINGS.getSetting('Visitor_GA') == '':
    from random import randint
    REAL_SETTINGS.setSetting('Visitor_GA', str(randint(0, 0x7fffffff)))

VISITOR = str(REAL_SETTINGS.getSetting("Visitor_GA"))

# The path to visit
PATH = ("PTVL:"+ str(ADDON_VERSION) + "/" + str(VISITOR) + '/' + str(donor) + '/Hub:' + str(HubEdition)+ '/Skin:' + str(Skin_Select) + '/BCT:' + bcts)
 
# Collect everything in a dictionary
DATA = {"utmwv": "5.2.2d",
        "utmn": str(randint(1, 9999999999)),
        "utmp": PATH,
        "utmac": PROPERTY_ID,
        "utmcc": "__utma=%s;" % ".".join(["1", VISITOR, "1", "1", "1", "1"])}
 
# Encode this data and generate the final URL
URL = urlunparse(("http",
                  "www.google-analytics.com",
                  "/__utm.gif",
                  "",
                  urlencode(DATA),
                  ""))
 
# Make the request
if REAL_SETTINGS.getSetting('ga_disable') == 'false' or REAL_SETTINGS.getSetting('Donor_Enabled') == 'true':
    print "Requesting", URL
    try:
        print urlopen(URL).info()
    except Exception,e:
        pass