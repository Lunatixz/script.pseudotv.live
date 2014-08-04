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

xbmc.log("script.pseudotv.live-service: Service Started...")


def ChangeMonitor(seconds=300):
    print 'ChangeMonitor'         
    ChangeMonitorThread = threading.Timer(float(seconds), ChangeMonitor)
    ChangeMonitorThread.name = 'script.pseudotv.live-service: ChangeMonitor_Thread'
    ChangeMonitorThread.start()
    CEpack()
    HubSwap()
        
        
def ArtServiceTimer(time=1800):
    print 'ArtServiceTimer'
    Artdown = Artdownloader()
    now  = datetime.datetime.today()
    ArtService_Timer = REFRESH_INT[int(REAL_SETTINGS.getSetting('ArtService_timer_amount'))]
    
    if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true":
        ArtServiceTimerThread = threading.Timer(float(time), ArtServiceTimer)
        ArtServiceTimerThread.name = 'script.pseudotv.live-service: ArtServiceTimer_Thread'
        ArtServiceTimerThread.start()
        
        try:
            ArtService_Last = REAL_SETTINGS.getSetting('ArtService_LastRun')
            ArtService_Last = ArtService_Last.split('.')[0]
            ArtService_LastRun = datetime.datetime.strptime(ArtService_Last, '%Y-%m-%d %H:%M:%S')
            ArtService_NextRun = (ArtService_LastRun + datetime.timedelta(seconds=ArtService_Timer))
        except:
            ArtService_NextRun = now
            REAL_SETTINGS.setSetting("DynamicArt_Enabled","false")
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(ArtService_NextRun))
            pass

        if now >= ArtService_NextRun:  
            Artdown.ArtService()            
        

def ForceArtService():
    print 'ForceArtService'
    Artdown = Artdownloader() 
    Artdown.ArtService()

    
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
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    
    if REAL_SETTINGS.getSetting("notify") == "true":
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')

ChangeMonitor()

if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true": 
    ArtServiceTimerThread = threading.Timer(float(1800), ArtServiceTimer)
    ArtServiceTimerThread.name = 'script.pseudotv.live-service: ArtServiceTimer_Thread'
    ArtServiceTimerThread.start()
    
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart()