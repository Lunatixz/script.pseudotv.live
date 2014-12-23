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


import os, shutil, datetime, random, buggalo
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
log("Service Started")

chanlist = ChannelList()
Artdown = Artdownloader()


def Autovideowindow():
    log('Autovideowindow')
    xbmc.executebuiltin('XBMC.RunScript(' + ADDON_PATH + '/utilities.py, -VWautopatch)')

        
def HubSwap(): # Swap Org/Hub versions if 'Hub Installer' found.
    log('HubSwap')
    icon = ADDON_PATH + '/icon'
    HUB = chanlist.plugin_ok('plugin.program.addoninstaller')
    if HUB == True:
        log('HubSwap - Hub Edition')
        
        if REAL_SETTINGS.getSetting('Hub') == 'false':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","Hub-Edition Activated", 4000, THUMB) )
            REAL_SETTINGS.setSetting("Hub","true")
            try:
                xbmcvfs.delete(icon + '.png')
                xbmcvfs.copy(icon + 'HUB', icon + '.png')
                xbmc.executebuiltin("UpdateLocalAddons")
                xbmc.executebuiltin("ReloadSkin()")
            except Exception:
                buggalo.onExceptionRaised()    
    else:
        log('HubSwap - Master')
        REAL_SETTINGS.setSetting("Hub","false")
        try:
            xbmcvfs.delete(icon + '.png')
            xbmcvfs.copy(icon + 'OEM', icon + '.png')
            xbmc.executebuiltin("UpdateLocalAddons")
            xbmc.executebuiltin("ReloadSkin()")
        except Exception:
            buggalo.onExceptionRaised()     

            
def donorCHK():
    log('donorCHK')
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
    log('autostart')   
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')

#Autostart Trigger
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart()   

# #Service loop    
# class Service:
    # def __init__(self):
        # log('Service - init')
        # while not xbmc.abortRequested:
            # try:
                # if REAL_SETTINGS.getSetting('Hub') == 'false':
                    # HubSwap()  
            # except Exception:
                # REAL_SETTINGS.setSetting("Hub","false")
                # buggalo.onExceptionRaised()
            # xbmc.sleep(10000)
 
#Startup Checks
# Service()
donorCHK()

# #Monitor for settings change
# try:
  # class MyMonitor( xbmc.Monitor ):
    # def __init__( self, *args, **kwargs ):
        # xbmc.Monitor.__init__( self )
        # log('MyMonitor - init')
        
    # def onSettingsChanged( self ):
        # log('onSettingsChanged')
        # if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True": 
            # if REAL_SETTINGS.getSetting("videowindow_" + Skin_Select) == "false":
                # Autovideowindow()  
        
  # xbmc_monitor = MyMonitor()
# except:
    # MSG = 'Using Eden API - you need to restart addon for changings to apply' 
    # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live",MSG, 4000, THUMB) )
    
# while not xbmc.abortRequested:
    # xbmc.sleep(1000)