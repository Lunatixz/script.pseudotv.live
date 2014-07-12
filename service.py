# Copyright 2011-2014 Blazetamer, Jason Anderson, Kevin, Lunatixz,
# Martijn Kaijser, Tommy Winther & Tristan Fischer.
#
# This file is part of PseudoTV Live. <https://github.com/Lunatixz/script.pseudotv.live>
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

import os, shutil, datetime, random, threading
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from time import sleep
from resources.lib.Globals import *
from resources.lib.ChannelList import *
from resources.lib.Artdownloader import *
from resources.lib.FileAccess import FileLock, FileAccess

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

global PseudoTVRunning
PseudoTVRunning = False

Restart = REAL_SETTINGS.getSetting('Auto_Restart')
Enabled = REAL_SETTINGS.getSetting('Auto_Start')
Msg = REAL_SETTINGS.getSetting('notify')
IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
xbmc.log("script.pseudotv.live-service: Service Started...")


if xbmcgui.Window(10000).getProperty("PseudoTVRunning") == "True":
    if (ArtService_Background == 'false'):
        PseudoTVRunning = True
        
def ThreadTimer(object, seconds, function):
    print 'ThreadTimer'
    objectname = str(object)
    object = threading.Timer(float(seconds), function)
    object.name = objectname
    object.start()    
    
def ChangeMonitor(seconds=900):
    print 'ChangeMonitor' 
    if (ArtService_Enabled == 'true'): 
        ChangeMonitorThread = threading.Timer(float(seconds), ChangeMonitor)
        ChangeMonitorThread.name = 'script.pseudotv.live-service: ChangeMonitor_Thread'
        ChangeMonitorThread.start()
        SkinChange()
    
def ArtServiceTimer(time=1800):
    print 'ArtServiceTimer'
    global PseudoTVRunning 
    if not PseudoTVRunning:
        now  = datetime.datetime.today()
        Artdown = Artdownloader()
        ArtServiceTimerThread = threading.Timer(float(time), ArtServiceTimer)
        ArtServiceTimerThread.name = 'script.pseudotv.live-service: ArtServiceTimer_Thread'
        ArtServiceTimerThread.start()
        try:
            ArtService_LastRun = REAL_SETTINGS.getSetting('ArtService_LastRun')
            ArtService_LastRun = ArtService_LastRun.split('.')[0]
            ArtService_LastRun = datetime.datetime.strptime(ArtService_LastRun, '%Y-%m-%d %H:%M:%S')
            ArtService_NextRun = (ArtService_LastRun + datetime.timedelta(seconds=ArtService_Timer))
        except:
            ArtService_NextRun = now
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(now))
            pass
            
        if now >= ArtService_NextRun:  
            Artdown.ArtService()       
       
def ForceArtService():
    print 'ForceArtService'
    Artdown = Artdownloader() 
    Artdown.ArtService()
         
         
def SkinChange():
    SkinChanged = False
    PseudoTVSkin_Num = int(REAL_SETTINGS.getSetting('SkinSelector'))
    try:
        PseudoTVSkin_LastNum = int(REAL_SETTINGS.getSetting('PseudoTVSkin_LastNum'))
         
        if PseudoTVSkin_Num != PseudoTVSkin_LastNum: # Force Art service after skin change.
            SkinChanged = True
            REAL_SETTINGS.setSetting("PseudoTVSkin_LastNum",str(PseudoTVSkin_Num))
            ForceArtService()
        #Disable art service for non compatible skins
        if PseudoTVSkin_Num == 0:
            ArtService_Enabled = 'false'
    except:
        REAL_SETTINGS.setSetting("PseudoTVSkin_LastNum",str(PseudoTVSkin_Num))
        pass
        
    print 'SkinChanged = ' + str(SkinChanged)
    return SkinChanged
   
           
def HubSwap():
    xbmc.log('script.pseudotv.live-service: HubSwap')
    icon = ADDON_PATH + '/icon'
    chanlist = ChannelList()
    HUB = chanlist.plugin_ok('plugin.program.addoninstaller')
    
    if HUB == True:
        xbmc.log('script.pseudotv.live-service: HubSwap - Hub Edition')
        REAL_SETTINGS.setSetting("Hub","true")
        try:
            os.remove(icon + '.png')
        except:
            pass
        try:
            shutil.copy2(icon + 'HUB', icon + '.png')
        except:
            pass   
            
    else:
        xbmc.log('script.pseudotv.live-service: HubSwap - Master')
        REAL_SETTINGS.setSetting("Hub","false")
        REAL_SETTINGS.setSetting("autoFindFilmonFavourites","false")
        try:
            os.remove(icon + '.png')
        except:
            pass
        try:
            shutil.copy2(icon + 'OEM', icon + '.png')
        except:
            pass    
          
 
def CEpack():
    xbmc.log('script.pseudotv.live-service: CEpack')

    if xbmcvfs.exists(CE_LOC):
        REAL_SETTINGS.setSetting("CinemaPack","true")
        xbmc.log('script.pseudotv.live-service: CEpack - Installed')
    else:
        REAL_SETTINGS.setSetting("CinemaPack","false")
        xbmc.log('script.pseudotv.live-service: CEpack - Not Found!')
        
        
def autostart():
    xbmc.log('script.pseudotv.live-service: autostart')
    if (Msg == 'true'):
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')


CEpack()
HubSwap()

if (Enabled == 'true'):
    autostart()
 
if (ArtService_Enabled == 'true'): 
    sleep(IDLE_TIME + 900)
    ArtServiceTimer() 
    ChangeMonitor()