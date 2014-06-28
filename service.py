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

    
timer_amounts = {}
timer_amounts['0'] = 0            
timer_amounts['1'] = 5           
timer_amounts['2'] = 10            
timer_amounts['3'] = 15
timer_amounts['4'] = 20

PseudoTVRunning = False
ArtService_Running = False
Restart = REAL_SETTINGS.getSetting('Auto_Restart')
Enabled = REAL_SETTINGS.getSetting('Auto_Start')
Msg = REAL_SETTINGS.getSetting('notify')
IDLE_TIME = int(timer_amounts[REAL_SETTINGS.getSetting('timer_amount')])
ArtService_Enabled = REAL_SETTINGS.getSetting('ArtService_Enabled') 
ArtService_Msg = REAL_SETTINGS.getSetting('ArtService_notify')
ArtService_Timer = REFRESH_INT[int(REAL_SETTINGS.getSetting('ArtService_timer_amount'))]  
ArtService_Background = REAL_SETTINGS.getSetting('ArtService_Background') 
xbmc.log("script.pseudotv.live-service: Service Started...")

    
if xbmcgui.Window(10000).getProperty("PseudoTVRunning") == "True":
    if not ArtService_Background:
        PseudoTVRunning = True

        
def MonitorChange():
    print 'MonitorChange'
    MonitorChange_Thread = threading.Timer(5.0, MonitorChange)
    MonitorChange_Thread.name = "script.pseudotv.live-service: MonitorChange"
    MonitorChange_Thread.start()
    
    #Skin Change
    PseudoTVSkin_Num = int(REAL_SETTINGS.getSetting('SkinSelector'))
    try:
        PseudoTVSkin_LastNum = int(REAL_SETTINGS.getSetting('PseudoTVSkin_LastNum'))
         
        if PseudoTVSkin_Num != PseudoTVSkin_LastNum: # Force Art service after skin change.
            REAL_SETTINGS.setSetting("ArtService_LastRun",'')#clear Artservice Lastrun
            REAL_SETTINGS.setSetting("PseudoTVSkin_LastNum",str(PseudoTVSkin_Num))
            #Run artservice, if not running.
            if not ArtService_Running:
                ArtService()
        #Disable art service for non compatible skins
        if PseudoTVSkin_Num == 0:
            ArtService_Enabled = False
    except:
        pass
         
        
def uniq(lst):
    print 'uniq'
    last = object()
    for item in lst:
        if item == last:
            continue
        yield item
        last = item

        
def sort_and_deduplicate(l):
    print 'sort_and_deduplicate'
    return list(uniq(sorted(l, reverse=True)))

    
def PreArtService():
    print 'PreArtService'
    ADDON_SETTINGS.loadSettings()
    exclude = ['#EXTM3U', '#EXTINF']
    lineLST = []
    newLST = []
    ArtLST = []
    chtype = ''
    
    for i in range(999):
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
        except Exception,e:
            pass
            
        if chtype:
            try:
                fle = xbmc.translatePath(os.path.join(LOCK_LOC, ("channel_" + str(i + 1) + '.m3u')))
                
                if FileAccess.exists(fle):
                    f = FileAccess.open(fle, 'r')
                    lineLST = f.readlines()
                    for n in range(len(lineLST)):
                        line = lineLST[n]
                        
                        try:
                            TV_liveid = (line.split('//tvshow')[1])
                            TV_liveid =  'tvshow' + TV_liveid
                            type = TV_liveid.split('|')[0]
                            id = TV_liveid.split('|')[1]
                        except:
                            pass
                            
                        try:
                            MO_liveid = line.split('//movie')[1]
                            MO_liveid = 'movie' + MO_liveid
                            type = MO_liveid.split('|')[0]
                            id = MO_liveid.split('|')[1]
                        except:
                            pass

                        if line[0:7] not in exclude:
                            mpath = os.path.split(line)[0]  
                            newLST = [type, chtype, id, mpath]
                            ArtLST.append(newLST)
            except:
                pass
                    
    ArtLST = sort_and_deduplicate(ArtLST)
    random.shuffle(ArtLST)
    print 'PreArtService - Total Count - ' + str(len(ArtLST))
    return ArtLST

  
def ArtService():
    print 'ArtService'
    sleep(IDLE_TIME + 240)   
    
    start = datetime.datetime.today()  
    # threading.Timer((float(ArtService_Timer)), ArtService()).start()
    
    ArtService_Thread = threading.Timer((float(ArtService_Timer)), ArtService)
    ArtService_Thread.name = "ArtService_Thread"
    ArtService_Thread.start()
    
    type1EXT = ''
    type2EXT = ''
    ArtService_NextRun = start
    Artdown = Artdownloader()
    
    type1EXT = REAL_SETTINGS.getSetting('type1EXT')
    type2EXT = REAL_SETTINGS.getSetting('type2EXT')
    
    if not type1EXT:
        type1EXT = 'landscape.jpg'
        
    if not type2EXT:
        type2EXT = 'logo.png'
         
    ArtService_LastRun = REAL_SETTINGS.getSetting('ArtService_LastRun')
    
    if ArtService_LastRun:
        ArtService_LastRun = ArtService_LastRun.split('.')[0]
        ArtService_LastRun = datetime.datetime.strptime(ArtService_LastRun, '%Y-%m-%d %H:%M:%S')
        ArtService_NextRun = (ArtService_LastRun + datetime.timedelta(seconds=ArtService_Timer)) #reset time after forcechannel reset. todo
        print 'ArtService_LastRun', str(ArtService_LastRun)
    print 'ArtService_NextRun', str(ArtService_NextRun)
    
    if start >= ArtService_NextRun:
    
        if not PseudoTVRunning:
        
            ArtService_Running = True
            if (ArtService_Msg == 'true'):
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Spooling Started", 2000, THUMB) )
            
            ArtLst = PreArtService()
            # Clear Artwork Cache Folders
            if REAL_SETTINGS.getSetting("ClearLiveArt") == "true":
                artwork.delete("%")
                artwork1.delete("%")
                artwork2.delete("%")
                artwork3.delete("%")
                artwork4.delete("%")
                artwork5.delete("%")
                artwork6.delete("%")
                
                if (ArtService_Msg == 'true'):
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Cache Cleared", 2000, THUMB) )
                
                REAL_SETTINGS.setSetting('ClearLiveArt', "false")
                xbmc.log('script.pseudotv.live-service: ArtCache Purged!')
                sleep(5)
     
            for i in range(len(ArtLst)):
                setImage1 = ''
                setImage2 = ''
                lineLST = ArtLst[i]
                type = lineLST[0]
                chtype = lineLST[1]
                id = lineLST[2]
                mpath = lineLST[3]
                
                setImage1 = Artdown.FindArtwork(type, chtype, id, mpath, type1EXT)
                setImage2 = Artdown.FindArtwork(type, chtype, id, mpath, type2EXT)
                
            stop = datetime.datetime.today()
            finished = stop - start
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(start))
            MSSG = ("Artwork Spooling Finished in %d seconds" %finished.seconds)
            print str(MSSG)
            ArtService_Running = False
            if (ArtService_Msg == 'true'):
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 2000, THUMB) )

                
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

    
MonitorChange()
HubSwap()
CEpack()

if (Enabled == 'true'):
    autostart()

if (ArtService_Enabled == 'true'):
    ArtService()
 
try:
    if sys.argv[1] == '-Auto_Restart':
        xbmc.log('script.pseudotv.live-service: Auto_RESTART')
        sleep(2)
        xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
except:
    pass
    
    
class UpdateMonitor(xbmc.Monitor):
    update_settings = None
    after_scan = None
    screensaver_running = False
    
    def __init__(self,*args,**kwargs):
        xbmc.Monitor.__init__(self)
        self.update_settings = kwargs['update_settings']
        self.after_scan = kwargs['after_scan']

    def onSettingsChanged(self):
        xbmc.sleep(1000) #slight delay for notifications
        print 'onSettingsChanged'
        self.update_settings()

    def onDatabaseUpdated(self,database):
        self.after_scan(database)