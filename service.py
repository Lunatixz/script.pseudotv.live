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
from resources.lib.ChannelList import *
from resources.lib.Artdownloader import *
from resources.lib.utils import *
from resources.lib.EPGWindow import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import resources.lib.storageserverdummy as StorageServer
    
# Plugin Info
ADDON_ID = 'script.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
xbmc.log(ADDON_ID +' '+ ADDON_NAME +' '+ ADDON_PATH +' '+ ADDON_VERSION)
xbmc.log("script.pseudotv.live-service: Service Started...")

chanlist = ChannelList()
Artdown = Artdownloader()


def Autovideowindow():
    xbmc.log('script.pseudotv.live-service: Autovideowindow')
    xbmc.executebuiltin('XBMC.RunScript(' + ADDON_PATH + '/videowindow.py, -autopatch)')

        
def HubSwap(): # Swap Org/Hub versions if 'Hub Installer' found.
    xbmc.log('script.pseudotv.live-service: HubSwap')
        
    try:#unknown Amazon firetv error encountered here, requires investigation
        icon = ADDON_PATH + '/icon'
        HUB = chanlist.plugin_ok('plugin.program.addoninstaller')
        if HUB == True:
            xbmc.log('script.pseudotv.live-service: HubSwap - Hub Edition')
            
            if REAL_SETTINGS.getSetting('Hub') == 'false':
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","Hub-Edition Activated", 4000, THUMB) )
                
                REAL_SETTINGS.setSetting("Hub","true")
                try:
                    xbmcvfs.delete(icon + '.png')
                except:
                    pass
                try:
                    xbmcvfs.copy(icon + 'HUB', icon + '.png')
                except:
                    pass      
        else:
            xbmc.log('script.pseudotv.live-service: HubSwap - Master')
            REAL_SETTINGS.setSetting("Hub","false")
            try:
                xbmcvfs.delete(icon + '.png')
            except:
                pass
            try:
                xbmcvfs.copy(icon + 'OEM', icon + '.png')
            except:
                pass      
    except:
        REAL_SETTINGS.setSetting("Hub","false")
        pass

          
def donorCHK():
    xbmc.log('script.pseudotv.live-service: donorCHK')
    
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
    xbmc.log('script.pseudotv.live-service: autostart')   
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')


#Startup Checks
HubSwap()
donorCHK()

#Reset Running Checks
REAL_SETTINGS.setSetting('SyncXMLTV_Running', "false")
REAL_SETTINGS.setSetting('ArtService_Running', "false")

#Autostart Trigger
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart()    
    
# #Monitor for settings change
# try:
  # class MyMonitor( xbmc.Monitor ):
    # def __init__( self, *args, **kwargs ):
        # xbmc.Monitor.__init__( self )
        # xbmc.log('script.pseudotv.live-service: MyMonitor - init')   
        
    # def onSettingsChanged( self ):
        # xbmc.log('script.pseudotv.live-service: MyMonitor - HubSwap') 
        # HubSwap()
        # Autovideowindow()
        
  # xbmc_monitor = MyMonitor()
# except:
    # MSG = 'Using Eden API - you need to restart addon for changings to apply' 
    # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live",MSG, 4000, THUMB) )
  
# while not xbmc.abortRequested:
  # xbmc.sleep(1000)