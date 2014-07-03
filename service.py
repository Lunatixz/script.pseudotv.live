import os, shutil, datetime, random, threading
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from time import sleep
from resources.lib.Globals import *
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
        now = datetime.datetime.today()
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
    ADDON = os.path.split(ADDON_PATH)[1]
    icon = ADDON_PATH + '/icon'
    if ADDON == 'script.pseudotv.live-Hub-Edition':
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

    
if sys.argv[0] == '-AutoRestart':
    xbmc.log('script.pseudotv.live-service: Auto_RESTART')
    sleep(2)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
else:
    CEpack()
    HubSwap()

    if (Enabled == 'true'):
        autostart()
     
    if (ArtService_Enabled == 'true'): 
        sleep(IDLE_TIME + 900)
        ArtServiceTimer() 
        ChangeMonitor()