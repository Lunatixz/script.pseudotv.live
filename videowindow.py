#   Copyright (C) 2013 Lunatixz
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

    
import os, sys, re, fileinput
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *


def replaceAll(file,searchExp,replaceExp):
    xbmc.log('script.pseudotv.live-videowindow: replaceAll')
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
        

def videowindow():   
    xbmc.log('script.pseudotv.live-videowindow: videowindow')
    REAL_SETTINGS.setSetting("videowindow","false")
    PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))
    
    xbmc.log('script.pseudotv.live-VideoWindow: Patcher Started')
    xbmc.log('script.pseudotv.live-VideoWindow: ADDON_PATH = ' + ADDON_PATH)
    xbmc.log('script.pseudotv.live-VideoWindow: PTVL_SKIN_SELECT = ' + PTVL_SKIN_SELECT)
    xbmc.log('script.pseudotv.live-VideoWindow: PTVL_SKIN_SELECT_FLE = ' + PTVL_SKIN_SELECT_FLE)
    xbmc.log('script.pseudotv.live-VideoWindow: XBMC_SKIN_LOC = ' + XBMC_SKIN_LOC)
        
    a = '<!-- PATCH START -->'
    b = '<!-- PATCH START --> <!--'
    c = '<!-- PATCH END -->'
    d = '--> <!-- PATCH END -->'
    
    v = ' '
    w = '<visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
    y = '</defaultcontrol>'
    z = '</defaultcontrol>\n    <visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
        
    Installed = False
    Patched = False
    MSG = ''

    Path = (os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '720p')) #Path to Default PTVL skin, location of mod file.
    fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
    VWPath = (os.path.join(XBMC_SKIN_LOC, fle))
    flePath = (os.path.join(Path, fle)) 
    fle1 = 'dialogseekbar.xml' #xbmc skin file, needs patch
    DSPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle1))
    
    Error = False
    Uninstall = False
    UnPatch = False
    Patch = False
    Install = False
    
    # Delete Old VideoWindow Patch
    if xbmcvfs.exists(VWPath):
        if dlg.yesno("PseudoTV Live", "VideoWindow Patch Found!\nRemove Patch?"):
            try:
                xbmcvfs.delete(VWPath)
                Uninstall = True
                xbmc.log('script.pseudotv.live-VideoWindow: Uninstall')
            except Exception,e:
                xbmc.log('script.pseudotv.live-VideoWindow: Delete Patch Failed' + str(e))
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
                        
                #unpatch seek
                f = open(DSPath, "r")
                lineLST = f.readlines()            
                f.close()
                for i in range(len(set(lineLST))):
                    line = lineLST[i]
                    if w in line:
                        replaceAll(DSPath,w,v)
                        
                UnPatch = True
                xbmc.log('script.pseudotv.live-VideoWindow: UnPatch')
            except Exception,e:
                xbmc.log('script.pseudotv.live-VideoWindow: Remove Patch Failed' + str(e))
                Error = True
                pass
        else:
            if dlg.yesno("PseudoTV Live", "VideoWindow Patch Found!\n Reapply Patch?"):
                Patch = True
            else:
                MSG = "VideoWindow Unchanged"
    else:
        Install = True
      
      
    # Copy VideoWindow Patch  
    if Install:
        try:
            xbmcvfs.copy(flePath, VWPath)
            if xbmcvfs.exists(VWPath):
                Installed = True
                Patch = True
                xbmc.log('script.pseudotv.live-VideoWindow: Installed')
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: Intall Failed' + str(e))
            Error = True
            pass
        
    if Patch:
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
            
            try:
                f = open(DSPath, "r")
                lineLST = f.readlines()            
                f.close()
                
                for i in range(len(set(lineLST))):
                    line = lineLST[i]
                    if y in line:
                        replaceAll(DSPath,y,z)
                        xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar Patched')
            except:
                pass
            
            
            Patched = True
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: script.pseudotv.live.EPG.xml Patch Failed' + str(e))
            Error = True
            pass

    if (Installed and Patched) or Patched:
        MSG = "VideoWindow Patched!"
        REAL_SETTINGS.setSetting("videowindow","true")
        xbmc.executebuiltin("ReloadSkin()")
    
    if Uninstall or UnPatch:
        MSG = "VideoWindow Patch Removed!"
        REAL_SETTINGS.setSetting("videowindow","false")
        xbmc.executebuiltin("ReloadSkin()")
    
    if Error:
        MSG = "VideoWindow Patch Error!"
        
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
    REAL_SETTINGS.openSettings()
    
    
def autopatch():
    xbmc.log('script.pseudotv.live-videowindow: autopatch')
    REAL_SETTINGS.setSetting("videowindow","false")
    PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))

    a = '<!-- PATCH START -->'
    b = '<!-- PATCH START --> <!--'
    c = '<!-- PATCH END -->'
    d = '--> <!-- PATCH END -->'
    
    v = ' '
    w = '    <visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
    y = '</defaultcontrol>'
    z = '</defaultcontrol>\n    <visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
        
    MSG = ''
    fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
    VWPath = (os.path.join(XBMC_SKIN_LOC, fle))
    flePath = (os.path.join(Path, fle)) 
    
    fle1 = 'dialogseekbar.xml' #xbmc skin file, needs patch
    DSPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle1))
    
    if xbmcvfs.exists(VWPath):
        try:
            #videowindow
            f = open(PTVL_SKIN_SELECT_FLE, "r")
            linesLST = f.readlines()            
            f.close()
            
            for i in range(len(set(linesLST))):
                lines = linesLST[i]
                if b in lines:
                    replaceAll(PTVL_SKIN_SELECT_FLE,b,a)
                elif d in lines:
                    replaceAll(PTVL_SKIN_SELECT_FLE,d,c)            
            xbmc.log('script.pseudotv.live-VideoWindow: autopatch script.pseudotv.live.EPG.xml Patched')
            MSG = "VideoWindow Patched"

            #seek
            f = open(DSPath, "r")
            lineLST = f.readlines()            
            f.close()
            
            for i in range(len(set(lineLST))):
                line = lineLST[i]
                
                if y in line:
                    replaceAll(DSPath,y,z)
                    xbmc.log('script.pseudotv.live-VideoWindow: DialogSeekBar Patched')

            REAL_SETTINGS.setSetting("videowindow","true")
        except Exception,e:
            xbmc.log('script.pseudotv.live-VideoWindow: autopatch script.pseudotv.live.EPG.xml Patch Failed' + str(e))
            MSG = "VideoWindow Patch Error!"
            pass
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 4000, THUMB) )

    else:
        xbmc.log('script.pseudotv.live-videowindow: autopatch fle not found')
            

if sys.argv[1] == '-autopatch':
    autopatch()
elif sys.argv[1] == '-videowindow':
    videowindow()