#   Copyright (C) 2015 Jason Anderson, Kevin S. Graer
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
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import sys, re, os
import time, traceback
import Globals

from FileAccess import FileAccess

class Settings:
    def __init__(self):
        self.logfile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
        self.repairfile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.repair.xml'))
        self.currentSettings = []
        self.alwaysWrite = 1


    def loadSettings(self):
        self.log("Loading settings from " + self.logfile);
        del self.currentSettings[:]
        try:
            if FileAccess.exists(self.logfile):
                try:
                    fle = FileAccess.open(self.logfile, "r")
                    curset = fle.readlines()
                    fle.close()
                except Exception,e:
                    self.log("Exception when reading settings: ")
                    self.log(traceback.format_exc(), xbmc.LOGERROR)

                for line in curset:
                    name = re.search('setting id="(.*?)"', line)

                    if name:
                        val = re.search(' value="(.*?)"', line)

                        if val:
                            self.currentSettings.append([name.group(1), val.group(1)])
        except Exception,e:
            print str(e)
            return
            
            
    def disableWriteOnSave(self):
        self.alwaysWrite = 0


    def log(self, msg, level = xbmc.LOGDEBUG):
        Globals.log('Settings: ' + msg, level)


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
        
        
    def writeSettingsNew(self, updateDialog):
        self.log("writeSettingsNew")
        updateDialog.update(90, "Repairing Channel Configurations", "Saving Changes")
        if FileAccess.exists(self.repairfile):
            xbmcvfs.delete(self.repairfile)
            
        try:
            fle = FileAccess.open(self.repairfile, "w")
        except Exception,e:
            self.log("Unable to open the file for writing")
            return

        flewrite = Globals.uni("<settings>\n")

        for i in range(len(self.amendedSettings)):
            updateDialog.update(int(i * .07) + 1, "Repairing Channel Configurations", "Saving Channel " + str(i+1))
            try:
                flewrite += Globals.uni('    <setting id="') + Globals.uni(self.amendedSettings[i][0]) + Globals.uni('" value="') + Globals.uni(self.amendedSettings[i][1]) + Globals.uni('" />\n')
            except:
                pass
        flewrite += Globals.uni('</settings>\n')
        fle.write(flewrite)
        fle.close()
        
        if FileAccess.exists(self.repairfile):
            xbmcvfs.delete(self.logfile)
            xbmcvfs.rename(self.repairfile, self.logfile)
        

    def repairSettings(self):
        self.log("repairSettings")
        xbmcgui.Dialog().ok("PseudoTV Live", "[COLOR=red]Warning!![/COLOR] The repair process can, but rarely; damages your channel configurations.", "Its recommended you backup before continuing.")
        
        if xbmcgui.Dialog().yesno("PseudoTV Live", "Repair Channel Configurations?"):
            self.loadSettings()
            self.amendedSettings = []
            
            updateDialog = xbmcgui.DialogProgress()
            updateDialog.create("PseudoTV Live", "Repairing Channel Configurations")
            MSG = "Channel Repair Failed!"

            for i in range(999):
                updateDialog.update(int(i * .07) + 1, "Repairing Channel Configurations", "Scanning Channel " + str(i+1))
                for n in range(len(self.currentSettings)):
                    if (self.currentSettings[n][0]).startswith('Channel_'+ str(i+1) + '_'):
                        updateDialog.update(int(i * .07) + 1, "Repairing Channel Configurations", "Repairing Channel " + str(i+1))
                        self.amendedSettings.append(self.currentSettings[n])
    
            self.writeSettingsNew(updateDialog)
            MSG = "Channel Configurations Repaired"
            updateDialog.close()
            xbmcgui.Dialog().ok("PseudoTV Live", "Repairing Channel Configurations Complete", "")
        
        # Return to PTVL Settings
        Globals.REAL_SETTINGS.openSettings()