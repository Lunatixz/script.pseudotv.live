#   Copyright (C) 2011 Lunatixz
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

import sys
import os, threading
import xbmc, xbmcgui
import xbmcaddon

from resources.lib.Globals import *
from resources.lib.ga import *

# Script constants
__scriptname__ = "PseudoTV Live"
__author__     = "Lunatixz, Originally Jason102 & Angrycamel"
__url__        = "https://github.com/Lunatixz/script.pseudotv.live"
__settings__   = xbmcaddon.Addon(id='script.pseudotv.live')
__cwd__        = __settings__.getAddonInfo('path')
__version__    = __settings__.getAddonInfo('version')
__language__   = __settings__.getLocalizedString

import resources.lib.Overlay as Overlay

try:#If found, Load PTVL Skin
    MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.live.TVOverlay.xml", __cwd__, Skin_Select)
except:#Else, Load PTV Skin
    MyOverlayWindow = Overlay.TVOverlay("script.pseudotv.TVOverlay.xml", __cwd__, Skin_Select)
    
# for curthread in threading.enumerate():
    # try:
        # log("Active Thread: " + str(curthread.name), xbmc.LOGERROR)

        # if curthread.name != "MainThread":
            # try:
                # curthread.join()
            # except:
                # pass

            # log("Joined " + curthread.name)
    # except:
        # pass
          
del MyOverlayWindow
  
xbmcgui.Window(10000).setProperty("PseudoTVRunning", "False")