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
    import storageserverdummy as StorageServer
    
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

def ServiceTimer():
    print 'ServiceTimer'
    REAL_SETTINGS.setSetting("ArtService_Startup","false")
    REAL_SETTINGS.setSetting("ArtService_Running","false")
    REAL_SETTINGS.setSetting('SyncXMLTV_Startup', "false")
    REAL_SETTINGS.setSetting('SyncXMLTV_Running', "false")
    
    # while not xbmc.abortRequested:

            # if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true" and REAL_SETTINGS.getSetting("SyncXMLTV_Startup") == "true":
                # SyncXMLTV()
                
            # if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true" and REAL_SETTINGS.getSetting("ArtService_Startup") == "true":
                # ArtService_Timer = REFRESH_INT[int(REAL_SETTINGS.getSetting('ArtService_timer_amount'))]
                # Update = True
                # now  = datetime.datetime.today()
                
                # try:
                    # ArtService_LastRun = REAL_SETTINGS.getSetting('ArtService_NextRun')
                    # ArtService_LastRun = ArtService_LastRun.split('.')[0]
                    # ArtService_LastRun = datetime.datetime.strptime(ArtService_LastRun, '%Y-%m-%d %H:%M:%S')
                # except:
                    # ArtService_LastRun = now
                    # pass

                # if now >= ArtService_LastRun: 
                    # if REAL_SETTINGS.getSetting('Enabled_RunOnPlayback') == 'false':
                        # if xbmc.Player().isPlaying():
                            # Update = False 

                    # if Update == True:
                        # ArtService_NextRun = (ArtService_LastRun + datetime.timedelta(seconds=ArtService_Timer))
                        # REAL_SETTINGS.setSetting("ArtService_NextRun",str(ArtService_NextRun))
                        # Artdown.ArtService()
                        
            # xbmc.sleep(4000)            
        

def ForceArtService():
    print 'ForceArtService'
    Artdown = Artdownloader() 
    Artdown.ArtService()

    
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
    
    if xbmcvfs.exists(DonorPath):
        REAL_SETTINGS.setSetting("AT_Donor", "true")
        REAL_SETTINGS.setSetting("COM_Donor", "true")
        REAL_SETTINGS.setSetting("TRL_Donor", "true")
        REAL_SETTINGS.setSetting("CAT_Donor", "true")
    elif xbmcvfs.exists(DL_DonorPath):  
        REAL_SETTINGS.setSetting("AT_Donor", "true")
        REAL_SETTINGS.setSetting("COM_Donor", "true")
        REAL_SETTINGS.setSetting("TRL_Donor", "true")
        REAL_SETTINGS.setSetting("CAT_Donor", "true")
    else:
        REAL_SETTINGS.setSetting("AT_Donor", "false")
        REAL_SETTINGS.setSetting("COM_Donor", "false")
        REAL_SETTINGS.setSetting("TRL_Donor", "false")
        REAL_SETTINGS.setSetting("CAT_Donor", "false")
        REAL_SETTINGS.setSetting("autoFindCommunity_Source", "0")
    
    
def SyncXMLTV():
    print 'SyncXMLTV'
    USxmltv = False
    SSxmltv = False
    FTVxmltv = False
    
    if REAL_SETTINGS.getSetting("SyncXMLTV_Running") == "false":
        REAL_SETTINGS.setSetting('SyncXMLTV_Running', "true")
            
        if not xbmcvfs.exists(XMLTV_CACHE_LOC):
            xbmcvfs.mkdirs(XMLTV_CACHE_LOC)
            
        USxmltv = chanlist.SyncUSTVnow()
        SSxmltv = chanlist.SyncSSTV()
        FTVxmltv = chanlist.SyncFTV()
        REAL_SETTINGS.setSetting('SyncXMLTV_Running', "false")
        
        if USxmltv or SSxmltv or FTVxmltv:
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","XMLTV Update Complete", 1000, THUMB) )
    
    
def autostart():
    xbmc.log('script.pseudotv.live-service: autostart')   
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
    
    IDLE_TIME = AUTOSTART_TIMER[int(REAL_SETTINGS.getSetting('timer_amount'))] 
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
    
    
HubSwap()
donorCHK()
ServiceTimer()

if REAL_SETTINGS.getSetting("Auto_Start") == "true": 
    autostart()
    