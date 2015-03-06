#   Copyright (C) 2015 Kevin S. Graer
#
#
# This file is part of PseudoTV Min.
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
# along with PseudoTV Min.  If not, see <http://www.gnu.org/licenses/>.
    
    
import os, sys, re, shutil, threading
import xbmc, xbmcgui, xbmcaddon, xbmcvfs


from resources.lib.Globals import *
from resources.lib.FileAccess import *
from resources.lib.utils import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import resources.lib.storageserverdummy as StorageServer

# Script constants
__scriptname__ = "PseudoTV Min"
__author__     = "Enigma0, Lunatixz, Jason102"
__url__        = "https://github.com/Enigma0/script.pseudotv.min"
__settings__   = xbmcaddon.Addon(id='script.pseudotv.min')
__cwd__        = __settings__.getAddonInfo('path')
__version__    = __settings__.getAddonInfo('version')
__language__   = __settings__.getLocalizedString
       

def PseudoTV():
    xbmcgui.Window(10000).setProperty("PseudoTVRunning", "True")
    xbmc.log('PseudoTV Min Starting...')
    
    import resources.lib.Overlay as Overlay
    
    MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.min.TVOverlay.xml", __cwd__, Skin_Select)
    for curthread in threading.enumerate():
        try:
            logGlob("Active Thread: " + str(curthread.name))

            if curthread.name != "MainThread":
                try:
                    curthread.join()      
                except: 
                    pass

                logGlob("Joined " + curthread.name)
                
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
    
    if PTVL_Version != __version__:
        ClearPlaylists()
        REAL_SETTINGS.setSetting('ClearCache', 'true')
        REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
        REAL_SETTINGS.setSetting("PTVL_Version", __version__)
        
        # Auto VideoWindow Patch.
        VideoWindow()
        
        if dlg.yesno("PseudoTV Min", "It may be necessary to restart Kodi to re-apply video patch after updating.","","Would you like to exit Kodi now?","No","Exit Now"):
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "Exiting...", 1000, THUMB) )
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Quit(),%d,true)" % ( 0.5, ) )
    
    #Check if Outdated/Install Repo
    updating = VersionCompare()
    
    if updating == False:
        # #Check Messaging Service todo
        # Announcement()

        # Auto VideoWindow Patch.
        VideoWindow()
        
        # Clear System Caches    
        if REAL_SETTINGS.getSetting("ClearCache") == "true":
            logGlob('ClearCache')  
            quarterly.delete("%") 
            bidaily.delete("%") 
            daily.delete("%") 
            weekly.delete("%")
            seasonal.delete("%") 
            monthly.delete("%")
            localTV.delete("%")
            REAL_SETTINGS.setSetting('ClearCache', "false")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "System Cache Cleared", 1000, THUMB) )
        
        # Clear Artwork Folders
        if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
            logGlob('ClearLiveArt')  
            try:    
                # Dynamic Artwork Cache
                shutil.rmtree(ART_LOC)
                logGlob('Removed ART_LOC')  
                REAL_SETTINGS.setSetting('ClearLiveArtCache', "true") 
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "Artwork Folder Cleared", 1000, THUMB) )
            except:
                pass
            REAL_SETTINGS.setSetting('ClearLiveArt', "false")
            
        #Enforce settings
        '''if LOWPOWER == True:
            #Set Configurations Optimized for LowPower Hardware.
            logGlob("LOWPOWER = " + str(LOWPOWER))
            REAL_SETTINGS.setSetting("EnhancedGuideData", "false")
            REAL_SETTINGS.setSetting("ArtService_Enabled", "false")
            REAL_SETTINGS.setSetting("ShowSeEp", "false")
            REAL_SETTINGS.setSetting("EPGcolor_enabled", "0")
            REAL_SETTINGS.setSetting("EPG.xInfo", "false")
            REAL_SETTINGS.setSetting("UNAlter_ChanBug", "true")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "Optimized Configurations Applied", 1000, THUMB) )
        else:
            REAL_SETTINGS.setSetting("ArtService_Enabled", "true")'''
        
        #Start PseudoTV
        PseudoTV()
    else:
        GlobalFileLock.close()
        #xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "Exiting...", 1000, THUMB) )
        #xbmc.executebuiltin("XBMC.UpdateLocalAddons()")
else:
    logGlob('Already running, exiting', xbmc.LOGERROR)
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Min", "Already running...", 1000, THUMB) )