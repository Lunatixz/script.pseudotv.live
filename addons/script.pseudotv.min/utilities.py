#   Copyright (C) 2015 Kevin S. Graer
#
#
# This file is part of PseudoTV Min.
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
# along with PseudoTV Min.  If not, see <http://www.gnu.org/licenses/>.
        
    
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, time, fileinput, re
import urllib, urllib2

from resources.lib.Globals import *


def showText(heading, text):
    logGlob("showText")
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
            
            
'''def showChangelog(addonID=None):
    logGlob("showChangelog")
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)
        f = open(ADDON.getAddonInfo('changelog'))
        text  = f.read()
        title = "Changelog - PseudoTV Min"
        showText(title, text)
    except:
        pass'''

def LogoDownloader():
    logGlob('LogoDownloader')
    LogoPath = xbmc.translatePath(os.path.join(SETTINGS_LOC))
    logGlob('LogoDownloader - LogoPath: '+ LogoPath)
    
    if dlg.yesno("PseudoTV Min", "Download Color Logos or No, Download Mono Logos", ""):
        LogoDEST = LogoPath + '/PTVL_Color.zip'
        i = 0
    else:
        LogoDEST = LogoPath + '/PTVL_Mono.zip'
        i = 1

    if not DEFAULT_LOGO_LOC:
        logGlob('DEFAULT_LOGO_LOC: ' + DEFAULT_LOGO_LOC)
        xbmcvfs.mkdirs(DEFAULT_LOGO_LOC)
        
    try:
        xbmcvfs.delete(xbmc.translatePath(LinkPath))
        logGlob('Removed LinkPath')  
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
            logGlob('Removed LinkPath')
            xbmcvfs.delete(LogoDEST)
            logGlob('Removed LogoDEST')
        except Exception:
            pass
            
    except Exception:
        pass
       
    # Return to PTVL Settings
    REAL_SETTINGS.openSettings()


if sys.argv[1] == '-LogoDownloader':
    LogoDownloader()
elif sys.argv[1] == '-SimpleDownloader':
    xbmcaddon.Addon(id='script.module.simple.downloader').openSettings()
'''
elif sys.argv[1] == '-showChangelog':
    showChangelog(ADDON_ID)
'''
