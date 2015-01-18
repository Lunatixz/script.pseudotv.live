#   Copyright (C) 2015 Kevin S. Graer
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
       
# Buggalo gmail
buggalo.GMAIL_RECIPIENT = 'pseudotvlive@gmail.com'

def PseudoTV():
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
    import resources.lib.Overlay as Overlay
    
    MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.live.TVOverlay.xml", __cwd__, Skin_Select)

    for curthread in threading.enumerate():
        try:
            log("Active Thread: " + str(curthread.name), xbmc.LOGERROR)

            if curthread.name != "MainThread":
                try:
                    curthread.join()      
                except: 
                    pass

                log("Joined " + curthread.name)
                
        except: 
            pass
            
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "False")
    del MyOverlayWindow

    
# Adapting a solution from ronie (http://forum.xbmc.org/showthread.php?t=97353)
if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":   
    try:
        PTVL_Version = REAL_SETTINGS.getSetting("PTVL_Version")
    except:
        REAL_SETTINGS.setSetting("PTVL_Version", __version__)
        PTVL_Version = REAL_SETTINGS.getSetting("PTVL_Version")
        pass  
    
    CurSkin = REAL_SETTINGS.getSetting("SkinSelector")
    try:
        LastSkin = REAL_SETTINGS.getSetting("LastSkin")
    except:
        REAL_SETTINGS.setSetting("LastSkin", CurSkin)
        LastSkin = REAL_SETTINGS.getSetting("LastSkin")
        pass

    if PTVL_Version != __version__:
        ClearPlaylists()
        REAL_SETTINGS.setSetting('ClearCache', 'true')
        REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
        REAL_SETTINGS.setSetting("PTVL_Version", __version__)
        xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-VWautopatch)")
        xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-DDautopatch)")
        
        #call showChangeLog like this to workaround bug in openElec, *Thanks spoyser
        xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-showChangelog)")
        
        if dlg.yesno("PseudoTV Live", "System Reboot recommend after update, Exit XBMC?"):
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Quit(),%d,true)" % ( 0.5, ) )
            
    else:
        #Check if Outdated/Install Repo
        VersionCompare()
        
        # #Check Messaging Service todo
        # Announcement()

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
       
        #TEMP PTVL SKIN LOCK/Disable art spooling, no longer needed?
        REAL_SETTINGS.setSetting('SkinSelector', "3")
        REAL_SETTINGS.setSetting("ArtService_Enabled", "false")
           
        # Clear BCT Caches
        if REAL_SETTINGS.getSetting("ClearBCT") == "true":
            log('ClearBCT')  
            bumpers.delete("%")
            ratings.delete("%")
            commercials.delete("%")
            trailers.delete("%")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", 'BCT Cache Cleared', 1000, THUMB) )
            REAL_SETTINGS.setSetting('ClearBCT', "false")

        # Clear Artwork Folders
        if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
            log('ClearLiveArt')  
            try:    
                # Dynamic Artwork Cache
                shutil.rmtree(ART_LOC)
                log('Removed ART_LOC')  
                REAL_SETTINGS.setSetting('ClearLiveArtCache', "true") 
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Folder Cleared", 1000, THUMB) )
            except:
                pass
            REAL_SETTINGS.setSetting('ClearLiveArt', "false")
            
        # Clear Artwork Cache
        if REAL_SETTINGS.getSetting("ClearLiveArtCache") == "true":
            artwork.delete("%") 
            artwork1.delete("%")
            artwork2.delete("%")
            artwork3.delete("%")
            artwork4.delete("%")
            artwork5.delete("%")
            artwork6.delete("%")
            log('ArtCache Purged!')
            REAL_SETTINGS.setSetting('ClearLiveArtCache', "false")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Cache Cleared", 1000, THUMB) )

        #Enforce settings
        if LOWPOWER == True:
            #Set Configurations Optimized for LowPower Hardware.
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
            
        # Trigger Auto VideoWindow Patch on skin change.
        if LastSkin != CurSkin:
            REAL_SETTINGS.setSetting("LastSkin", CurSkin)
            xbmc.executebuiltin("RunScript("+__cwd__+"/utilities.py,-VWautopatch)")

        #Start PseudoTV
        PseudoTV()
else:
    log('script.pseudotv.live - Already running, exiting', xbmc.LOGERROR)
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Already running" , "Try Rebooting?", 1000, THUMB) )