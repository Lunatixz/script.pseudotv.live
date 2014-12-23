#   Copyright (C) 2014 Kevin S. Graer
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
    
    
import os, sys, re, shutil, buggalo, threading
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.ga import *
from resources.lib.Globals import *
from resources.lib.FileAccess import *
from resources.lib.utils import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import resources.lib.storageserverdummy as StorageServer

# Script constants
__scriptname__ = "PseudoTV Live"
__author__     = "Lunatixz, Jason102"
__url__        = "https://github.com/Lunatixz/script.pseudotv.live"
__settings__   = xbmcaddon.Addon(id='script.pseudotv.live')
__cwd__        = __settings__.getAddonInfo('path')
__version__    = __settings__.getAddonInfo('version')
__language__   = __settings__.getLocalizedString
   
# Buggalo
buggalo.GMAIL_RECIPIENT = 'pseudotvlive@gmail.com'

def PseudoTV():
    import resources.lib.Overlay as Overlay

    try:
        MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.live.TVOverlay.xml", __cwd__, Skin_Select)
    except:
        MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.TVOverlay.xml", __cwd__, Skin_Select)
        
    for curthread in threading.enumerate():
        try:
            log("Active Thread: " + str(curthread.name), xbmc.LOGERROR)

            if curthread.name != "MainThread":
                try:
                    curthread.join()      
                except Exception: 
                    buggalo.onExceptionRaised()
                    pass

                log("Joined " + curthread.name)
                
        except Exception: 
            buggalo.onExceptionRaised()  
            pass
            
    del MyOverlayWindow
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "False")
    
    
# Adapting a solution from ronie (http://forum.xbmc.org/showthread.php?t=97353)
if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
    ShouldRestart = False
    VersionUpdated = False

    if ShouldRestart == False: 
        try:
            if REAL_SETTINGS.getSetting("Auto_Version") != "0":
                # Compare git version with local version.
                log("CheckVersion mode = " + str(REAL_SETTINGS.getSetting("Auto_Version")))
                buggalo.addExtraData('CheckVersion mode = ', str(REAL_SETTINGS.getSetting("Auto_Version")))
                curver = xbmc.translatePath(os.path.join(ADDON_PATH,'addon.xml'))    
                source = open(curver, mode = 'r')
                link = source.read()
                source.close()
                match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
                
                for vernum in match:
                    log("Original Version = " + str(vernum))
                    buggalo.addExtraData('Original Version = ', str(vernum))
                
                if REAL_SETTINGS.getSetting("Auto_Version") == "1":
                    link = Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/master/addon.xml')
                elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
                    link = Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/development/addon.xml')
                        
                link = link.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
                match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
                
                if len(match) > 0:
                    if vernum != str(match[0]):
                        dialog = xbmcgui.Dialog()
                        confirm = xbmcgui.Dialog().yesno('[B]PseudoTV Live Update Available![/B]', "Your version is outdated." ,'The current available version is '+str(match[0]),'Would you like to update now?',"Cancel","Update")
                        if confirm:
                            VersionUpdated = True
                            UPDATEFILES() 
        except Exception:
            buggalo.onExceptionRaised()
            
        log("VersionUpdated = " + str(VersionUpdated))
        #If VersionUpdated: Videowindow/DonorDownload/Changelog/Reboot
        if VersionUpdated == True:
            REAL_SETTINGS.setSetting('ClearCache', 'true')
            REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
            xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-VWautopatch)")
            xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-DDautopatch)")
            TextBox()

            if dlg.yesno("PseudoTV Live", "Restart required after update, Exit XBMC?"):
                xbmc.executebuiltin("Reboot")            
        else:
            #Enforce settings
            if LOWPOWER == True:
                #Set Configurations Optimized for Low Power OS's
                log("LOWPOWER = " + str(LOWPOWER))
                REAL_SETTINGS.setSetting("EnhancedGuideData", "false")
                REAL_SETTINGS.setSetting("ArtService_Enabled", "false")
                REAL_SETTINGS.setSetting("ShowSeEp", "false")
                REAL_SETTINGS.setSetting("EPGcolor_enabled", "0")
                REAL_SETTINGS.setSetting("EPG.xInfo", "false")
                REAL_SETTINGS.setSetting("UNAlter_ChanBug", "true")
                REAL_SETTINGS.setSetting("sickbeard.enabled", "false")
                REAL_SETTINGS.setSetting("couchpotato.enabled", "false")  

                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Optimized Configurations Applied", 1000, THUMB) )
                        
            # Clear BCT Folder
            if REAL_SETTINGS.getSetting("ClearBCT") == "true":
                log('ClearBCT')  
                try:
                    shutil.rmtree(BCT_LOC)     
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", 'BCT Cache Cleared', 1000, THUMB) )
                except:
                    pass       

                REAL_SETTINGS.setSetting('ClearBCT', "false")

            # Clear Artwork Cache Folders
            if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
                log('ClearLiveArt')  
                try:    
                    # Dynamic Artwork Cache
                    shutil.rmtree(ART_LOC)
                    log('Removed ART_LOC')  
                    REAL_SETTINGS.setSetting('ClearLiveArtCache', "true")
                    # Logo Cache
                    shutil.rmtree(LOGO_CACHE_LOC)   
                    log('Removed LOGO_CACHE_LOC')    
                    # tvdbapi Cache
                    shutil.rmtree(xbmc.translatePath(os.path.join(SETTINGS_LOC,'cache','tvdb_api')))  
                    log('Removed tvdb_api')
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Folders Cleared", 1000, THUMB) )
                except:
                    pass
     
                REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                
            # Clear System Caches    
            if REAL_SETTINGS.getSetting("ClearCache") == "true":
                log('ClearCache')  
                quarterly.delete("%") 
                daily.delete("%") 
                weekly.delete("%")
                monthly.delete("%")
                seasonal.delete("%") 
                localTV.delete("%")
                liveTV.delete("%")
                YoutubeTV.delete("%")
                RSSTV.delete("%")
                pluginTV.delete("%")
                playonTV.delete("%")
                lastfm.delete("%")
                
                REAL_SETTINGS.setSetting('ClearCache', "false")
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "System Cache Cleared", 1000, THUMB) )

            #Start PseudoTV
            PseudoTV()
else:
    log('script.pseudotv.live - Already running, exiting', xbmc.LOGERROR)
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Already running, exiting", 1000, THUMB) )