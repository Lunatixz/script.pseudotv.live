#   Copyright (C) 2013 Blazetamer, Lunatixz
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.


import urllib,urllib2
import xbmcplugin, xbmcgui, xbmc, xbmcaddon, xbmcvfs
import re, os, sys, time

from resources.lib.utils import *
from resources.lib.Globals import *

def UPDATEFILES():
    xbmc.log('script.pseudotv.live-autoupdate: UPDATEFILES')
    
    if REAL_SETTINGS.getSetting("Auto_Version") == "1":
        url='https://github.com/Lunatixz/script.pseudotv.live/archive/master.zip'
        changelog = 'https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/master/changelog.txt'    
    elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
        url='https://github.com/Lunatixz/script.pseudotv.live/archive/development.zip'
        changelog = 'https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/development/changelog.txt'  
      
    name = 'script.pseudotv.live.zip'   
    path = xbmc.translatePath(os.path.join('special://home/addons','packages'))
    addonpath = xbmc.translatePath(os.path.join('special://','home/addons'))
    lib = os.path.join(path,name)
    xbmc.log('script.pseudotv.live-autoupdate: URL = ' + url)
    
    try: 
        xbmcvfs.delete(lib)
        xbmc.log('script.pseudotv.live-autoupdate: deleted old package')
    except: 
        pass
     
    try:
        download(url, lib, '')
        xbmc.log('script.pseudotv.live-autoupdate: downloaded new package')
        all(lib,addonpath,'')
        xbmc.log('script.pseudotv.live-autoupdate: extracted new package')
        MSG = 'Update Complete'
    except: 
        MSG = 'Update Failed, Try Again Later'
        pass
        
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 4000, THUMB) )
    return