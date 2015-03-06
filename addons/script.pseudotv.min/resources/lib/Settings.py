#   Copyright (C) 2015 Jason Anderson, Kevin S. Graer
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
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcaddon
import sys, re, os
import time, traceback
import Globals

from FileAccess import FileAccess
#from Globals import logGlob

class Settings:
    def __init__(self):
        self.logfile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
        self.currentSettings = []
        self.alwaysWrite = 1


    def loadSettings(self):
        self.log("Loading settings from " + self.logfile);
        del self.currentSettings[:]

        if FileAccess.exists(self.logfile):
            try:
                fle = FileAccess.open(self.logfile, "r")
                curset = fle.readlines()
                fle.close()
            except Exception,e:
                self.logError("Exception when reading settings: ")
                self.logError(traceback.format_exc())

            for line in curset:
                name = re.search('setting id="(.*?)"', line)

                if name:
                    val = re.search(' value="(.*?)"', line)

                    if val:
                        self.currentSettings.append([name.group(1), val.group(1)])


    def disableWriteOnSave(self):
        self.alwaysWrite = 0


    def log(self, msg, level = xbmc.LOGNOTICE):
        Globals.logGlob('Settings: ' + msg, level)
    
    def logDebug(self, msg):
        Globals.logGlob('Settings: ' + msg)
    
    def logError(self, msg):
        Globals.logGlob('Settings: ' + msg, xbmc.LOGERROR)


    def getSetting(self, name, force = False):
        if force:
            self.loadSettings()

        result = self.getSettingNew(name)

        if result is None:
            return self.realGetSetting(name)

        return result


    def getSettingNew(self, name):
        for i in range(len(self.currentSettings)):
            if self.currentSettings[i][0] == name:
                return self.currentSettings[i][1]

        return None


    def realGetSetting(self, name):
        try:
            val = Globals.REAL_SETTINGS.getSetting(name)
            return val
        except Exception,e:
            return ''


    def setSetting(self, name, value):
        found = False

        for i in range(len(self.currentSettings)):
            if self.currentSettings[i][0] == name:
                self.currentSettings[i][1] = value
                found = True
                break

        if found == False:
            self.currentSettings.append([name, value])

        if self.alwaysWrite == 1:
            self.writeSettings()


    def writeSettings(self):
        try:
            fle = FileAccess.open(self.logfile, "w")
        except Exception,e:
            self.log("Unable to open the file for writing")
            return

        flewrite = Globals.uni("<settings>\n")

        for i in range(len(self.currentSettings)):
            try:
                flewrite += Globals.uni('    <setting id="') + Globals.uni(self.currentSettings[i][0]) + Globals.uni('" value="') + Globals.uni(self.currentSettings[i][1]) + Globals.uni('" />\n')
            except:
                pass
        flewrite += Globals.uni('</settings>\n')
        fle.write(flewrite)
        fle.close()
