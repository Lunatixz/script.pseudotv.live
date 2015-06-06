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
import os, sys, time, urllib

from resources.lib.Globals import *
from resources.lib.utils import *

# showInfo
def showText(heading, text):
    xbmc.log('script.pseudotv.live-utilities: showText')
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
            
def showInfo(addonID=None, type='changelog'):
    xbmc.log('script.pseudotv.live-utilities: showInfo')
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)
        if type == 'changelog':
            title = "PseudoTV Live - Changelog"
            f = open(ADDON.getAddonInfo('changelog'))
        if type == 'readme':
            title = "PseudoTV Live - Readme"
            f = open(os.path.join(ADDON_PATH,'README.md'))
        text  = f.read()
        showText(title, text)
    except:
        pass      

#DonorDownload
DonorURLPath = (PTVLURL + 'Donor.py')
LinkPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'links.py'))
DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))

def DDautopatch():
    xbmc.log('script.pseudotv.live-utilities: DDautopatch')
    REAL_SETTINGS.setSetting("AT_Donor", "false")
    REAL_SETTINGS.setSetting("COM_Donor", "false")
    REAL_SETTINGS.setSetting("TRL_Donor", "false")
    REAL_SETTINGS.setSetting("CAT_Donor", "false")

    try:
        if xbmcvfs.exists(xbmc.translatePath(DL_DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DL_DonorPath))
            xbmc.log('script.pseudotv.live-utilities: DDautopatch, Removed DL_DonorPath')
            
        if xbmcvfs.exists(xbmc.translatePath(DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DonorPath))  
            xbmc.log('script.pseudotv.live-utilities: DDautopatch, Removed DonorPath')
    except:
        pass
        
    try:
        urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
        if xbmcvfs.exists(DL_DonorPath):
            xbmc.log('script.pseudotv.live-utilities: DDautopatch, DL_DonorPath Downloaded')
            REAL_SETTINGS.setSetting("AT_Donor", "true")
            REAL_SETTINGS.setSetting("COM_Donor", "true")
            REAL_SETTINGS.setSetting("TRL_Donor", "true")
            REAL_SETTINGS.setSetting("CAT_Donor", "true")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Donor Autoupdate Complete", 4000, THUMB) ) 
    except:
        pass

def DonorDownloader():
    xbmc.log('script.pseudotv.live-utilities: DonorDownloader')
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
                xbmc.log('script.pseudotv.live-utilities: DonorDownloader, Removed DonorPath')
                Install = True
            except Exception: 
                pass
    else:  
        Install = True
    
    if Install == True:
        try:                   
            urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
            if xbmcvfs.exists(DL_DonorPath):
                xbmc.log('script.pseudotv.live-utilities: DonorDownloader, DL_DonorPath Downloaded')
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
            
            # Return to PTVL Settings
            REAL_SETTINGS.openSettings()
        except:
            pass
         
def LogoDownloader():
    xbmc.log('script.pseudotv.live-utilities: LogoDownloader')
    if dlg.yesno("PseudoTV Live", "Download Color Logos or No, Download Mono Logos"):
        LogoDEST = os.path.join(LOCK_LOC,'PTVL_Color.zip')
        URLPath = PTVLURL + 'PTVL_Color.zip'
    else:
        LogoDEST = os.path.join(LOCK_LOC,'PTVL_Mono.zip')
        URLPath = PTVLURL + 'PTVL_Mono.zip'

    try:
        if not xbmcvfs.exists(LOCK_LOC):
            xbmcvfs.mkdir(LOCK_LOC)

        xbmcvfs.delete(xbmc.translatePath(LogoDEST))
    except:
        pass
         
    try:
        download(URLPath, LogoDEST)
        all(LogoDEST, LOCK_LOC)
        REAL_SETTINGS.setSetting("ChannelLogoFolder", LogoDEST)
        xbmcvfs.delete(LogoDEST)
    except:
        pass
        
    # Return to PTVL Settings
    REAL_SETTINGS.openSettings()
 
def DeleteSettings2():
    xbmc.log('script.pseudotv.live-utilities: DeleteSettings2')
    if xbmcvfs.exists(os.path.join(SETTINGS_LOC, 'settings2.xml')):
        if dlg.yesno("PseudoTV Live", "Delete Current Channel Configurations?"):
            try:
                xbmcvfs.delete(xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml')))
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Channel Configurations Cleared", 1000, THUMB) )
            except:
                pass

    # Return to PTVL Settings
    REAL_SETTINGS.openSettings()
    
    
if sys.argv[1] == '-DDautopatch':
    DDautopatch()   
elif sys.argv[1] == '-DonorDownloader':
    DonorDownloader()  
elif sys.argv[1] == '-LogoDownloader':
    LogoDownloader()
elif sys.argv[1] == '-SimpleDownloader':
    xbmcaddon.Addon(id='script.module.simple.downloader').openSettings()
elif sys.argv[1] == '-showChangelog':
    showInfo(ADDON_ID, 'changelog') 
elif sys.argv[1] == '-showReadme':
    showInfo(ADDON_ID, 'readme') 
elif sys.argv[1] == '-DeleteSettings2':
    DeleteSettings2()
elif sys.argv[1] == '-repairSettings2':
    from resources.lib.Settings import *
    Setfun = Settings()
    Setfun.repairSettings()