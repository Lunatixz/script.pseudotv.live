# Copyright 2011-2014 Jason Anderson, Kevin, Lunatixz, Martijn Kaijser,
# Tommy Winther, Tristan Fischer.
#
# This file is part of PseudoTV Live. <https://github.com/Lunatixz/script.pseudotv.live>.
#
# PseudoTV Live is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV Live is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live. If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, time, fileinput, re
import urllib, urllib2

from resources.lib.Globals import *
from resources.lib.FileAccess import FileLock, FileAccess
from resources.lib.utils import *

try:
    import Donor
    from Donor import *
except:
    pass
    
#Globals
UserPass = REAL_SETTINGS.getSetting('Donor_UP')
BaseURL = ('http://'+UserPass+'@ptvl.comeze.com/PTVL/')

DonorDownloaded = False
LogoDownloaded = False
BumperDownloaded = False

#Donor
DonorURLPath = (BaseURL + 'Donor.py')
LinkURLPath = (BaseURL + 'links.py')
LinkPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'links.py'))
DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))


def autopatch():
    xbmc.log('script.pseudotv.live-donordownload: autopatch')
    MSG = 'Donor Autoupdate Complete'
    
    try:
        os.remove(xbmc.translatePath(DL_DonorPath))
    except:
        pass
        
    try:
        os.remove(xbmc.translatePath(DonorPath))  
    except:
        pass
        
    try:
        urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
        xbmc.log('script.pseudotv.live-donordownload: autopatch, Downloading DL_DonorPath')   
        if xbmcvfs.exists(DL_DonorPath):
            REAL_SETTINGS.setSetting("AT_Donor", "true")
            REAL_SETTINGS.setSetting("COM_Donor", "true")
            REAL_SETTINGS.setSetting("TRL_Donor", "true")
            REAL_SETTINGS.setSetting("CAT_Donor", "true")
            if REAL_SETTINGS.getSetting('AT_Donor') and REAL_SETTINGS.getSetting('COM_Donor') and REAL_SETTINGS.getSetting('TRL_Donor') and REAL_SETTINGS.getSetting('CAT_Donor'):
                xbmc.log('script.pseudotv.live-donordownload: autopatch, Settings.xml Patched')
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) ) 
    except:
        pass
    

def DonorDownloader():
    xbmc.log('script.pseudotv.live-donordownload: DonorDownloader')
    Install = False
    Verified = False
    InstallStatusMSG = 'Activate'  
    if xbmcvfs.exists(DonorPath):
        InstallStatusMSG = 'Update'
        if dlg.yesno("PseudoTV Live", str(InstallStatusMSG) + " Donor Features?"):
            try:
                os.remove(xbmc.translatePath(DonorPath))
                xbmc.log('script.pseudotv.live-donordownload: Removed DonorPath')  
                Install = True
            except Exception,e:
                xbmc.log('script.pseudotv.live-donordownload: Removed DonorPath Failed! ' + str(e)) 
                pass
    else:  
        Install = True
    
    if Install == True:
        xbmc.log('script.pseudotv.live-donordownload: DonorDownload')    
        try:                   
            urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
            xbmc.log('script.pseudotv.live-donordownload: Downloading DL_DonorPath')   
            if xbmcvfs.exists(DL_DonorPath):
                REAL_SETTINGS.setSetting("AT_Donor", "true")
                REAL_SETTINGS.setSetting("COM_Donor", "true")
                REAL_SETTINGS.setSetting("TRL_Donor", "true")
                REAL_SETTINGS.setSetting("CAT_Donor", "true")
            
                if REAL_SETTINGS.getSetting('AT_Donor') and REAL_SETTINGS.getSetting('COM_Donor') and REAL_SETTINGS.getSetting('TRL_Donor') and REAL_SETTINGS.getSetting('CAT_Donor'):
                    Verified = True
                    xbmc.log('script.pseudotv.live-donordownload: Settings.xml Patched')

            if Verified == True:
                MSG = "Donor Features " + str(InstallStatusMSG) + "d"
            else:
                MSG = "Donor Features Not " + str(InstallStatusMSG) + "d"
                
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) ) 
            REAL_SETTINGS.openSettings()

        except Exception,e:
            xbmc.log('script.pseudotv.live-donordownload: Downloading DL_DonorPath Failed! ' + str(e))  
            pass
        
def BumperDownloader():
    xbmc.log('script.pseudotv.live-donordownload: BumperDownloader')
    
    BUMPERDEST = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'Bumpers.zip'))
    BumperPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))
     
    try:
        os.remove(BUMPERDEST)
    except:
        pass
    
    if dlg.yesno("PseudoTV Live", "Download Bumpers?", "700Mb File"):
        try:
            os.remove(xbmc.translatePath(LinkPath))
        except:
            pass
         
        try:       
            urllib.urlretrieve(LinkURLPath, (xbmc.translatePath(LinkPath)))
            f = FileAccess.open((xbmc.translatePath(LinkPath)), "r")
            linesLST = f.readlines()
            BumperURLPath = linesLST[0]
            
            download(BumperURLPath, BUMPERDEST)
            all(BUMPERDEST, BumperPath)
                
            REAL_SETTINGS.setSetting("bumpers", "true")
            REAL_SETTINGS.setSetting("bumpersfolder", BUMPER_LOC)
            REAL_SETTINGS.setSetting("numbumpers", "1")
            
            os.remove(BUMPERDEST)
        except:
            pass
    
        REAL_SETTINGS.openSettings()
        
    else:
        REAL_SETTINGS.openSettings()
            
            
def LogoDownloader():
    xbmc.log('script.pseudotv.live-donordownload: LogoDownloader')
    
    LogoPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))
    
    if dlg.yesno("PseudoTV Live", "Download Color Logos or No, Download Mono Logos", ""):
        LogoDEST = LogoPath + '/PTVL_Color.zip'
        i = 1
    else:
        LogoDEST = LogoPath + '/PTVL_Mono.zip'
        i = 2

    if not DEFAULT_LOGO_LOC:
        os.makedirs(DEFAULT_LOGO_LOC)
        
    try:
        os.remove(xbmc.translatePath(LinkPath))
    except:
        pass
         
    try:
        urllib.urlretrieve(LinkURLPath, (xbmc.translatePath(LinkPath)))
        f = FileAccess.open((xbmc.translatePath(LinkPath)), "r")
        linesLST = f.readlines()
        LogoURLPath = linesLST[i] 
        download(LogoURLPath, LogoDEST)
        all(LogoDEST, LogoPath)
        REAL_SETTINGS.setSetting("ChannelLogoFolder", DEFAULT_LOGO_LOC)
        os.remove(LogoDEST)
    except:
        pass
        
    REAL_SETTINGS.openSettings()
        
def CEDownloader():
    xbmc.log('script.pseudotv.live-donordownload: CEDownloader')

    CEURL = (BaseURL + 'CEURL.txt')
    CEDEST = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'PTVL_Cinema_Experience_Pack.zip'))
    CEPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))

    if dlg.yesno("PseudoTV Live", "Download Cinema Experience Pack", ""):
        
        try:
            os.remove(xbmc.translatePath(LinkPath))
        except:
            pass
            
        try:
            urllib.urlretrieve(LinkURLPath, (xbmc.translatePath(LinkPath)))
            f = FileAccess.open((xbmc.translatePath(LinkPath)), "r")
            linesLST = f.readlines()
            CEURLPath = linesLST[3]
            
            download(CEURLPath, CEDEST)
            all(CEDEST, CEPath)
            
            if xbmcvfs.exists(CE_LOC):
                REAL_SETTINGS.setSetting("CinemaPack", "true")
            else:
                REAL_SETTINGS.setSetting("CinemaPack", "false")

            os.remove(CEDEST)
        except:
            pass  
            
            REAL_SETTINGS.openSettings()
    else:
        REAL_SETTINGS.openSettings()
       
       
if sys.argv[1] == '-autopatch':
    autopatch()   
elif sys.argv[1] == '-DonorDownloader':
    DonorDownloader()
elif sys.argv[1] == '-LogoDownloader':
    LogoDownloader()
elif sys.argv[1] == '-BumperDownloader':
    BumperDownloader()
elif sys.argv[1] == '-CEDownloader':
    CEDownloader()
elif sys.argv[1] == '-SimpleDownloader':
    xbmcaddon.Addon(id='script.module.simple.downloader').openSettings()
    
