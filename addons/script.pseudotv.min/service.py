#   Copyright (C) 2015 Kevin S. Graer
#
#
# This file is part of PseudoTV Min.
#
# PseudoTV Min is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV Min is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Min.  If not, see <http://www.gnu.org/licenses/>.


import os, shutil, datetime, time, random
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from time import sleep

# Plugin Info
ADDON_ID = 'script.pseudotv.min'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
THUMB = (xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'images')) + '/' + 'icon.png')


def service():
    xbmc.log('script.pseudotv.min-Service: Init')
    #REAL_SETTINGS.setSetting("ArtService_Running","false")
    try:
        while (not xbmc.abortRequested):
            if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
                xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
                xbmc.log('script.pseudotv.min-Service: Running')
                #HubSwap()
                xbmcgui.Window(10000).setProperty("PseudoTVRunning", "False")
                xbmc.log('script.pseudotv.min-Service: Idle')
            xbmc.sleep(4000)
    except:
        pass

def autostart():
    xbmc.log('script.pseudotv.min-Service: autostart')   
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Min","Service Starting...", 4000, THUMB) )
    AUTOSTART_TIMER = [0,5,10,15,20]#in seconds
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')

service()

#Autostart Trigger
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart() 
    