#   Copyright (C) 2014 Kevin S. Graer
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV Live is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV Live is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.


import os, shutil, datetime, random
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from time import sleep


# Plugin Info
ADDON_ID = 'script.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
THUMB = (xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'images')) + '/' + 'icon.png')
xbmc.log("Service Started")

        
def HubSwap(): # Swap Org/Hub versions if 'Hub Installer' found.
    xbmc.log('script.pseudotv.live-Service: HubSwap')
    icon = ADDON_PATH + '/icon'
    HUB = xbmc.getCondVisibility('System.HasAddon(plugin.program.addoninstaller)') == 1
    
    if HUB == True:
        xbmc.log('script.pseudotv.live-Service: HubSwap = Hub Edition')
        
        if REAL_SETTINGS.getSetting('Hub') == 'false':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","Hub-Edition Activated", 4000, THUMB) )
            REAL_SETTINGS.setSetting("Hub","true")
            try:
                xbmcvfs.delete(icon + '.png')
                xbmcvfs.copy(icon + 'HUB', icon + '.png')
                xbmc.executebuiltin("UpdateLocalAddons")
                xbmc.executebuiltin("ReloadSkin()")
            except:
                pass
    else:
        xbmc.log('script.pseudotv.live-Service: HubSwap = Master')
        REAL_SETTINGS.setSetting("Hub","false")
        try:
            xbmcvfs.delete(icon + '.png')
            xbmcvfs.copy(icon + 'OEM', icon + '.png')
            xbmc.executebuiltin("UpdateLocalAddons")
            xbmc.executebuiltin("ReloadSkin()")
        except:
            pass

            
def donorCHK():
    xbmc.log('script.pseudotv.live-Service: donorCHK')
    DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
    DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))
    
    if xbmcvfs.exists(DonorPath) or xbmcvfs.exists(DL_DonorPath):  
        REAL_SETTINGS.setSetting("AT_Donor", "true")
        REAL_SETTINGS.setSetting("COM_Donor", "true")
        REAL_SETTINGS.setSetting("TRL_Donor", "true")
        REAL_SETTINGS.setSetting("CAT_Donor", "true")
        REAL_SETTINGS.setSetting("autoFindCommunity_Source", "1")
    else:
        REAL_SETTINGS.setSetting("AT_Donor", "false")
        REAL_SETTINGS.setSetting("COM_Donor", "false")
        REAL_SETTINGS.setSetting("TRL_Donor", "false")
        REAL_SETTINGS.setSetting("CAT_Donor", "false")
        REAL_SETTINGS.setSetting("autoFindCommunity_Source", "0")
    
        
def autostart():
    xbmc.log('script.pseudotv.live-Service: autostart')   
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
  
donorCHK()
HubSwap()

#Autostart Trigger
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart() 