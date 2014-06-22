import os, shutil
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from time import sleep
from resources.lib.Globals import *

try:
    from Donor import *
    DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
    DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))
    if xbmcvfs.exists(DL_DonorPath):
        if xbmcvfs.exists(DonorPath):
            try:
                os.remove(xbmc.translatePath(DL_DonorPath))
            except:
                pass             
except Exception,e:         
    pass  
    
timer_amounts = {}
timer_amounts['0'] = 0            
timer_amounts['1'] = 5           
timer_amounts['2'] = 10            
timer_amounts['3'] = 15
timer_amounts['4'] = 20

IDLE_TIME = int(timer_amounts[REAL_SETTINGS.getSetting('timer_amount')])
Enabled = REAL_SETTINGS.getSetting('Auto_Start')
Restart = REAL_SETTINGS.getSetting('Auto_Restart')
Msg = REAL_SETTINGS.getSetting('notify')
 
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
        
    
def Notify():
    xbmc.log('script.pseudotv.live-service: Notify')
    if (Msg == 'true'):
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("AutoStart PseudoTV Live","Service Starting...", 4000, THUMB) )
        xbmc.log("script.pseudotv.live-service: Notifications Enabled...")
    else:
        xbmc.log("script.pseudotv.live-service: Notifications Disabled...")

        
def autostart():
    xbmc.log('script.pseudotv.live-service: autostart')
    Notify()
    sleep(IDLE_TIME)
    xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
    xbmc.log("script.pseudotv.live-service: Service Started...")


if (Enabled == 'true'):
    autostart()

HubSwap() 
CEpack()

try:  
    if sys.argv[1] == '-Auto_Restart':
        xbmc.log('script.pseudotv.live-service: Auto_RESTART')
        sleep(2)
        xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/default.py' + '")')
except:
    pass