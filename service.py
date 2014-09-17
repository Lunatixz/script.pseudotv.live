import os, shutil, datetime, random#, threading
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

def ArtServiceTimer(time=1800): #only needed when settop box enabled
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

    
def HubSwap(): # Swap Org/Hub versions if 'Hub Installer' found.
    xbmc.log('script.pseudotv.live-service: HubSwap')
    
    try:#unknown amazon firetv error encountered here, requires investigation
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
            try:
                os.remove(icon + '.png')
            except:
                pass
            try:
                shutil.copy2(icon + 'OEM', icon + '.png')
            except:
                pass    
    except:
        REAL_SETTINGS.setSetting("Hub","false")
        pass
          
          
def donorCHK():
    xbmc.log('script.pseudotv.live-service: donorCHK')
    
    DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
    DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))
    
    if FileAccess.exists(DonorPath):
        REAL_SETTINGS.setSetting("AT_Donor", "true")
        REAL_SETTINGS.setSetting("COM_Donor", "true")
        REAL_SETTINGS.setSetting("TRL_Donor", "true")
        REAL_SETTINGS.setSetting("CAT_Donor", "true")
    elif FileAccess.exists(DL_DonorPath):  
        REAL_SETTINGS.setSetting("AT_Donor", "true")
        REAL_SETTINGS.setSetting("COM_Donor", "true")
        REAL_SETTINGS.setSetting("TRL_Donor", "true")
        REAL_SETTINGS.setSetting("CAT_Donor", "true")
    else:
        REAL_SETTINGS.setSetting("AT_Donor", "false")
        REAL_SETTINGS.setSetting("COM_Donor", "false")
        REAL_SETTINGS.setSetting("TRL_Donor", "false")
        REAL_SETTINGS.setSetting("CAT_Donor", "false")
    

def autostart():
    xbmc.log('script.pseudotv.live-service: autostart')
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    
    if REAL_SETTINGS.getSetting("notify") == "true":
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')

HubSwap()
donorCHK()

# if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true": 
    # ArtServiceTimerThread = threading.Timer(float(1800), ArtServiceTimer)
    # ArtServiceTimerThread.name = 'script.pseudotv.live-service: ArtServiceTimer_Thread'
    # ArtServiceTimerThread.start()
    
if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart()