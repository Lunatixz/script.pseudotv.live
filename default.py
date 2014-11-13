#   Copyright (C) 2013 Lunatixz
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
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, re, shutil
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *
from resources.lib.FileAccess import *
from autoupdate import *
from pseudotv import *
from resources.lib.utils import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import resources.lib.storageserverdummy as StorageServer

# Script constants
__scriptname__ = "PseudoTV Live"
__author__     = "Lunatixz, Jason102 & Angrycamel"
__url__        = "https://github.com/Lunatixz/script.pseudotv.live"
__settings__   = xbmcaddon.Addon(id='script.pseudotv.live')
__cwd__        = __settings__.getAddonInfo('path')
   
# Adapting a solution from ronie (http://forum.xbmc.org/showthread.php?t=97353)
if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
    shouldrestart = False
    UPDATED = False

    if shouldrestart == False: 
        if REAL_SETTINGS.getSetting("Auto_Version") != "0":
            # Compare git version with local version.
            xbmc.log('script.pseudotv.live-default: CheckVersion mode = ' + str(REAL_SETTINGS.getSetting("Auto_Version")))
            try:        
                curver = xbmc.translatePath(os.path.join(ADDON_PATH,'addon.xml'))    
                source = open(curver, mode = 'r')
                link = source.read()
                source.close()
                match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
                
                for vernum in match:
                    xbmc.log('script.pseudotv.live-default: Original Version = ' + str(vernum))
                    
                try:
                    if REAL_SETTINGS.getSetting("Auto_Version") == "1":
                        link=Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/master/addon.xml')
                    elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
                        link=Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/development/addon.xml')
                except:
                    link='nill'

                link = link.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
                match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
                
                if len(match) > 0:
                    if vernum != str(match[0]):
                        dialog = xbmcgui.Dialog()
                        confirm = xbmcgui.Dialog().yesno('[B]PseudoTV Live Update Available![/B]', "Your version is outdated." ,'The current available version is '+str(match[0]),'Would you like to update now?',"Cancel","Update")
                        if confirm:
                            UPDATEFILES() 
                            UPDATED = True
            except Exception:
                pass
            
        #If Updated, Textbox, Videowindow/DonorDownload and quit...
        if UPDATED == True:
            REAL_SETTINGS.setSetting('ClearCache', 'true')
            REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
            xbmc.executebuiltin("RunScript("+__cwd__+"/videowindow.py,-autopatch)")
            xbmc.executebuiltin("RunScript("+__cwd__+"/donordownload.py,-autopatch)")
            TextBox()           
        else:
            #If not Updated, Launch PTVL
            #Enforce settings
            if LOWPOWER == True:
                #Set Configurations Optimized for Low Power OS's
                REAL_SETTINGS.setSetting("EnhancedGuideData", "false")
                REAL_SETTINGS.setSetting("ArtService_Enabled", "false")
                REAL_SETTINGS.setSetting("ShowSeEp", "false")
                REAL_SETTINGS.setSetting("EPGcolor_enabled", "0")
                REAL_SETTINGS.setSetting("EPG.xInfo", "false")
                REAL_SETTINGS.setSetting("UNAlter_ChanBug", "true")
                REAL_SETTINGS.setSetting("sickbeard.enabled", "false")
                REAL_SETTINGS.setSetting("couchpotato.enabled", "false")  
                
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Optimized Configurations Applied", 1000, THUMB) )
                        
            # Clear BCT Folder
            if REAL_SETTINGS.getSetting("ClearBCT") == "true":
                try:
                    shutil.rmtree(BCT_LOC)
                    xbmc.log('script.pseudotv.live-default: BCT Folder Purged!')             
                except Exception,e:
                    xbmc.log('script.pseudotv.live-default: BCT Folder Purge Failed! ' + str(e))  
                    pass

                REAL_SETTINGS.setSetting('ClearBCT', "false")
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", 'BCT Cache Cleared', 1000, THUMB) )
            
            # Clear Artwork Cache Folders
            if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
                try: # Logo Cache
                    shutil.rmtree(LOGO_CACHE_LOC)
                except Exception,e:
                    xbmc.log('script.pseudotv.live-default: Logo Cache Folder Purge Failed! ' + str(e))  
                    pass
                    
                try: # Dynamic Artwork Cache
                    shutil.rmtree(ART_LOC)
                    REAL_SETTINGS.setSetting('ClearLiveArtCache', "true")
                except Exception,e:
                    xbmc.log('script.pseudotv.live-default: Dynamic Artwork Cache Folder Purge Failed! ' + str(e))  
                    pass
                    
                try: # tvdbapi Cache
                    shutil.rmtree(xbmc.translatePath(os.path.join(SETTINGS_LOC,'cache','tvdb_api')))
                except Exception,e:
                    xbmc.log('script.pseudotv.live-default: tvdbapi Cache Folder Purge Failed! ' + str(e))  
                    pass

                REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                xbmc.log('script.pseudotv.live-default: Art Folders Purged!')
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Folders Cleared", 1000, THUMB) )
                
            # Clear System Caches    
            if REAL_SETTINGS.getSetting("ClearCache") == "true":
                quarterly.delete("%") 
                daily.delete("%") 
                weekly.delete("%")
                monthly.delete("%")
                localTV.delete("%")
                liveTV.delete("%")
                YoutubeTV.delete("%")
                RSSTV.delete("%")
                pluginTV.delete("%")
                playonTV.delete("%")
                lastfm.delete("%")
                
                REAL_SETTINGS.setSetting('ClearCache', "false")
                xbmc.log('script.pseudotv.live-default: System Cache Purged!')
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "System Cache Cleared", 1000, THUMB) )

            PseudoTV()
else:
    xbmc.log('script.pseudotv.live - Already running, exiting', xbmc.LOGERROR)
