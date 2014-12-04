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

import os, sys, re
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *
from resources.lib.utils import *
    
PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))   
Path = (os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '720p')) #Path to Default PTVL skin, location of mod file.
fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
VWPath = (os.path.join(XBMC_SKIN_LOC, fle))
flePath = (os.path.join(Path, fle)) 
fle1 = 'dialogseekbar.xml' #xbmc skin file, needs patch
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
    xbmc.log('script.pseudotv.live-videowindow: videowindow, auto = ' + str(auto))
    REAL_SETTINGS.setSetting("videowindow","false")    
    xbmc.log('script.pseudotv.live-VideoWindow: PTVL_SKIN_SELECT_FLE = ' + PTVL_SKIN_SELECT_FLE)
    xbmc.log('script.pseudotv.live-VideoWindow: XBMC_SKIN_LOC = ' + XBMC_SKIN_LOC)
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
            Install(False)
        
    if auto == False:
        if dlg.yesno("PseudoTV Live", MSG):
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Reboot(),%d,false)" % ( 0.5, ) )
        else:
            REAL_SETTINGS.openSettings()   
            
     
def Install(exist=False):
    Error = False  
   
    #Copy VideoWindow Patch file
    if not xbmcvfs.exists(VWPath):
        try:
            xbmcvfs.copy(flePath, VWPath)
            if xbmcvfs.exists(VWPath):
                xbmc.log('script.pseudotv.live-VideoWindow: Installed')
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: Intall Failed' + str(e))
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
        xbmc.log('script.pseudotv.live-VideoWindow: script.pseudotv.live.EPG.xml Patched')

        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        
        for i in range(len(set(lineLST))):
            line = lineLST[i]
            if y in line:
                replaceAll(DSPath,y,z)
        xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar Patched')
    except Exception,e:
        xbmc.log('script.pseudotv.live-VideoWindow: Patch Failed' + str(e))
        Error = True
        pass
        
    if Error:
        MSG = "VideoWindow Patch Error!"
    else:
        if exist == True:
            MSG = "VideoWindow Patch Reapplied!"
        else:
            MSG = "VideoWindow Patched!"
        REAL_SETTINGS.setSetting("videowindow","true")
   
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )

       
def Uninstall():
    Error = False  
    try:
        xbmcvfs.delete(VWPath)
        if not xbmcvfs.exists(VWPath):
            xbmc.log('script.pseudotv.live-VideoWindow: Uninstall')
    except Exception,e:
        xbmc.log('script.pseudotv.live-VideoWindow: Uninstall Failed' + str(e))
        Error = True
        pass     

    try:
        #unpatch videowindow
        f = open(PTVL_SKIN_SELECT_FLE, "r")
        linesLST = f.readlines()    
        f.close()
        for i in range(len(set(linesLST))):
            lines = linesLST[i]
            if a in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,a,b)
            elif c in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,c,d)
        xbmc.log('script.pseudotv.live-VideoWindow: script.pseudotv.live.EPG.xml UnPatched')
                
        #unpatch seekbar
        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        for i in range(len(set(lineLST))):
            line = lineLST[i]
            if w in line:
                replaceAll(DSPath,w,v)
                
        xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar UnPatched')
    except Exception,e:
        xbmc.log('script.pseudotv.live-VideoWindow: Remove Patch Failed' + str(e))
        Error = True
        pass
    
    if Error:
        MSG = "VideoWindow Patch Error!"
    else:
        MSG = "VideoWindow Patch Removed!"
        REAL_SETTINGS.setSetting("videowindow","false")

    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
            

if sys.argv[1] == '-autopatch':
    videowindow(True)  
elif sys.argv[1] == '-videowindow':
    if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
        videowindow(False)    
    else:
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Not available while running.", 4000, THUMB) )
