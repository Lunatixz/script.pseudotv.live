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


import os, sys, re
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *
from resources.lib.FileAccess import *

xbmc.log("script.pseudotv.live-restore: Restore Setting2 Started")

settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.bak.xml'))

if REAL_SETTINGS.getSetting("ATRestore") == "true":
    if FileAccess.exists(settingsFile) and FileAccess.exists(nsettingsFile):
        try:
            xbmc.log('script.pseudotv.live-restore: Autotune, Removing Setting2...')
            os.remove(settingsFile)
            xbmc.log('script.pseudotv.live-restore: Restoring Backup Setting2...')   
            FileAccess.rename(nsettingsFile, settingsFile)  
            REAL_SETTINGS.setSetting("ATRestore","false")   
            MSG = "Backup Channels Restored"
        except Exception,e:       
            REAL_SETTINGS.setSetting("ATRestore","false")
            MSG = "Restoring Backup Channels Failed!"
            xbmc.log('script.pseudotv.live-restore: Restoring Backup Channels Failed!' + str(e))   
            pass
    else:
        MSG = "No Backup Found"
        
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
        