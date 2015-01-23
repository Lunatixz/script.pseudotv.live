#   Copyright (C) 2015 Kevin S. Graer
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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random

from xml.dom.minidom import parse, parseString
from resources.lib.utils import *
from resources.lib.Globals import *
from resources.lib.ChannelList import ChannelList
from resources.lib.AdvancedConfig import AdvancedConfig
from resources.lib.FileAccess import FileAccess
from resources.lib.Migrate import Migrate

NUMBER_CHANNEL_TYPES = 17

class ConfigWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.log("__init__")
        if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
            self.madeChanges = 0
            self.showingList = True
            self.channel = 0
            self.channel_type = 9999
            self.setting1 = ''
            self.setting2 = ''
            self.setting3 = ''
            self.setting4 = ''
            self.savedRules = False
            self.DirName = ''
            self.PluginSourcePathDir = ''
            
            if CHANNEL_SHARING:
                realloc = REAL_SETTINGS.getSetting('SettingsFolder')
                FileAccess.copy(realloc + '/settings2.xml', SETTINGS_LOC + '/settings2.xml')

            ADDON_SETTINGS.loadSettings()
            ADDON_SETTINGS.disableWriteOnSave()
            self.doModal()
            self.log("__init__ return")
        else:
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Not available while running.", 4000, THUMB) )


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelConfig: ' + msg, level)


    def onInit(self):
        self.log("onInit")
        REAL_SETTINGS.setSetting('Autotune', "false")
        REAL_SETTINGS.setSetting('Warning1', "false") 
        
        for i in range(NUMBER_CHANNEL_TYPES):
            try:
                self.getControl(120 + i).setVisible(False)
            except:
                pass

        migratemaster = Migrate()
        migratemaster.migrate()
        self.prepareConfig()
        self.myRules = AdvancedConfig("script.pseudotv.live.AdvancedConfig.xml", ADDON_PATH, "Default")
        self.log("onInit return")


    def onFocus(self, controlId):
        pass


    def onAction(self, act):
        action = act.getId()

        if action in ACTION_PREVIOUS_MENU:
            if self.showingList == False:
                self.cancelChan()
                self.hideChanDetails()
            else:
                if self.madeChanges == 1:
                    dlg = xbmcgui.Dialog()

                    if dlg.yesno("Save", "Do you want to save all changes?"):
                        ADDON_SETTINGS.writeSettings()
            
                        if CHANNEL_SHARING:
                            realloc = REAL_SETTINGS.getSetting('SettingsFolder')
                            FileAccess.copy(SETTINGS_LOC + '/settings2.xml', realloc + '/settings2.xml')

                self.close()
        elif act.getButtonCode() == 61575:      # Delete button
            curchan = self.listcontrol.getSelectedPosition() + 1

            if( (self.showingList == True) and (ADDON_SETTINGS.getSetting("Channel_" + str(curchan) + "_type") != "9999") ):
                dlg = xbmcgui.Dialog()

                if dlg.yesno("Save", "Are you sure you want to clear this channel?"):
                    ADDON_SETTINGS.setSetting("Channel_" + str(curchan) + "_type", "9999")
                    self.updateListing(curchan)
                    self.madeChanges = 1


    def saveSettings(self):
        self.log("saveSettings channel " + str(self.channel))
        chantype = 9999
        chan = str(self.channel)
        set1 = ''
        set2 = ''
        set3 = ''
        set4 = ''
        channame = ''

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + chan + "_type"))
        except:
            self.log("Unable to get channel type")

        setting1 = "Channel_" + chan + "_1"
        setting2 = "Channel_" + chan + "_2"
        setting3 = "Channel_" + chan + "_3"
        setting4 = "Channel_" + chan + "_4"
        channame = ADDON_SETTINGS.getSetting("Channel_" + chan + "_rule_1_opt_1")

        if chantype == 0:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(330).getLabel2())
        elif chantype == 1:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(142).getLabel())
        elif chantype == 2:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(152).getLabel())
        elif chantype == 3:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(162).getLabel())
        elif chantype == 4:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(172).getLabel())
        elif chantype == 5:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(182).getLabel())
        elif chantype == 6:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(192).getLabel())
            
            if self.getControl(194).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_ORDERAIRDATE))
            else:
                ADDON_SETTINGS.setSetting(setting2, "0")
                
        elif chantype == 7:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(200).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(203).getLabel())
        elif chantype == 8: #LiveTV
            ADDON_SETTINGS.setSetting(setting1, self.getControl(210).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(211).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(212).getLabel())
            ADDON_SETTINGS.setSetting(channame, self.getControl(213).getLabel())
        elif chantype == 9: #InternetTV
            ADDON_SETTINGS.setSetting(setting1, self.getControl(220).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(221).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(222).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(223).getLabel())
        elif chantype == 10: #Youtube
            ADDON_SETTINGS.setSetting(setting1, self.getControl(231).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(230).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(232).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(233).getLabel())
        elif chantype == 11: #RSS
            ADDON_SETTINGS.setSetting(setting1, self.getControl(240).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(242).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(243).getLabel())
        elif chantype == 12: #Music
            ADDON_SETTINGS.setSetting(setting1, self.getControl(250).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(251).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(252).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(253).getLabel())
        elif chantype == 13: #Music Videos
            ADDON_SETTINGS.setSetting(setting1, self.getControl(260).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(261).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(262).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(263).getLabel())
        elif chantype == 14: #Exclusive
            ADDON_SETTINGS.setSetting(setting1, self.getControl(270).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(271).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(272).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(273).getLabel())
        elif chantype == 15: #Plugin
            ADDON_SETTINGS.setSetting(setting1, self.getControl(282).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(283).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(284).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(287).getLabel())
        elif chantype == 16: #UPNP
            ADDON_SETTINGS.setSetting(setting1, self.getControl(290).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(291).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(292).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(293).getLabel())
        elif chantype == 9999:
            ADDON_SETTINGS.setSetting(setting1, '')
            ADDON_SETTINGS.setSetting(setting2, '')
            ADDON_SETTINGS.setSetting(setting3, '')
            ADDON_SETTINGS.setSetting(setting4, '')

        if self.savedRules:
            self.saveRules(self.channel)

        # Check to see if the user changed anything
        set1 = ''
        set2 = ''
        set3 = ''
        set4 = ''

        try:
            set1 = ADDON_SETTINGS.getSetting(setting1)
            set2 = ADDON_SETTINGS.getSetting(setting2)
            set3 = ADDON_SETTINGS.getSetting(setting3)
            set4 = ADDON_SETTINGS.getSetting(setting4)
        except:
            pass

        if chantype != self.channel_type or set1 != self.setting1 or set2 != self.setting2 or self.savedRules:
            self.madeChanges = 1
            ADDON_SETTINGS.setSetting('Channel_' + chan + '_changed', 'True')

        self.log("saveSettings return")


    def cancelChan(self):
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_type", str(self.channel_type))
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_1", self.setting1)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_2", self.setting2)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_3", self.setting3)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_4", self.setting4)


    def hideChanDetails(self):
        self.getControl(106).setVisible(False)

        for i in range(NUMBER_CHANNEL_TYPES):
            try:
                self.getControl(120 + i).setVisible(False)
            except:
                pass

        self.setFocusId(102)
        self.getControl(105).setVisible(True)
        self.showingList = True
        self.updateListing(self.channel)
        self.listcontrol.selectItem(self.channel - 1)


    def onClick(self, controlId):
        self.log("onClick " + str(controlId))
        chnlst = ChannelList()  
        dlg = xbmcgui.Dialog()
        
        if controlId == 102:        # Channel list entry selected
            self.getControl(105).setVisible(False)
            self.getControl(106).setVisible(True)
            self.channel = self.listcontrol.getSelectedPosition() + 1
            self.changeChanType(self.channel, 0)
            self.setFocusId(110)
            self.showingList = False
            self.savedRules = False
        elif controlId == 110:      # Change channel type left
            self.changeChanType(self.channel, -1)
        elif controlId == 111:      # Change channel type right
            self.changeChanType(self.channel, 1)
        elif controlId == 112:      # Ok button
            self.saveSettings()
            self.hideChanDetails()
        elif controlId == 113:      # Cancel button
            self.cancelChan()
            self.hideChanDetails()
        elif controlId == 114:      # Rules button
            self.myRules.ruleList = self.ruleList
            self.myRules.doModal()

            if self.myRules.wasSaved == True:
                self.ruleList = self.myRules.ruleList
                self.savedRules = True
        elif controlId == 330:      # Playlist-type channel, playlist button
            retval = dlg.browse(1, "Channel " + str(self.channel) + " Playlist", "files", ".xsp", False, False, "special://videoplaylists/")
            if retval != "special://videoplaylists/":
                self.getControl(330).setLabel(self.getSmartPlaylistName(retval), label2=retval)
                
        elif controlId == 140:      # Network TV channel, left
            self.changeListData(self.networkList, 142, -1)
        elif controlId == 141:      # Network TV channel, right
            self.changeListData(self.networkList, 142, 1)
        elif controlId == 150:      # Movie studio channel, left
            self.changeListData(self.studioList, 152, -1)
        elif controlId == 151:      # Movie studio channel, right
            self.changeListData(self.studioList, 152, 1)
        elif controlId == 160:      # TV Genre channel, left
            self.changeListData(self.showGenreList, 162, -1)
        elif controlId == 161:      # TV Genre channel, right
            self.changeListData(self.showGenreList, 162, 1)
        elif controlId == 170:      # Movie Genre channel, left
            self.changeListData(self.movieGenreList, 172, -1)
        elif controlId == 171:      # Movie Genre channel, right
            self.changeListData(self.movieGenreList, 172, 1)
        elif controlId == 180:      # Mixed Genre channel, left
            self.changeListData(self.mixedGenreList, 182, -1)
        elif controlId == 181:      # Mixed Genre channel, right
            self.changeListData(self.mixedGenreList, 182, 1)
        elif controlId == 190:      # TV Show channel, left
            self.changeListData(self.showList, 192, -1)
        elif controlId == 191:      # TV Show channel, right
            self.changeListData(self.showList, 192, 1)
        elif controlId == 200:      # Directory channel, select
            dlg = xbmcgui.Dialog()
            retval = dlg.browse(0, "Channel " + str(self.channel) + " Directory", "files")
            if len(retval) > 0:
                self.getControl(200).setLabel(retval)       
        elif controlId == 201:      # Directory SortOrder, left
            self.changeListData(self.SortOrderList, 203, -1)
        elif controlId == 202:      # Directory SortOrder, right
            self.changeListData(self.SortOrderList, 203, 1)   
        elif controlId == 210:    # LiveTV Channel ID, select
            chnlst = ChannelList() 
            if self.getControl(212).getLabel() != '':
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                setting3 = self.getControl(212).getLabel()
                if setting3.startswith('http'):
                    xmlTvFile = setting3
                else:
                    xmlTvFile = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('xmltvLOC'), str(setting3) +'.xml'))
                dnameID, CHid = chnlst.findZap2itID(self.getControl(213).getLabel(), xmlTvFile)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                self.getControl(210).setLabel(CHid)
            else:  
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Input channel & xmltv name first", 1000, THUMB) )
        elif controlId == 211:    # LiveTV Source Path, select
            dlg = xbmcgui.Dialog()
            retval = dlg.browse(1, "Channel " + str(self.channel) + " LiveTV", "video", "", False, False, "pvr://")
            if len(retval) > 0:
                self.getControl(211).setLabel(retval)
        elif controlId == 212:    # LiveTV XMLTV Name, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(212).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) != '':
                self.getControl(212).setLabel(retval)
        elif controlId == 213:    # LiveTV Channel Name, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(213).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(213).setLabel(retval)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", retval)
        elif controlId == 220:    # InternetTV Duration, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(220).getLabel(), type=xbmcgui.INPUT_NUMERIC)
            if len(retval) > 0:
                self.getControl(220).setLabel(retval)
        elif controlId == 221:    # InternetTV Source Path, select
            dlg = xbmcgui.Dialog()
            retval = dlg.browse(1, "Channel " + str(self.channel) + " InternetTV", "video", "", False, False, "")
            if len(retval) > 0:
                self.getControl(221).setLabel(retval)
        elif controlId == 222:    # InternetTV Title, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(222).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) != '':
                self.getControl(222).setLabel(retval)
        elif controlId == 223:    # InternetTV Description, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(223).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(223).setLabel(retval)
        elif controlId == 230:    # Youtube Channel, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(230).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(230).setLabel(retval)
        elif controlId == 234:      # Youtube Type, left
            self.changeListData(self.YoutubeList, 231, -1)
        elif controlId == 235:      # Youtube Type, right
            self.changeListData(self.YoutubeList, 231, 1)
        elif controlId == 238:      # Youtube MediaLimit, left
            self.changeListData(self.MediaLimitList, 232, -1)
        elif controlId == 239:      # Youtube MediaLimit, right
            self.changeListData(self.MediaLimitList, 232, 1)   
        elif controlId == 236:      # Youtube SortOrder, left
            self.changeListData(self.SortOrderList, 233, -1)
        elif controlId == 237:      # Youtube SortOrder, right
            self.changeListData(self.SortOrderList, 233, 1)   
        elif controlId == 240:    # RSS Feed URL, input
            dlg = xbmcgui.Dialog()
            retval = dlg.input(self.getControl(240).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(240).setLabel(retval)
        elif controlId == 248:      # RSS MediaLimit, left
            self.changeListData(self.MediaLimitList, 242, -1)
        elif controlId == 249:      # RSS MediaLimit, right
            self.changeListData(self.MediaLimitList, 242, 1)   
        elif controlId == 246:      # RSS SortOrder, left
            self.changeListData(self.SortOrderList, 243, -1)
        elif controlId == 247:      # RSS SortOrder, right
            self.changeListData(self.SortOrderList, 243, 1)
        #Plugin
        elif controlId == 280:      # Plugin Source, input
            select = selectDialog(self.pluginNameList, 'Select Plugin for parsing')
            self.PluginSourceName = self.pluginNameList[select]
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", self.PluginSourceName)
            self.PluginSourcePath = self.pluginPathList[select]
            self.PluginSourcePath = 'plugin://' + self.PluginSourcePath
            self.getControl(280).setLabel(self.PluginSourceName)
            self.getControl(281).setLabel(' ')
        elif controlId == 281:      # Plugin Path, input
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )

            if len(self.getControl(281).getLabel()) > 1:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(chnlst.PluginInfo(self.PluginSourcePathDir), 'Dir')
            else:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(chnlst.PluginInfo(self.PluginSourcePath), 'Dir')
                self.DirName = ' '
                self.PluginSourcePathDir = ' '
                self.getControl(282).setLabel(' ')
            
            select = selectDialog(PluginDirNameLst, 'Select Directory or leave blank for root')
            selectItem = PluginDirNameLst[select]
            
            if selectItem == '[B]Back[/B]':
                self.getControl(281).setLabel('')
                self.getControl(282).setLabel('')
            elif selectItem == '[B]Clear[/B]':
                self.DirName = ' '
                self.PluginSourcePathDir = ' '
                self.getControl(281).setLabel(' ')
                self.getControl(282).setLabel(' ')
            else:
                self.DirName += '/' + selectItem
                PathName = PluginDirPathLst[select]
                if self.DirName.startswith(' /'):
                    self.DirName = self.DirName[2:]
                elif self.DirName.startswith('/'):
                    self.DirName = self.DirName[1:]
                if len(self.DirName) > 0:
                    self.getControl(281).setLabel(self.DirName)
                    self.getControl(282).setLabel(self.PluginSourcePath+'/'+self.DirName)
                    self.PluginSourcePathDir = PathName
            
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", selectItem)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        elif controlId == 283:    # Plugin Exclude, input
            retval = dlg.input(self.getControl(283).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) != '':
                self.getControl(283).setLabel(retval)
        elif controlId == 285:      # Plugin MediaLimit, left
            self.changeListData(self.MediaLimitList, 284, -1)
        elif controlId == 286:      # Plugin MediaLimit, right
            self.changeListData(self.MediaLimitList, 284, 1)   
        elif controlId == 288:      # Plugin SortOrder, left
            self.changeListData(self.SortOrderList, 287, -1)
        elif controlId == 289:      # Plugin SortOrder, right
            self.changeListData(self.SortOrderList, 287, 1)   
        self.log("onClick return")


    def changeListData(self, thelist, controlid, val):
        self.log("changeListData " + str(controlid) + ", " + str(val))
        curval = self.getControl(controlid).getLabel()
        found = False
        index = 0

        if len(thelist) == 0:
            self.getControl(controlid).setLabel('')
            self.log("changeListData return Empty list")
            return

        for item in thelist:
            if item == curval:
                found = True
                break

            index += 1

        if found == True:
            index += val

        while index < 0:
            index += len(thelist)

        while index >= len(thelist):
            index -= len(thelist)

        self.getControl(controlid).setLabel(thelist[index])
        self.log("changeListData return")


    def getSmartPlaylistName(self, fle):
        self.log("getSmartPlaylistName " + fle)
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log('Unable to open smart playlist')
            return ''

        try:
            dom = parse(xml)
        except:
            xml.close()
            self.log("getSmartPlaylistName return unable to parse")
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log("getSmartPlaylistName return " + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.playlisy('Unable to find element name')

        self.log("getSmartPlaylistName return")


    def changeChanType(self, channel, val):
        self.log("changeChanType " + str(channel) + ", " + str(val))
        chantype = 9999

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
        except:
            self.log("Unable to get channel type")

        if val != 0:
            chantype += val

            if chantype < 0:
                chantype = 9999
            elif chantype == 10000:
                chantype = 0
            elif chantype == 9998:
                chantype = NUMBER_CHANNEL_TYPES - 1
            elif chantype == NUMBER_CHANNEL_TYPES:
                chantype = 9999

            ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", str(chantype))
        else:
            self.channel_type = chantype
            self.setting1 = ''
            self.setting2 = ''
            self.setting3 = ''
            self.setting4 = ''

            try:
                self.setting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
                self.setting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
                self.setting3 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
                self.setting4 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_4")
            except:
                pass

        for i in range(NUMBER_CHANNEL_TYPES):
            if i == chantype:
                self.getControl(120 + i).setVisible(True)
                self.getControl(110).controlDown(self.getControl(120 + ((i + 1) * 10)))

                try:
                    if chantype > 7:
                        raise
                        
                    self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10 + 1)))
                except:
                    self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10)))
            else:
                try:
                    self.getControl(120 + i).setVisible(False)
                except:
                    pass

        self.fillInDetails(channel)
        self.log("changeChanType return")


    def fillInDetails(self, channel):
        self.log("fillInDetails " + str(channel))
        self.getControl(104).setLabel("Channel " + str(channel))
        chantype = 9999
        chansetting1 = ''
        chansetting2 = ''
        chansetting3 = ''
        chansetting4 = ''
        channame = ''

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type"))
            chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
            chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
            chansetting3 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_3")
            chansetting4 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_4")
            channame = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        except:
            self.log("Unable to get some setting")

        self.getControl(109).setLabel(self.getChanTypeLabel(chantype))

        if chantype == 0:
            plname = self.getSmartPlaylistName(chansetting1)

            if len(plname) == 0:
                chansetting1 = ''
            self.getControl(330).setLabel(self.getSmartPlaylistName(chansetting1), label2=chansetting1)
            
        elif chantype == 1:
            self.getControl(142).setLabel(self.findItemInList(self.networkList, chansetting1))
        elif chantype == 2:
            self.getControl(152).setLabel(self.findItemInList(self.studioList, chansetting1))
        elif chantype == 3:
            self.getControl(162).setLabel(self.findItemInList(self.showGenreList, chansetting1))
        elif chantype == 4:
            self.getControl(172).setLabel(self.findItemInList(self.movieGenreList, chansetting1))
        elif chantype == 5:
            self.getControl(182).setLabel(self.findItemInList(self.mixedGenreList, chansetting1))
        elif chantype == 6:
            self.getControl(192).setLabel(self.findItemInList(self.showList, chansetting1))
            self.getControl(194).setSelected(chansetting2 == str(MODE_ORDERAIRDATE))
        elif chantype == 7:
            if (chansetting1.find('/') > -1) or (chansetting1.find('\\') > -1):
                plname = self.getSmartPlaylistName(chansetting1)
                if len(plname) != 0:
                    chansetting1 = ''
            else:
                chansetting1 = ''
            self.getControl(200).setLabel(chansetting1)
            self.getControl(203).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 8:
            self.getControl(210).setLabel(chansetting1)
            self.getControl(211).setLabel(chansetting2)
            self.getControl(212).setLabel(chansetting3)
            self.getControl(213).setLabel(channame)
        elif chantype == 9:
            self.getControl(220).setLabel(chansetting1)
            self.getControl(222).setLabel(chansetting3)
            self.getControl(223).setLabel(chansetting4)
        elif chantype == 10:
            self.getControl(231).setLabel(chansetting1)
            self.getControl(230).setLabel(self.findItemInList(self.YoutubeList, chansetting2))
            self.getControl(232).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(233).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 11:
            self.getControl(240).setLabel(chansetting1)
            self.getControl(242).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(243).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 12:
            self.getControl(250).setLabel(chansetting1)
            self.getControl(251).setLabel(chansetting2)
            self.getControl(252).setLabel(chansetting3)
            self.getControl(253).setLabel(chansetting4)
        elif chantype == 13:
            self.getControl(260).setLabel(chansetting1)
            self.getControl(261).setLabel(chansetting2)
            self.getControl(262).setLabel(chansetting3)
            self.getControl(263).setLabel(chansetting4)
        elif chantype == 14:
            self.getControl(270).setLabel(chansetting1)
            self.getControl(271).setLabel(chansetting2)
            self.getControl(272).setLabel(chansetting3)
            self.getControl(273).setLabel(chansetting4)
        elif chantype == 15:
            self.getControl(282).setLabel(chansetting1)
            self.getControl(283).setLabel(chansetting2)
            self.getControl(284).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(287).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 16:
            self.getControl(290).setLabel(chansetting1)
            self.getControl(291).setLabel(chansetting2)
            self.getControl(292).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(293).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
            
        self.loadRules(channel)
        self.log("fillInDetails return")


    def loadRules(self, channel):
        self.log("loadRules")
        self.ruleList = []
        self.myRules.allRules

        try:
            rulecount = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_rulecount'))

            for i in range(rulecount):
                ruleid = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_rule_' + str(i + 1) + '_id'))

                for rule in self.myRules.allRules.ruleList:
                    if rule.getId() == ruleid:
                        self.ruleList.append(rule.copy())

                        for x in range(rule.getOptionCount()):
                            self.ruleList[-1].optionValues[x] = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_rule_' + str(i + 1) + '_opt_' + str(x + 1))

                        foundrule = True
                        break
        except:
            self.ruleList = []


    def saveRules(self, channel):
        self.log("saveRules")
        rulecount = len(self.ruleList)
        ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_rulecount', str(rulecount))
        index = 1

        for rule in self.ruleList:
            ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_rule_' + str(index) + '_id', str(rule.getId()))

            for x in range(rule.getOptionCount()):
                ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_rule_' + str(index) + '_opt_' + str(x + 1), rule.getOptionValue(x))

            index += 1


    def findItemInList(self, thelist, item):
        loitem = item.lower()

        for i in thelist:
            if loitem == i.lower():
                return item

        if len(thelist) > 0:
            return thelist[0]

        return ''


    def getChanTypeLabel(self, chantype):
        if chantype == 0:
            return "Custom Playlist"
        elif chantype == 1:
            return "TV Network"
        elif chantype == 2:
            return "Movie Studio"
        elif chantype == 3:
            return "TV Genre"
        elif chantype == 4:
            return "Movie Genre"
        elif chantype == 5:
            return "Mixed Genre"
        elif chantype == 6:
            return "TV Show"
        elif chantype == 7:
            return "Directory"
        elif chantype == 8:
            return "LiveTV"
        elif chantype == 9:
            return "InternetTV"
        elif chantype == 10:
            return "Youtube"
        elif chantype == 11:
            return "RSS"
        elif chantype == 12:
            return "Music"
        elif chantype == 13:
            return "Music Videos"
        elif chantype == 14:
            return "Exclusive"
        elif chantype == 15:
            return "Plugin"
        elif chantype == 16:
            return "UPNP"
        elif chantype == 9999:
            return "None"
            # for i in range(NUMBER_CHANNEL_TYPES):
                # if i == chantype:
                    # self.getControl((120 + ((i + 1) * 10))+ 1).setLabel(' ')
                    # self.getControl((120 + ((i + 1) * 10))+ 2).setLabel(' ')
                    # self.getControl((120 + ((i + 1) * 10))+ 3).setLabel(' ')
                    # self.getControl((120 + ((i + 1) * 10))+ 4).setLabel(' ')
        return ''

        
    def prepareConfig(self):
        self.log("prepareConfig")
        self.showList = []
        self.getControl(105).setVisible(False)
        self.getControl(106).setVisible(False)
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("PseudoTV Live", "Preparing Configuration")
        self.dlg.update(1)
        chnlst = ChannelList()        
        self.dlg.update(50)
        chnlst.fillMusicInfo()       
        self.dlg.update(60)
        chnlst.fillTVInfo()
        self.dlg.update(70)
        chnlst.fillMovieInfo()
        self.dlg.update(80)
        chnlst.fillPluginList()
        self.dlg.update(90)
        self.mixedGenreList = chnlst.makeMixedList(chnlst.showGenreList, chnlst.movieGenreList)
        self.networkList = chnlst.networkList
        self.studioList = chnlst.studioList
        self.showGenreList = chnlst.showGenreList
        self.movieGenreList = chnlst.movieGenreList
        self.musicGenreList = chnlst.musicGenreList
        self.pluginPathList = chnlst.pluginPathList
        self.pluginNameList = chnlst.pluginNameList
        self.YoutubeList = ['Channel ID','Playlist','User Subscription','User Favorites','Search Query','Multi Playlist','Multi Channel','Raw gdata']
        self.MediaLimitList = ['25','50','100','150','200','250','500','1000']
        self.SortOrderList = ['Default','Random','Reverse']
        self.SourceTypes = ['PVR','HDhomerun','Local Video','Local Music','Plugin','UPNP','Favorites','Super Favorites','URL','Community List']
        self.DonorSourceTypes = ['PVR','HDhomerun','Local Video','Local Music','Plugin','UPNP','Favorites','Super Favorites','URL','Community List','Donor List','IPTV M3U','LiveStream XML','Navi-X PLX']
        
        for i in range(len(chnlst.showList)):
            self.showList.append(chnlst.showList[i][0])

        self.mixedGenreList.sort(key=lambda x: x.lower())
        self.listcontrol = self.getControl(102)

        for i in range(999):
            theitem = xbmcgui.ListItem()
            theitem.setLabel(str(i + 1))
            self.listcontrol.addItem(theitem)

        self.dlg.update(90)
        self.updateListing()
        self.dlg.close()
        self.getControl(105).setVisible(True)
        self.getControl(106).setVisible(False)
        self.setFocusId(102)
        self.log("prepareConfig return")

        
    def parsePlugin(self, DetailLST, type='all'):
        self.log("parsePlugin")
        dirCount = 0
        fleCount = 0
        chnlst = ChannelList()  
        PluginNameLst = []
        PluginPathLst = []
        PluginDirNameLst = []
        PluginDirPathLst = []
        
        for i in range(len(DetailLST)):
            Detail = (DetailLST[i]).split(',')
            filetype = Detail[0]
            title = Detail[1]
            title = chnlst.CleanLabels(title)
            genre = Detail[2]
            dur = Detail[3]
            description = Detail[4]
            file = Detail[5]
            
            if filetype == 'directory':
                dirCount += 1
                PluginDirNameLst.append(title)
                PluginDirPathLst.append(file)
            elif filetype == 'files':
                fleCount += 1
 
            PluginNameLst.append(title)
            PluginPathLst.append(file)
        
        PluginDirNameLst.append('[B]Back[/B]')
        PluginDirPathLst.append('')
        PluginDirNameLst.append('[B]Clear[/B]')
        PluginDirPathLst.append('')
        
        if type == 'Dir':
            return PluginDirNameLst, PluginDirPathLst
        else:
            return PluginNameLst, PluginPathLst
            

    def fillSources(self, type, path=''):
        self.log("fillSources")
        dlg = xbmcgui.Dialog()
        chnlst = ChannelList() 
        # Parse Source, return list
        if type == 'PVR':
            self.log("PVR")
            retval = dlg.browse(1, "Select File", "video", "", False, False, "pvr://")
            if len(retval) > 0:
                return retval
        elif type == 'HDhomerun':
            self.log("HDhomerun")
            retval = dlg.browse(1, "Select File", "video", "", False, False, "hdhomerun://")
            if len(retval) > 0:
                return retval
        elif type == 'Local Video':
            self.log("Local Video")
            retval = dlg.browse(1, "Select File", "video", ".avi|.mp4|.m4v|.3gp|.3g2|.f4v|.mov|.mkv|.flv|.ts|.m2ts|.strm", False, False, "")
            if len(retval) > 0:
                return retval            
        elif type == 'Local Music':
            self.log("Local Music")
            retval = dlg.browse(1, "Select File", "music", ".mp3|.flac|.mp4", False, False, "")
            if len(retval) > 0:
                return retval
        elif type == 'Plugin':
            self.log("Plugin")
            NameLst, PathLst = self.parsePlugin(chnlst.PluginInfo(path))
            select = selectDialog(NameLst, 'Select File')
            if len(PathLst[select]) > 0:
                return NameLst[select], PathLst[select]
        elif type == 'UPNP':
            self.log("UPNP")
            retval = dlg.browse(1, "Select File", "video", "", False, False, "upnp://")
            if len(retval) > 0:
                return retval
        elif type == 'Favorites':
            self.log("Favorites")
            PathLst = chnlst.loadFavourites()
            select = selectDialog(PathLst, 'Select Favorite')
            if len(PathLst[select]) > 0:
                return PathLst[select]
        elif type == 'Super Favorites':
            self.log("Super Favorites")
        elif type == 'URL':
            self.log("URL")
            input = dlg.input('Enter URL', type=xbmcgui.INPUT_ALPHANUM)
            if len(input) > 0:
                return input
        elif type == 'Community List':
            self.log("Community List")
        elif type == 'Donor List':
            self.log("Donor List")
        elif type == 'IPTV M3U':
            self.log("IPTV M3U")
        elif type == 'LiveStream XML':
            self.log("LiveStream XML")
        elif type == 'Navi-X PLX':
            self.log("Navi-X PLX")
        else:
            return  
           
            
    def updateListing(self, channel = -1):
        self.log("updateListing")
        start = 0
        end = 999

        if channel > -1:
            start = channel - 1
            end = channel

        for i in range(start, end):
            theitem = self.listcontrol.getListItem(i)
            chantype = 9999
            chansetting1 = ''
            chansetting2 = ''
            chansetting3 = ''
            chansetting4 = ''
            channame = ''
            newlabel = ''

            try:
                chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type"))
                chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_1")
                chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2")
                chansetting3 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_3")
                chansetting4 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_4")
                channame = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_rule_1_opt_1")
            except:
                pass

            if chantype == 0:
                newlabel = self.getSmartPlaylistName(chansetting1)
            elif chantype == 1 or chantype == 2 or chantype == 5 or chantype == 6:
                newlabel = chansetting1
            elif chantype == 3:
                newlabel = chansetting1 + " - TV"
            elif chantype == 4:
                newlabel = chansetting1 + " - Movies"
            elif chantype == 7:
                if chansetting1[-1] == '/' or chansetting1[-1] == '\\':
                    newlabel = os.path.split(chansetting1[:-1])[1]
                else:
                    newlabel = os.path.split(chansetting1)[1]
            elif chantype == 8:
                newlabel = channame + " - LiveTV"
            elif chantype == 9:
                newlabel = channame + " - InternetTV"
            elif chantype == 10:
                newlabel = channame + " - Youtube"            
            elif chantype == 11:
                newlabel = channame + " - RSS"            
            elif chantype == 12:
                newlabel = channame + " - Music"
            elif chantype == 13:
                newlabel = channame + " - Music Videos"
            elif chantype == 14:
                newlabel = channame + " - Exclusive"
            elif chantype == 15:
                newlabel = channame + " - Plugin"
            elif chantype == 16:
                newlabel = channame + " - UPNP"
            
            theitem.setLabel2(newlabel)
        self.log("updateListing return")

        
__cwd__ = REAL_SETTINGS.getAddonInfo('path')

mydialog = ConfigWindow("script.pseudotv.live.ChannelConfig.xml", __cwd__, "Default")
del mydialog
