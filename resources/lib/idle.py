#Standard modules
import os
import sys
#Third-party modules
import xbmcaddon
#Project modules
from Globals import *

###Path handling
rootDir = ADDON_PATH
if rootDir[-1] == ';':rootDir = rootDir[0:-1]
resDir = os.path.join(rootDir, 'resources')
libDir = os.path.join(resDir, 'lib')
skinsDir = os.path.join(resDir, 'skins')

sys.path.append (libDir)

import idle_gui
ui = idle_gui.GUI("idle.xml" , ADDON_PATH, "Default")
ui.doModal()
    