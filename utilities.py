#   Copyright (C) 2014 Kevin S. Graer
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.
        
    
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, time, fileinput, re
import urllib, urllib2

from resources.lib.Globals import *

try:
    from Donor import *
except:
    pass
    
    
def showText(heading, text):
    log("showText")
    id = 10147
    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)
    win = xbmcgui.Window(id)
    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            return
        except:
            pass
            
            
def showChangelog(addonID=None):
    log("showChangelog")
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)
        f = open(ADDON.getAddonInfo('changelog'))
        text  = f.read()
        title = "Changelog - PseudoTV Live"
        showText(title, text)
    except:
        pass


#DonorDownload
DonorURLPath = (PTVLURL + 'Donor.py')
LinkURLPath = (PTVLURL + 'links.py')
LinkPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'links.py'))
DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.pyo'))
DL_DonorPath = (os.path.join(ADDON_PATH, 'resources', 'lib', 'Donor.py'))


#String replace
def replaceAll(file,searchExp,replaceExp):
    log('replaceAll')
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

        
def DDautopatch():
    log("DDautopatch")
    REAL_SETTINGS.setSetting("AT_Donor", "false")
    REAL_SETTINGS.setSetting("COM_Donor", "false")
    REAL_SETTINGS.setSetting("TRL_Donor", "false")
    REAL_SETTINGS.setSetting("CAT_Donor", "false")

    try:
        if xbmcvfs.exists(xbmc.translatePath(DL_DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DL_DonorPath))
            log('Removed DL_DonorPath')  
            
        if xbmcvfs.exists(xbmc.translatePath(DonorPath)):
            xbmcvfs.delete(xbmc.translatePath(DonorPath))  
            log('Removed DonorPath')  
    except Exception:
        pass
        
    try:
        urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
        if xbmcvfs.exists(DL_DonorPath):
            log('DL_DonorPath Downloaded')  
            REAL_SETTINGS.setSetting("AT_Donor", "true")
            REAL_SETTINGS.setSetting("COM_Donor", "true")
            REAL_SETTINGS.setSetting("TRL_Donor", "true")
            REAL_SETTINGS.setSetting("CAT_Donor", "true")
            xbmc.executebuiltin("UpdateLocalAddons")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Donor Autoupdate Complete", 4000, THUMB) ) 
    except Exception:
        pass
    

def DonorDownloader():
    log('DonorDownloader')
    REAL_SETTINGS.setSetting("AT_Donor", "false")
    REAL_SETTINGS.setSetting("COM_Donor", "false")
    REAL_SETTINGS.setSetting("TRL_Donor", "false")
    REAL_SETTINGS.setSetting("CAT_Donor", "false")
    Install = False
    Verified = False
    InstallStatusMSG = 'Activate'  
    
    if xbmcvfs.exists(DonorPath):
        InstallStatusMSG = 'Update'
        if dlg.yesno("PseudoTV Live", str(InstallStatusMSG) + " Donor Features?"):
            try:
                xbmcvfs.delete(xbmc.translatePath(DonorPath))
                log('Removed DonorPath')  
                Install = True
            except Exception: 
                pass
    else:  
        Install = True
    
    if Install == True:
        try:                   
            urllib.urlretrieve(DonorURLPath, (xbmc.translatePath(DL_DonorPath)))
            if xbmcvfs.exists(DL_DonorPath):
                log('DL_DonorPath Downloaded')  
                REAL_SETTINGS.setSetting("AT_Donor", "true")
                REAL_SETTINGS.setSetting("COM_Donor", "true")
                REAL_SETTINGS.setSetting("TRL_Donor", "true")
                REAL_SETTINGS.setSetting("CAT_Donor", "true")
                xbmc.executebuiltin("UpdateLocalAddons")
            
                if REAL_SETTINGS.getSetting('AT_Donor') and REAL_SETTINGS.getSetting('COM_Donor') and REAL_SETTINGS.getSetting('TRL_Donor') and REAL_SETTINGS.getSetting('CAT_Donor'):
                    Verified = True

            if Verified == True:
                MSG = "Donor Features " + str(InstallStatusMSG) + "d"
            else:
                MSG = "Donor Features Not " + str(InstallStatusMSG) + "d"
                
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) ) 
            REAL_SETTINGS.openSettings()
        except Exception:
            pass
           
            
def LogoDownloader():
    log('LogoDownloader')
    LogoPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))
    
    if dlg.yesno("PseudoTV Live", "Download Color Logos or No, Download Mono Logos", ""):
        LogoDEST = LogoPath + '/PTVL_Color.zip'
        i = 0
    else:
        LogoDEST = LogoPath + '/PTVL_Mono.zip'
        i = 1

    if not DEFAULT_LOGO_LOC:
        xbmcvfs.mkdirs(DEFAULT_LOGO_LOC)
        
    try:
        xbmcvfs.delete(xbmc.translatePath(LinkPath))
        log('Removed LinkPath')  
    except Exception:
        pass
         
    try:
        urllib.urlretrieve(LinkURLPath, (xbmc.translatePath(LinkPath)))
        f = open((xbmc.translatePath(LinkPath)), "r")
        linesLST = f.readlines()
        LogoURLPath = linesLST[i] 
        download(LogoURLPath, LogoDEST)
        all(LogoDEST, LogoPath)
        REAL_SETTINGS.setSetting("ChannelLogoFolder", DEFAULT_LOGO_LOC)
        
        try:
            xbmcvfs.delete(xbmc.translatePath(LinkPath))
            log('Removed LinkPath')  
            xbmcvfs.delete(LogoDEST)
            log('Removed LogoDEST')  
        except Exception:
            pass
            
    except Exception:
        pass
       
    # Return to PTVL Settings
    REAL_SETTINGS.openSettings()
        
        
#Videowindow
PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))   
Path = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '720p')) #Path to Default PTVL skin, location of mod file.
fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
VWPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle))
flePath = xbmc.translatePath(os.path.join(Path, fle))
fle1 = 'DialogSeekBar.xml' #xbmc skin file, needs patch
DSPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle1))

#videowindow
a = '<!-- PATCH START -->'
b = '<!-- PATCH START --> <!--'
c = '<!-- PATCH END -->'
d = '--> <!-- PATCH END -->'

#seekbar
v = ' '
w = '<visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
y = '</defaultcontrol>'
z = '</defaultcontrol>\n    <visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'

def videowindow(auto):      
    log('videowindow, auto = ' + str(auto))
    REAL_SETTINGS.setSetting("videowindow_Enabled","false") 
    REAL_SETTINGS.setSetting("videowindow_"+ Skin_Select,"false")   
    log('PTVL_SKIN_SELECT_FLE = ' + PTVL_SKIN_SELECT_FLE)
    log('XBMC_SKIN_LOC = ' + XBMC_SKIN_LOC)
    MSG = "VideoWindow Patched!\nXBMC Reboot is required, Proceed?"
    
    if xbmcvfs.exists(VWPath):
        if auto == False:
            if dlg.yesno("PseudoTV Live", "VideoWindow Patch Found!\nRemove Patch?"):
                Uninstall()
                MSG = "VideoWindow Patch Removed!\nXBMC Reboot is required, Proceed?"
            else:
                Install(True)
        else:
            Install(True)
    else:
        if auto == False:
            Install()
        
    if auto == False:
        if dlg.yesno("PseudoTV Live", MSG):
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Reboot(),%d,true)" % ( 0.5, ) )
        else:
            REAL_SETTINGS.openSettings()   
            
     
def Install(exist=False):
    Error = False  
   
    #Copy VideoWindow Patch file
    if not xbmcvfs.exists(VWPath):
        try:
            xbmcvfs.copy(flePath, VWPath)
            if xbmcvfs.exists(VWPath):
                log('custom_script.pseudotv.live_9506.xml Copied')
        except Exception:
            Error = True
            pass
            
    #Patch Videowindow/Seekbar
    try:
        f = open(PTVL_SKIN_SELECT_FLE, "r")
        linesLST = f.readlines()  
        f.close()
        
        for i in range(len(set(linesLST))):
            lines = linesLST[i]
            if b in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,b,a)
            elif d in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,d,c)            
        log('script.pseudotv.live.EPG.xml Patched')

        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        
        for i in range(len(set(lineLST))):
            line = lineLST[i]
            if y in line:
                replaceAll(DSPath,y,z)
        log('dialogseekbar.xml Patched')
    except Exception:
        pass

    if Error:
        MSG = "VideoWindow Install Patch Error!"
    else:
        if exist == True:
            MSG = "VideoWindow Patch Reapplied!"
        else:
            MSG = "VideoWindow Patched!"
        REAL_SETTINGS.setSetting("videowindow_Enabled","true")
        REAL_SETTINGS.setSetting("videowindow_"+ Skin_Select,"true")
   
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )

       
def Uninstall():
    Error = False  
    
    try:
        xbmcvfs.delete(VWPath)
        if not xbmcvfs.exists(VWPath):
            log('custom_script.pseudotv.live_9506.xml Removed')
    except Exception:
        Error = True
        pass
  
    #unpatch videowindow
    try:
        f = open(PTVL_SKIN_SELECT_FLE, "r")
        linesLST = f.readlines()    
        f.close()
        for i in range(len(set(linesLST))):
            lines = linesLST[i]
            if a in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,a,b)
            elif c in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,c,d)          
        log('script.pseudotv.live.EPG.xml UnPatched')
                
        #unpatch seekbar
        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        for i in range(len(set(lineLST))):
            line = lineLST[i]
            if w in line:
                replaceAll(DSPath,w,v)
        log('dialogseekbar.xml UnPatched')
    except Exception:
        pass
  
    if Error:
        MSG = "VideoWindow Uninstall Patch Error!"
    else:
        MSG = "VideoWindow Patch Removed!"
        REAL_SETTINGS.setSetting("videowindow_Enabled","false")
        REAL_SETTINGS.setSetting("videowindow_"+ Skin_Select,"false")

    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
            

if sys.argv[1] == '-VWautopatch':
    videowindow(True)  
elif sys.argv[1] == '-videowindow':
    if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
        videowindow(False)    
    else:
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Not available while running.", 1000, THUMB) )
elif sys.argv[1] == '-DDautopatch':
    DDautopatch()   
elif sys.argv[1] == '-DonorDownloader':
    if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
        DonorDownloader()  
    else:
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Not available while running.", 1000, THUMB) )
elif sys.argv[1] == '-LogoDownloader':
    LogoDownloader()
elif sys.argv[1] == '-SimpleDownloader':
    xbmcaddon.Addon(id='script.module.simple.downloader').openSettings()
elif sys.argv[1] == '-showChangelog':
    showChangelog(ADDON_ID)
