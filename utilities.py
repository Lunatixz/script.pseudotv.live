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
        
    
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, time, fileinput, re
import urllib, urllib2

from resources.lib.Globals import *


def showText(heading, text):
    log("showText")
    id = 10147
    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)
    win = xbmcgui.Window(id)
    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            return
        except:
            pass
            
            
def showChangelog(addonID=None):
    log("showChangelog")
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)
        f = open(ADDON.getAddonInfo('changelog'))
        text  = f.read()
        title = "Changelog - PseudoTV Live"
        showText(title, text)
    except:
        pass


#DonorDownload
DonorURLPath = (PTVLURL + 'Donor.py')
LinkURLPath = (PTVLURL + 'links.py')
LinkPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'links.py'))
DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))


def DDautopatch():
    log("DDautopatch")
    REAL_SETTINGS.setSetting("AT_Donor", "false")
    REAL_SETTINGS.setSetting("COM_Donor", "false")
    REAL_SETTINGS.setSetting("TRL_Donor", "false")
    REAL_SETTINGS.setSetting("CAT_Donor", "false")

    try:
        if xbmcvfs.exists(xbmc.translatePath(DL_DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DL_DonorPath))
            log('Removed DL_DonorPath')  
            
        if xbmcvfs.exists(xbmc.translatePath(DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DonorPath))  
            log('Removed DonorPath')  
    except Exception:
        pass
        
    try:
        urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
        if xbmcvfs.exists(DL_DonorPath):
            log('DL_DonorPath Downloaded')  
            REAL_SETTINGS.setSetting("AT_Donor", "true")
            REAL_SETTINGS.setSetting("COM_Donor", "true")
            REAL_SETTINGS.setSetting("TRL_Donor", "true")
            REAL_SETTINGS.setSetting("CAT_Donor", "true")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Donor Autoupdate Complete", 4000, THUMB) ) 
    except Exception:
        pass
    

def DonorDownloader():
    log('DonorDownloader')
    REAL_SETTINGS.setSetting("AT_Donor", "false")
    REAL_SETTINGS.setSetting("COM_Donor", "false")
    REAL_SETTINGS.setSetting("TRL_Donor", "false")
    REAL_SETTINGS.setSetting("CAT_Donor", "false")
    Install = False
    Verified = False
    InstallStatusMSG = 'Activate'  
    
    if xbmcvfs.exists(DonorPath):
        InstallStatusMSG = 'Update'
        if dlg.yesno("PseudoTV Live", str(InstallStatusMSG) + " Donor Features?"):
            try:
                xbmcvfs.delete(xbmc.translatePath(DonorPath))
                log('Removed DonorPath')  
                Install = True
            except Exception: 
                pass
    else:  
        Install = True
    
    if Install == True:
        try:                   
            urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
            if xbmcvfs.exists(DL_DonorPath):
                log('DL_DonorPath Downloaded')  
                REAL_SETTINGS.setSetting("AT_Donor", "true")
                REAL_SETTINGS.setSetting("COM_Donor", "true")
                REAL_SETTINGS.setSetting("TRL_Donor", "true")
                REAL_SETTINGS.setSetting("CAT_Donor", "true")
                xbmc.executebuiltin("UpdateLocalAddons")
            
                if REAL_SETTINGS.getSetting('AT_Donor') and REAL_SETTINGS.getSetting('COM_Donor') and REAL_SETTINGS.getSetting('TRL_Donor') and REAL_SETTINGS.getSetting('CAT_Donor'):
                    Verified = True

            if Verified == True:
                MSG = "Donor Features " + str(InstallStatusMSG) + "d"
            else:
                MSG = "Donor Features Not " + str(InstallStatusMSG) + "d"
                
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) ) 
            REAL_SETTINGS.openSettings()
        except Exception:
            pass
           
            
def LogoDownloader():
    log('LogoDownloader')
    LogoPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))
    
    if dlg.yesno("PseudoTV Live", "Download Color Logos or No, Download Mono Logos"):
        LogoDEST = LogoPath + '/PTVL_Color.zip'
        i = 0
    else:
        LogoDEST = LogoPath + '/PTVL_Mono.zip'
        i = 1

    if not DEFAULT_LOGO_LOC:
        xbmcvfs.mkdirs(DEFAULT_LOGO_LOC)
        
    try:
        xbmcvfs.delete(xbmc.translatePath(LinkPath))
        log('Removed LinkPath')  
    except Exception:
        pass
         
    try:
        urllib.urlretrieve(LinkURLPath, (xbmc.translatePath(LinkPath)))
        f = open((xbmc.translatePath(LinkPath)), "r")
        linesLST = f.readlines()
        LogoURLPath = linesLST[i] 
        download(LogoURLPath, LogoDEST)
        all(LogoDEST, LogoPath)
        REAL_SETTINGS.setSetting("ChannelLogoFolder", DEFAULT_LOGO_LOC)
        
        try:
            xbmcvfs.delete(xbmc.translatePath(LinkPath))
            log('Removed LinkPath')  
            xbmcvfs.delete(LogoDEST)
            log('Removed LogoDEST')  
        except Exception:
            pass
            
    except Exception:
        pass
       
    # Return to PTVL Settings
    REAL_SETTINGS.openSettings()
        
        
if sys.argv[1] == '-DDautopatch':
    DDautopatch()   
elif sys.argv[1] == '-DonorDownloader':
    if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
        DonorDownloader()  
    else:
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Not available while running.", 1000, THUMB) )
elif sys.argv[1] == '-LogoDownloader':
    LogoDownloader()
elif sys.argv[1] == '-SimpleDownloader':
    xbmcaddon.Addon(id='script.module.simple.downloader').openSettings()
elif sys.argv[1] == '-showChangelog':
    showChangelog(ADDON_ID)
