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
import datetime, time, threading
import datetime
import sys, re
import random

from urllib import unquote
from xml.dom.minidom import parse, parseString
from resources.lib.utils import *
from resources.lib.Globals import *
from resources.lib.ChannelList import ChannelList
from resources.lib.AdvancedConfig import AdvancedConfig
from resources.lib.FileAccess import FileAccess
from resources.lib.Migrate import Migrate

try:
    import resources.lib.Donor
    Donor_Downloaded = True
except:  
    Donor_Downloaded = False      
    pass
    
try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo-web/submit.php'
except:
    pass
    
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
            self.LockBrowse = False
            self.chnlst = ChannelList()
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
        self.KodiVideoSources()
        
        for i in range(NUMBER_CHANNEL_TYPES):
            try:
                self.getControl(120 + i).setVisible(False)
            except:
                pass

        migratemaster = Migrate()
        migratemaster.migrate()
        self.prepareConfig()
        self.myRules = AdvancedConfig("script.pseudotv.live.AdvancedConfig.xml", ADDON_PATH, "Default")
        self.getControl(239).setVisible(False)
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


    def KodiVideoSources(self):
        sourcepath = xbmc.translatePath(os.path.join('special://masterprofile/','sources.xml'))
        self.log("KodiVideoSources, sources.xml = " + sourcepath)
        PVR = False
        UPNP = False
        HDHR = False
        Restart = False
        a = '<video>'
        b = '<video>\n'

        if FileAccess.exists(sourcepath):
            json_query = ('{"jsonrpc":"2.0","method":"Files.GetSources","params":{"media":"video"},"id":1}')
            json_folder_detail = self.chnlst.sendJSON(json_query)
            file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
            
            for f in file_detail:
                match = re.search('"file" *: *"(.*?)",', f)
                if match:
                    if match.group(1) == 'pvr://':
                        PVR = True
                    elif match.group(1) == 'upnp://':
                        UPNP = True
                    elif match.group(1) == 'hdhomerun://':
                        HDHR = True         
            self.log("KodiVideoSources, PVR = " + str(PVR) + " UPNP = " + str(UPNP) + " HDHR = " + str(HDHR))
            
            if PVR == False:
                b = b + '<source>\n<name>PVR</name>\n<path pathversion="1">pvr://</path>\n<allowsharing>true</allowsharing>\n</source>\n'
            if UPNP == False:
                b = b + '<source>\n<name>UPnP Media Servers (Auto-Discover)</name>\n<path pathversion="1">upnp://</path>\n<allowsharing>true</allowsharing>\n</source>\n'
            if HDHR == False:
                b = b + '<source>\n<name>HDHomerun Devices</name>\n<path pathversion="1">hdhomerun://</path>\n<allowsharing>true</allowsharing>\n</source>\n'
            
            try:
                f = open(sourcepath, "r")
                linesLST = f.readlines()  
                f.close()

                for i in range(len(linesLST)):
                    line = linesLST[i]
                    if a in line:
                        self.log("KodiVideoSources, a found replacing with b = " + b)
                        replaceAll(sourcepath,a,b)  
                        Restart = True      
                        break
            except:
                self.log("KodiVideoSources, sources.xml missing")
                # todo write missing sourcxml Restart = True
                pass

        if Restart:
            if dlg.yesno("PseudoTV Live", "Updated Kodi video sources, reboot recommend! Exit XBMC?"):
                xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Quit(),%d,true)" % ( 0.5, ) )      
            
            
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
            ADDON_SETTINGS.setSetting(setting1, self.getControl(190).getLabel())
            if self.getControl(194).isSelected():
                ADDON_SETTINGS.setSetting(setting2, str(MODE_ORDERAIRDATE))
            else:
                ADDON_SETTINGS.setSetting(setting2, "0")
        elif chantype == 7:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(200).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(201).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(202).getLabel())
        elif chantype == 8: #LiveTV
            ADDON_SETTINGS.setSetting(setting1, self.getControl(216).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(217).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(212).getLabel())
        elif chantype == 9: #InternetTV
            ADDON_SETTINGS.setSetting(setting1, self.getControl(226).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(227).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(222).getLabel())
            ADDON_SETTINGS.setSetting(setting4, self.getControl(223).getLabel())
        elif chantype == 10: #Youtube
            ADDON_SETTINGS.setSetting(setting1, self.getControl(234).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(232).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(235).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(236).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 11: #RSS
            ADDON_SETTINGS.setSetting(setting1, self.getControl(241).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(242).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(243).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 12: #Music
            ADDON_SETTINGS.setSetting(setting1, self.getControl(250).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(251).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(252).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(253).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 13: #Music Videos
            ADDON_SETTINGS.setSetting(setting1, self.getControl(260).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(261).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(262).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(263).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 14: #Exclusive
            ADDON_SETTINGS.setSetting(setting1, self.getControl(270).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(271).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(272).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(273).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 15: #Plugin
            ADDON_SETTINGS.setSetting(setting1, self.getControl(282).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(283).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(284).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(285).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
        elif chantype == 16: #UPNP
            ADDON_SETTINGS.setSetting(setting1, self.getControl(292).getLabel())
            ADDON_SETTINGS.setSetting(setting2, self.getControl(293).getLabel())
            ADDON_SETTINGS.setSetting(setting3, self.getControl(294).getLabel())
            ADDON_SETTINGS.setSetting(setting4, (self.getControl(295).getLabel()).replace('Default','1').replace('Random','2').replace('Reverse','3'))
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
        dlg = xbmcgui.Dialog()
        YTFilter = ['User Subscription','User Favorites','Search Query','Raw gdata']  
        
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
            self.clearLabel()
        elif controlId == 111:      # Change channel type right
            self.changeChanType(self.channel, 1)
            self.clearLabel()
        elif controlId == 112:      # Ok button
            self.saveSettings()
            self.hideChanDetails()
        elif controlId == 113:      # Cancel button
            self.cancelChan()
            self.hideChanDetails()
        elif controlId == 555:      # Help Guide
            self.help()
        elif controlId == 114:      # Rules button
            self.myRules.ruleList = self.ruleList
            self.myRules.doModal()
            if self.myRules.wasSaved == True:
                self.ruleList = self.myRules.ruleList
                self.savedRules = True
        
        elif controlId == 115:      # Submit button
            # optionList = [chantype, setting1, setting2, setting3, setting4]
            # if dlg.yesno("Submit?", "Channel Configuration"):
                # sent = sendGmail("CommunityNetwork",str(optionList))
                # if sent:
                    # MSG = 'Thank you for your submisson'
                # else:
                    # MSG = 'Submisson Failed!' 
            MSG = 'Coming Soon' 
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
                
        elif controlId == 330:      # Playlist-type channel, playlist button
            retval = dlg.browse(1, "Channel " + str(self.channel) + " Playlist", "files", ".xsp", False, False, "special://videoplaylists/")
            if retval != "special://videoplaylists/":
                self.getControl(330).setLabel(self.getSmartPlaylistName(retval), label2=retval)
        
        elif controlId == 331:      # Playlist-type Editor button
            smartplaylist = "special://videoplaylists/" + os.path.split(self.getControl(330).getLabel2())[1]
            xbmc.executebuiltin( "ActivateWindow(10136,%s)" % (smartplaylist) )
        
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
            select = selectDialog(self.showList, 'Select TV Show')
            if len(self.showList[select]) > 0:
                self.getControl(190).setLabel(self.showList[select])
        
        elif controlId == 200:      # Directory channel, select
            retval = dlg.browse(0, "Channel " + str(self.channel) + " Directory", "files")
            if len(retval) > 0:
                self.getControl(200).setLabel(retval)       
        
        elif controlId == 201:    # setLabel MediaLimit, select 
            select = selectDialog(self.MediaLimitList, 'Select Media Limit')
            self.getControl(201).setLabel(self.MediaLimitList[select])
        elif controlId == 202:    # setLabel SortOrder, select 
            select = selectDialog(self.SortOrderList, 'Select Sorting Order')
            self.getControl(202).setLabel(self.SortOrderList[select]) 
        #LiveTV
        elif controlId == 216:    # LiveTV Channel ID, select
            setting3 = self.getControl(212).getLabel()
            if setting3 == '':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Enter Channel & XMLTV Name", 4000, THUMB) )
            else:
                if setting3.startswith('http') or setting3 == 'pvr' or setting3 == 'scheduledirect' or setting3 == 'zap2it':
                    xmlTvFile = setting3
                else:
                    xmlTvFile = os.path.join(XMLTV_LOC, str(setting3) +'.xml')
                dnameID, CHid = self.chnlst.findZap2itID(self.getControl(213).getLabel(), xmlTvFile)
                self.getControl(216).setLabel(CHid)

        elif controlId == 211:    # LiveTV Browse, select
            if self.LockBrowse:
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "File Already Selected", 1000, THUMB) )     
                return
            elif len(self.getControl(211).getLabel()) > 0:
                title, retval = self.fillSources('LiveTV', self.getControl(214).getLabel(), self.getControl(217).getLabel())
            else:
                try:
                    title, retval = self.fillSources('LiveTV', self.getControl(214).getLabel())
                except:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Select Source First", 1000, THUMB) )     
                    pass
            try:
                self.getControl(211).setLabel(title)
                self.getControl(217).setLabel(retval)
                title, genre = title.split(' - ')
            except:
                pass
        elif controlId == 212:    # LiveTV XMLTV Name, Select
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            xmltvLst = []
            dirs,files = xbmcvfs.listdir(XMLTV_CACHE_LOC)
            dir,file = xbmcvfs.listdir(XMLTV_LOC)
            xmltvcacheLst = [s.replace('.xml','') for s in files if s.endswith('.xml')] + ['pvr','scheduledirect','zap2it']
            xmltvLst = sorted_nicely([s.replace('.xml','') for s in file if s.endswith('.xml')] + xmltvcacheLst)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            select = selectDialog(xmltvLst, 'Select xmltv file')
            self.getControl(212).setLabel(xmltvLst[select])
        
        elif controlId == 213:    # LiveTV Channel Name, input
            retval = dlg.input(self.getControl(213).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(213).setLabel(retval)
                #Set Channel Name
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", retval) 
        
        elif controlId == 215:      # LiveTV Source Type, left
            self.changeListData(self.SourceList, 214, -1)
            self.clearLabel(211)
            self.clearLabel(217)
            self.LockBrowse = False
        elif controlId == 210:      # LiveTV Source Type, right
            self.changeListData(self.SourceList, 214, 1)
            self.clearLabel(211)
            self.clearLabel(217)
            self.LockBrowse = False

        #InternetTV
        elif controlId == 226:    # InternetTV Duration, input
            retval = dlg.input(self.getControl(226).getLabel(), type=xbmcgui.INPUT_NUMERIC)
            if len(retval) > 0:
                self.getControl(226).setLabel(retval)
            
        elif controlId == 221:    # InternetTV Browse, select
            if self.LockBrowse:
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "File Already Selected", 1000, THUMB) )     
                return
            elif len(self.getControl(221).getLabel()) > 0:
                title, retval = self.fillSources('InternetTV', self.getControl(224).getLabel(), self.getControl(227).getLabel())
            else:   
                title, retval = self.fillSources('InternetTV', self.getControl(224).getLabel())               
                
            self.getControl(221).setLabel(title)
            self.getControl(227).setLabel(retval)
            self.getControl(226).setLabel('5400')
            
            try:
                title, genre = title.split(' - ')
            except:
                pass
                
            #Set Channel Name
            self.getControl(222).setLabel(title)
            self.getControl(223).setLabel(self.getControl(224).getLabel())
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", title) 
        
        elif controlId == 222:    # InternetTV Title, input
            retval = dlg.input(self.getControl(222).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            self.getControl(222).setLabel(retval)
        
        elif controlId == 223:    # InternetTV Description, input
            retval = dlg.input(self.getControl(223).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            self.getControl(223).setLabel(retval)
        
        elif controlId == 225:      # InternetTV Source Type, left
            self.changeListData(self.SourceList, 224, -1)
            self.clearLabel(221)
            self.clearLabel(227)
            self.LockBrowse = False
        elif controlId == 220:      # InternetTV Source Type, right
            self.changeListData(self.SourceList, 224, 1)
            self.clearLabel(221)
            self.clearLabel(227)
            self.LockBrowse = False
        
        #Youtube
        elif controlId == 230:      # Youtube Type, left
            self.changeListData(self.YoutubeList, 232, -1)
            
            if (self.getControl(232).getLabel()).startswith('Multi'):
                self.getControl(239).setVisible(True)
                self.getControl(239).setLabel('Separate MultiTube with [COLOR=blue][B]|[/B][/COLOR], eg. ESPN[COLOR=blue][B]|[/B][/COLOR]ESPN2')
            elif (self.getControl(232).getLabel()).startswith('Search'):
                self.getControl(239).setVisible(True)
                self.getControl(239).setLabel('Search w/[COLOR=red]Safesearch [moderate|strict][/COLOR], eg. (Football+Soccer) or (Football Soccer) or ([COLOR=red]strict|[/COLOR]Dick+Cheney)')
            else:
                self.getControl(239).setVisible(False)
                
            if self.getControl(232).getLabel() in YTFilter:
                self.getControl(233).setVisible(False)
            else:
                self.getControl(233).setVisible(True)
                
        elif controlId == 231:      # Youtube Type, right
            self.changeListData(self.YoutubeList, 232, 1)  
            
            if (self.getControl(232).getLabel()).startswith('Multi'):
                self.getControl(239).setVisible(True)
                self.getControl(239).setLabel('Separate MultiTube with [COLOR=blue][B]|[/B][/COLOR], eg. ESPN[COLOR=blue][B]|[/B][/COLOR]ESPN2')
            elif (self.getControl(232).getLabel()).startswith('Search'):
                self.getControl(239).setVisible(True)
                self.getControl(239).setLabel('Search w/[COLOR=red]Safesearch [moderate|strict][/COLOR], eg. (Football+Soccer) or (Football Soccer) or ([COLOR=red]strict|[/COLOR]Dick+Cheney)')
            else:
                self.getControl(239).setVisible(False)
                
            if self.getControl(232).getLabel() in YTFilter:
                self.getControl(233).setVisible(False)
            else:
                self.getControl(233).setVisible(True)
                
        elif controlId == 233:    # Youtube Community List, Select
            if (self.getControl(232).getLabel()).startswith('Seasonal'): 
                today = datetime.datetime.now()
                month = today.strftime('%B')
                self.getControl(233).setLabel('Seasonal')
                self.getControl(234).setLabel(month)
                self.getControl(235).setLabel("200")
                self.getControl(236).setLabel("Default")
                #Set Channel Name
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "2")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", 'Seasonal') 
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_2_id", "13")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_2_opt_1", "168") 
            else:
                try:
                    Name, Option1, Option2, Option3, Option4 = self.fillSources('YouTube', 'Community List', self.getControl(232).getLabel())
                    self.getControl(233).setLabel(Name)
                    self.getControl(234).setLabel(Option1)
                    self.getControl(235).setLabel(Option3)
                    self.getControl(236).setLabel(Option4)
                    try:
                        title, genre = Name.split(' - ')
                    except:
                        title = Name
                        
                    #Set Channel Name
                    ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                    ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                    ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", title)                 
                except:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Select Youtube Type First", 1000, THUMB) )     
                    pass
                
        elif controlId == 234:    # Youtube Channel, input
            retval = dlg.input(self.getControl(234).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(234).setLabel(retval)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", retval)  
        
        elif controlId == 235:    # Youtube MediaLimit, select 
            select = selectDialog(self.MediaLimitList, 'Select Media Limit')
            self.getControl(235).setLabel(self.MediaLimitList[select])
        elif controlId == 236:    # Youtube SortOrder, select 
            select = selectDialog(self.SortOrderList, 'Select Sorting Order')
            self.getControl(236).setLabel(self.SortOrderList[select]) 
        
        #RSS
        elif controlId == 240:    # RSS Community List, Select
            Name, Option1, Option2, Option3, Option4 = self.fillSources('RSS', 'Community List')
            self.getControl(240).setLabel(Name)
            self.getControl(241).setLabel(Option1)
            self.getControl(242).setLabel(Option3)
            self.getControl(243).setLabel(Option4)
            #Set Channel Name
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", Name) 
            
        elif controlId == 241:    # RSS Feed URL, input
            retval = dlg.input(self.getControl(241).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(241).setLabel(retval) 
        elif controlId == 242:    # Youtube MediaLimit, select 
            select = selectDialog(self.MediaLimitList, 'Select Media Limit')
            self.getControl(242).setLabel(self.MediaLimitList[select])
        elif controlId == 243:    # Youtube SortOrder, select 
            select = selectDialog(self.SortOrderList, 'Select Sorting Order')
            self.getControl(243).setLabel(self.SortOrderList[select]) 

        #Plugin
        elif controlId == 280:      # Plugin Source, input
            select = selectDialog(self.pluginNameList, 'Select Plugin')
            self.PluginSourceName = (self.pluginNameList[select]).replace('[COLOR=blue][B]','').replace('[/B][/COLOR]','')
            
            if self.PluginSourceName == 'Community List':
                Name, Option1, Option2, Option3, Option4 = self.fillSources('Plugin', 'Community List')
                PLname, CHname = Name.split(' - ')
                PLname = PLname.split(':')[0]
                Dirs = ((Option1.split('//')[1]).split('/'))
                del Dirs[0]
                Dirname = "/".join(Dirs)
                self.getControl(280).setLabel(PLname)
                self.getControl(281).setLabel(Dirname)
                self.getControl(282).setLabel(Option1)
                self.getControl(284).setLabel(Option3)
                self.getControl(285).setLabel(Option4)
                if len(Option2) > 0:
                    self.getControl(283).setLabel(Option2)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", CHname)
            elif self.PluginSourceName == 'Donor List':
                Name, Option1, Option2, Option3, Option4 = self.fillSources('Plugin', 'Donor List')
                PLname, CHname = Name.split(' - ')
                PLname = PLname.split(':')[0]
                Dirs = ((Option1.split('//')[1]).split('/'))
                del Dirs[0]
                Dirname = "/".join(Dirs)
                self.getControl(280).setLabel(PLname)
                self.getControl(281).setLabel(Dirname)
                self.getControl(282).setLabel(Option1)
                self.getControl(284).setLabel(Option3)
                self.getControl(285).setLabel(Option4)
                if len(Option2) > 0:
                    self.getControl(283).setLabel(Option2)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", CHname)
            else:
                self.PluginSourcePath = self.pluginPathList[select]
                self.PluginSourcePath = 'plugin://' + self.PluginSourcePath
                self.getControl(280).setLabel(self.PluginSourceName)
                self.clearLabel(281)
        elif controlId == 281:      # Plugin browse, input
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            if len(self.getControl(281).getLabel()) > 0:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(self.chnlst.PluginInfo(self.PluginSourcePathDir), 'Dir')
            else:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(self.chnlst.PluginInfo(self.PluginSourcePath), 'Dir')
                self.DirName = ''
                self.PluginSourcePathDir = ''
                
            select = selectDialog(PluginDirNameLst, 'Select [COLOR=red][D][/COLOR]irectory')
            selectItem = PluginDirNameLst[select]
            
            if selectItem == '[B]Back[/B]':
                print 'todo'
            elif selectItem == '[B]Return[/B]':
                print 'todo'
            elif selectItem == '[B]Clear[/B]':
                self.DirName = ''
                self.PluginSourcePathDir = ''
            else:
                self.DirName += '/' + (self.chnlst.CleanLabels(selectItem).replace('/','%2F')).replace('[D]','').replace('[F]','')
                PathName = PluginDirPathLst[select]
                if self.DirName.startswith(' /'):
                    self.DirName = self.DirName[2:]
                elif self.DirName.startswith('/'):
                    self.DirName = self.DirName[1:]
                if len(self.DirName) > 0:
                    self.getControl(281).setLabel(self.DirName)
                    self.getControl(282).setLabel((self.PluginSourcePath+'/'+self.DirName).replace('/ ','/'))
                    self.PluginSourcePathDir = PathName
            try:
                Dir = self.DirName.rsplit('/',1)[1]
            except:
                Dir = selectItem
                
            Chname = self.chnlst.CleanLabels(((self.PluginSourcePath.split('//')[1]).split('/')[0]).replace('plugin.video.','').replace('plugin.audio.','') + ' ' + Dir).replace('[D]','')
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", Chname)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        elif controlId == 283:    # Plugin Exclude, input
            retval = dlg.input(self.getControl(283).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(283).setLabel(retval)
        elif controlId == 284:    # Plugin MediaLimit, select 
            select = selectDialog(self.MediaLimitList, 'Select Media Limit')
            self.getControl(284).setLabel(self.MediaLimitList[select])
        elif controlId == 285:    # Plugin SortOrder, select 
            select = selectDialog(self.SortOrderList, 'Select Sorting Order')
            self.getControl(285).setLabel(self.SortOrderList[select]) 
        #UPNP
        elif controlId == 290:      # UPNP Source, select 
            select = selectDialog(self.UPNPSourceList, 'Select UPNP Source')
            self.UPNPSourceList = (self.UPNPSourceList[select]).replace('[COLOR=blue][B]','').replace('[/B][/COLOR]','')
            self.getControl(290).setLabel(self.UPNPSourceList)

            if self.UPNPSourceList == 'Community List':
                Name, Option1, Option2, Option3, Option4 = self.fillSources('Playon', 'Community List')
                PLname, CHname = Name.split('- ')
                Dirs = ((Option1.split('//')[1]).split('/'))
                del Dirs[0]
                Dirname = "/".join(Dirs)
                self.getControl(290).setLabel(PLname)
                self.getControl(291).setLabel(Dirname)
                self.getControl(292).setLabel(Option1)
                self.getControl(293).setLabel(Option2)
                self.getControl(294).setLabel(Option3)
                self.getControl(295).setLabel(Option4)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", CHname)
            elif self.UPNPSourceList == 'Donor List':
                Name, Option1, Option2, Option3, Option4 = self.fillSources('Playon', 'Donor List')
                PLname, CHname = Name.split('- ')
                Dirs = ((Option1.split('//')[1]).split('/'))
                del Dirs[0]
                Dirname = "/".join(Dirs)
                self.getControl(290).setLabel(PLname)
                self.getControl(291).setLabel(Dirname)
                self.getControl(292).setLabel(Option1)
                self.getControl(293).setLabel(Option2)
                self.getControl(294).setLabel(Option3)
                self.getControl(295).setLabel(Option4)
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
                ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", CHname)
            else:
                retval = self.fillSources('Directory', 'UPNP')
                if len(retval) > 0:
                    self.getControl(291).setLabel(retval)
                    self.getControl(292).setLabel(retval)

        elif controlId == 291:      # UPNP browse, input
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            if len(self.getControl(291).getLabel()) > 0:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(self.chnlst.PluginInfo(self.PluginSourcePathDir), 'Dir')
            else:
                PluginDirNameLst, PluginDirPathLst = self.parsePlugin(self.chnlst.PluginInfo(self.PluginSourcePath), 'Dir')
                self.DirName = ''
                self.PluginSourcePathDir = ''
            select = selectDialog(PluginDirNameLst, 'Select [COLOR=red][D][/COLOR]irectory')
            selectItem = PluginDirNameLst[select]
            
            if selectItem == '[B]Back[/B]':
                print 'todo'
            elif selectItem == '[B]Return[/B]':
                print 'todo'
            elif selectItem == '[B]Clear[/B]':
                self.DirName = ''
                self.PluginSourcePathDir = ''
            else:
                self.DirName += '/' + (self.chnlst.CleanLabels(selectItem)).replace('[D]','').replace('[F]','')
                PathName = PluginDirPathLst[select]
                if self.DirName.startswith(' /'):
                    self.DirName = self.DirName[2:]
                elif self.DirName.startswith('/'):
                    self.DirName = self.DirName[1:]
                if len(self.DirName) > 0:
                    self.getControl(291).setLabel(self.DirName)
                    self.getControl(292).setLabel((self.PluginSourcePath+'/'+self.DirName.replace('/ ','/')))
                    self.PluginSourcePathDir = PathName
            try:
                Dir = self.DirName.rsplit('/',1)[1]
            except:
                Dir = selectItem
                
            Chname = self.chnlst.CleanLabels(((self.PluginSourcePath.split('//')[1]).split('/')[0]) + ' ' + Dir).replace('[D]','')
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rulecount", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_id", "1")
            ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_rule_1_opt_1", Chname)
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        elif controlId == 293:    # UPNP Exclude, input
            retval = dlg.input(self.getControl(293).getLabel(), type=xbmcgui.INPUT_ALPHANUM)
            if len(retval) > 0:
                self.getControl(293).setLabel(retval)
        elif controlId == 294:    # UPNP MediaLimit, select 
            select = selectDialog(self.MediaLimitList, 'Select Media Limit')
            self.getControl(294).setLabel(self.MediaLimitList[select])
        elif controlId == 295:    # UPNP SortOrder, select 
            select = selectDialog(self.SortOrderList, 'Select Sorting Order')
            self.getControl(295).setLabel(self.SortOrderList[select]) 
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
            self.playlist('Unable to find element name')

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
                if chantype != 0:
                    self.getControl(110).controlDown(self.getControl(120 + ((i + 1) * 10)))
                    try:
                        if chantype >= 8:
                            raise
                        self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10 + 1)))
                    except:
                        self.getControl(111).controlDown(self.getControl(120 + ((i + 1) * 10)))
                else:
                    self.getControl(110).controlDown(self.getControl(330))
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
            chansetting4 = (ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_4")).replace('1','Default').replace('2','Random').replace('3','Reverse')
            channame = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        except:
            self.log("Unable to get some setting")

        chansetting4 = chansetting4.replace('0','Default').replace('1','Random').replace('2','Reverse')
        self.getControl(109).setLabel(self.getChanTypeLabel(chantype))
   
        if chantype == 0:
            plname = self.getSmartPlaylistName(chansetting1)

            if len(plname) == 0:
                chansetting1 = ''
                # chansetting1 = 'Playlist:                                                                                                                      '
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
            self.getControl(190).setLabel(self.findItemInList(self.showList, chansetting1))
            self.getControl(194).setSelected(chansetting2 == str(MODE_ORDERAIRDATE))
        elif chantype == 7:
            if (chansetting1.find('/') > -1) or (chansetting1.find('\\') > -1):
                plname = self.getSmartPlaylistName(chansetting1)
                if len(plname) != 0:
                    chansetting1 = ''
            else:
                chansetting1 = ''
            self.getControl(200).setLabel(chansetting1)
            self.getControl(201).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(202).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 8:
            self.getControl(216).setLabel(chansetting1)
            self.getControl(217).setLabel(chansetting2)
            self.getControl(212).setLabel(chansetting3)
            self.getControl(213).setLabel(channame)
        elif chantype == 9:
            self.getControl(226).setLabel(chansetting1)
            self.getControl(227).setLabel(chansetting2)
            self.getControl(222).setLabel(chansetting3)
            self.getControl(223).setLabel(chansetting4)
        elif chantype == 10:
            chansetting2 = chansetting2.replace('7','Multi Playlist').replace('8','Multi Channel').replace('1','User Subscription')
            chansetting2 = chansetting2.replace('1','User Favorites').replace('5','Search Query').replace('9','Raw gdata')
            chansetting2 = chansetting2.replace('31','Seasonal').replace('1','Channel').replace('2','Playlist')    
            self.getControl(234).setLabel(chansetting1)
            self.getControl(232).setLabel(self.findItemInList(self.YoutubeList, chansetting2))
            self.getControl(235).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(236).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 11:
            self.getControl(241).setLabel(chansetting1)
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
            try:
                tmp = chansetting1.split('/')
                PlugPath = tmp[2]
                DirPath = "/".join(tmp[3:])
                self.getControl(280).setLabel(self.pluginNameList[self.findItemLens(self.pluginPathList, PlugPath)])
                self.getControl(281).setLabel(DirPath)
            except:
                pass
            self.getControl(282).setLabel(chansetting1)
            self.getControl(283).setLabel(chansetting2)
            self.getControl(284).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(285).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
        elif chantype == 16:
            self.getControl(292).setLabel(chansetting1)
            self.getControl(293).setLabel(chansetting2)
            self.getControl(294).setLabel(self.findItemInList(self.MediaLimitList, chansetting3))
            self.getControl(295).setLabel(self.findItemInList(self.SortOrderList, chansetting4))
            
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
        
        
    def findItemLens(self, thelist, item):
        loitem = item.lower()

        for i in range(len(thelist)):
            line = (thelist[i]).lower()
            if line == loitem:
                return i
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
            return "Music (Coming Soon)"
        elif chantype == 13:
            return "Music Videos (Coming Soon)"
        elif chantype == 14:
            return "Exclusive (Coming Soon)"
        elif chantype == 15:
            return "Plugin"
        elif chantype == 16:
            return "UPNP (Coming Soon)"
        elif chantype == 9999:
            return "None"
        return ''

        
    def prepareConfig(self):
        self.log("prepareConfig")
        self.showList = []
        self.getControl(105).setVisible(False)
        self.getControl(106).setVisible(False)
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("PseudoTV Live", "Preparing Configuration")
        self.dlg.update(1)        
        self.dlg.update(50)
        self.chnlst.fillMusicInfo()       
        self.dlg.update(60)
        self.chnlst.fillTVInfo()
        self.dlg.update(70)
        self.chnlst.fillMovieInfo()
        self.dlg.update(80)
        self.chnlst.fillPluginList()
        self.dlg.update(90)
        self.chnlst.fillFavourites()
        self.dlg.update(95)
        self.mixedGenreList = self.chnlst.makeMixedList(self.chnlst.showGenreList, self.chnlst.movieGenreList)
        self.networkList = self.chnlst.networkList
        self.studioList = self.chnlst.studioList
        self.showGenreList = self.chnlst.showGenreList
        self.movieGenreList = self.chnlst.movieGenreList
        self.musicGenreList = self.chnlst.musicGenreList
        self.FavouritesPathList = self.chnlst.FavouritesPathList
        self.FavouritesNameList = self.chnlst.FavouritesNameList
        self.YoutubeList = ['Channel','Playlist','User Subscription','User Favorites','Search Query','Multi Playlist','Multi Channel','Raw gdata','Seasonal']
        self.MediaLimitList = ['25','50','100','150','200','250','500','1000']
        self.SortOrderList = ['Default','Random','Reverse']
        self.SourceTypes = ['PVR','HDhomerun','Local Video','Local Music','Plugin','UPNP','Kodi Favourites','Super Favourites','URL','Community List']
        self.DonorSourceTypes = ['PVR','HDhomerun','Local Video','Local Music','Plugin','UPNP','Kodi Favourites','Super Favourites','URL','Community List','Donor List','IPTV M3U','LiveStream XML','Navi-X PLX']
        self.ExternalPlaylistSources = ['[COLOR=blue][B]Community List[/B][/COLOR]','Local File','URL']
        
        
        
        if Donor_Downloaded:
            self.pluginPathList = ['',''] + self.chnlst.pluginPathList
            self.pluginNameList = ['[COLOR=blue][B]Community List[/B][/COLOR]','[COLOR=blue][B]Donor List[/B][/COLOR]'] + self.chnlst.pluginNameList
            self.UPNPSourceList = ['[COLOR=blue][B]Community List[/B][/COLOR]','[COLOR=blue][B]Donor List[/B][/COLOR]','Local UPNP']
            self.SourceList = self.DonorSourceTypes
        else:
            self.pluginPathList = [''] + self.chnlst.pluginPathList
            self.pluginNameList = ['[COLOR=blue][B]Community List[/B][/COLOR]'] + self.chnlst.pluginNameList
            self.UPNPSourceList = ['[COLOR=blue][B]Community List[/B][/COLOR]','Local UPNP']
            self.SourceList = self.SourceTypes
            
        for i in range(len(self.chnlst.showList)):
            self.showList.append(self.chnlst.showList[i][0])
        
        self.showList =  sorted_nicely(self.showList)
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
        try:
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            dirCount = 0
            fleCount = 0
            PluginNameLst = []
            PluginPathLst = []
            PluginDirNameLst = []
            PluginDirPathLst = []
            
            for i in range(len(DetailLST)):
                Detail = (DetailLST[i]).split(',')
                filetype = Detail[0]
                title = Detail[1]
                title = self.chnlst.CleanLabels(title)
                genre = Detail[2]
                dur = Detail[3]
                description = Detail[4]
                file = Detail[5]
                
                if filetype == 'directory':
                    dirCount += 1
                    Color = 'red'
                    fileInt = 'D'
                    PluginDirNameLst.append(('[COLOR=%s][%s] [/COLOR]' + title) % (Color,fileInt))
                    PluginDirPathLst.append(file)
                elif filetype == 'file':
                    Color = 'green'
                    fileInt = 'F'
                    fleCount += 1
                    
                PluginNameLst.append(('[COLOR=%s][%s] [/COLOR]' + title) % (Color,fileInt))
                PluginPathLst.append(file)
            
            PluginDirNameLst.append('[B]Back[/B]')
            PluginDirPathLst.append('')
            PluginDirNameLst.append('[B]Return[/B]')
            PluginDirPathLst.append('')
            PluginDirNameLst.append('[B]Clear[/B]')
            PluginDirPathLst.append('') 
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            if type == 'Dir':
                if len(PluginDirNameLst[3:]) > 0:
                    return PluginDirNameLst, PluginDirPathLst
            else:
                return PluginNameLst, PluginPathLst
        except:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            buggalo.onExceptionRaised() 
             
            
    def clearLabel(self, id=None):
        print 'clearLabel'
        if id: 
            try:
                # self.getControl(id).reset()
                self.getControl(id).setLabel('')  
            except:
                pass
        else:
            for i in range(NUMBER_CHANNEL_TYPES):
                if i >= 7:
                    base = (120 + ((i + 1) * 10))
                    for n in range(10):
                        id = base + n
                        try:
                            # self.getControl(id).reset()
                            self.getControl(id).setLabel('')  
                        except:
                            pass
                            
                            
    def fillSources(self, type, source, path=None):
        self.log("fillSources")
        dlg = xbmcgui.Dialog()
        print source, type, path
        # Parse Source, return title, path
        try:
            if source == 'PVR':
                self.log("PVR")
                retval = dlg.browse(1, "Select File", "video", "", False, False, "pvr://")
                if len(retval) > 0:
                    return retval, retval
            elif source == 'HDhomerun':
                self.log("HDhomerun")
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Coming Soon", 4000, THUMB) )
            elif source == 'Local Video':
                self.log("Local Video")
                retval = dlg.browse(1, "Select File", "video", ".avi|.mp4|.m4v|.3gp|.3g2|.f4v|.mov|.mkv|.flv|.ts|.m2ts|.strm", False, False, "")
                if len(retval) > 0:
                    return retval, retval           
            elif source == 'Local Music':
                self.log("Local Music")
                retval = dlg.browse(1, "Select File", "music", ".mp3|.flac|.mp4", False, False, "")
                if len(retval) > 0:
                    return retval, retval
            elif source == 'Plugin':
                self.log("Plugin")
                if path:
                    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                    NameLst, PathLst = self.parsePlugin(self.chnlst.PluginInfo(path))
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" ) 
                    select = selectDialog(NameLst, 'Select [COLOR=green][F][/COLOR]ile')
                    if (NameLst[select]).startswith('[COLOR=green][F]'):
                        self.LockBrowse = True
                    return self.chnlst.CleanLabels(NameLst[select]).replace('[D]','').replace('[F]',''), PathLst[select]
                else:
                    if Donor_Downloaded:
                        # Remove Donor List Reference
                        select = selectDialog(self.pluginNameList[2:], 'Select Plugin')
                        return self.chnlst.CleanLabels((self.pluginNameList[2:])[select]), 'plugin://' + (self.pluginPathList[2:])[select]
                    else:
                        select = selectDialog(self.pluginNameList[1:], 'Select Plugin')
                        return self.chnlst.CleanLabels((self.pluginNameList[1:])[select]), 'plugin://' + (self.pluginPathList[1:])[select]
                        
            elif source == 'UPNP':
                self.log("UPNP")
                if type == 'Directory':
                    retval = dlg.browse(0, "Select Directory", "video", "", False, False, "upnp://")
                    return retval
                else:
                    retval = dlg.browse(1, "Select File", "video", "", False, False, "upnp://")
                    return retval
            elif source == 'Kodi Favourites':
                self.log("Kodi Favourites")
                select = selectDialog(self.FavouritesNameList, 'Select Favourites')
                return self.FavouritesNameList[select], self.FavouritesPathList[select]  
            elif source == 'Super Favourites':
                self.log("Super Favourites")
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                if path:
                    #remove unwanted reference to superfavourites 
                    if 'ActivateWindow%2810025%2C%22plugin%3A%2F%2Fplugin' in path:
                        path = unquote(path).replace('",return)','')
                        path = (path.split('ActivateWindow(10025,"')[1])
                    elif 'PlayMedia%28%22plugin%3A%2F%2Fplugin' in path:
                        path = unquote(path).replace('",return)','')
                        path = ((path.split('PlayMedia("')[1]).split('")')[0])

                    NameLst, PathLst = self.parsePlugin(self.chnlst.PluginInfo(path))
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                    select = selectDialog(NameLst, 'Select [COLOR=green][F][/COLOR]ile')
                    name = self.chnlst.CleanLabels(NameLst[select])
                    path = PathLst[select]
                    if name.startswith('[F]'):
                        #remove unwanted reference to superfavourites 
                        if 'ActivateWindow%2810025%2C%22plugin%3A%2F%2Fplugin' in path:
                            path = unquote(path).replace('",return)','')
                            path = (path.split('ActivateWindow(10025,"')[1])
                        elif 'PlayMedia%28%22plugin%3A%2F%2Fplugin' in path:
                            path = unquote(path).replace('",return)','')
                            path = ((path.split('PlayMedia("')[1]).split('")')[0])
                        print 'locked'
                        self.LockBrowse = True
                    return name.replace('[D]','').replace('[F]',''), path
                else:
                    NameLst, PathLst = self.parsePlugin(self.chnlst.PluginInfo('plugin://plugin.program.super.favourites'))
                    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                    select = selectDialog(NameLst, 'Select [COLOR=green][F][/COLOR]ile')
                    return self.chnlst.CleanLabels(NameLst[select]).replace('[D]','').replace('[F]',''), PathLst[select]
            elif source == 'URL':
                self.log("URL")
                input = dlg.input('Enter URL', type=xbmcgui.INPUT_ALPHANUM)
                if len(input) > 0:
                    return input, input
            elif source == 'Community List':
                self.log("Community List")
                if type == 'LiveTV':
                    self.log("Community List, LiveTV")
                    NameLst, Option1LST, PathLst, Option3LST, Option4LST = self.chnlst.fillExternalList('LiveTV')
                    select = selectDialog(NameLst, 'Select LiveTV')
                    try:
                        source, title = NameLst[select].split(' - ')
                    except:
                        title = NameLst[select]

                    self.getControl(216).setLabel(Option1LST[select])
                    self.getControl(212).setLabel(Option3LST[select])
                    self.getControl(213).setLabel(title)
                    return NameLst[select], PathLst[select]
                elif type == 'InternetTV':
                    self.log("Community List, InternetTV")
                    NameLst, Option1LST, PathLst, Option3LST, Option4LST = self.chnlst.fillExternalList('InternetTV')
                    select = selectDialog(NameLst, 'Select InternetTV')
                    self.getControl(226).setLabel(Option1LST[select])
                    self.getControl(222).setLabel(Option3LST[select])
                    self.getControl(223).setLabel(Option4LST[select])
                    return NameLst[select], PathLst[select]
                elif type == 'YouTube':
                    self.log("Community List, YouTube")
                    if path == 'Channel':
                        NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('YouTube', 'Channel')
                        select = selectDialog(NameLst, 'Select Channel')
                        return NameLst[select], Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse')
                    elif path == 'Playlist':
                        NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('YouTube', 'Playlist')
                        select = selectDialog(NameLst, 'Select Playlist')
                        return NameLst[select], Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse')
                    elif path == 'Multi Playlist':
                        NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('YouTube', 'Multi Playlist')
                        select = selectDialog(NameLst, 'Select Network Playlist ')
                        return NameLst[select], (Option1LST[select]).replace(',','|'), Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse')
                    elif path == 'Multi Channel':   
                        NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('YouTube', 'Multi Channel')
                        select = selectDialog(NameLst, 'Select Network Channel')
                        return NameLst[select], (Option1LST[select]).replace(',','|'), Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse')          
                elif type == 'RSS':
                    self.log("Community List, RSS")
                    NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('RSS')
                    select = selectDialog(NameLst, 'Select RSS Feed')
                    return NameLst[select], (Option1LST[select]).replace(',','|'), Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse') 
                elif type == 'Plugin':
                    self.log("Community List, Plugin")
                    NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('Plugin')
                    select = selectDialog(NameLst, 'Select Plugin')
                    return self.chnlst.CleanLabels(NameLst[select]), Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse') 
                elif type == 'Playon':
                    self.log("Community List, Playon")
                    NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('Playon')
                    select = selectDialog(NameLst, 'Select Playon')
                    return NameLst[select], Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse') 
            elif source == 'Donor List':
                self.log("Donor List")
                if type == 'LiveTV':
                    self.log("Donor List, LiveTV")
                    NameLst, Option1LST, PathLst, Option3LST, Option4LST = self.chnlst.fillExternalList('LiveTV','','Donor')
                    select = selectDialog(NameLst, 'Select LiveTV')
                    self.getControl(216).setLabel(Option1LST[select])
                    self.getControl(212).setLabel(Option3LST[select])
                    self.getControl(213).setLabel(NameLst[select])
                    return NameLst[select], PathLst[select]
                elif type == 'InternetTV':
                    self.log("Donor List, InternetTV")
                    NameLst, Option1LST, PathLst, Option3LST, Option4LST = self.chnlst.fillExternalList('InternetTV','','Donor')
                    select = selectDialog(NameLst, 'Select InternetTV')
                    self.getControl(226).setLabel(Option1LST[select])
                    self.getControl(222).setLabel(Option3LST[select])
                    self.getControl(223).setLabel(Option4LST[select])
                    return NameLst[select], PathLst[select]
                elif type == 'Plugin':
                    self.log("Donor List, Plugin")
                    NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('Plugin','','Donor')
                    select = selectDialog(NameLst, 'Select Plugin')
                    return self.chnlst.CleanLabels(NameLst[select]), Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse') 
                elif type == 'Playon':
                    self.log("Donor List, Playon")
                    NameLst, Option1LST, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('Playon','','Donor')
                    select = selectDialog(NameLst, 'Select Playon')
                    return NameLst[select], Option1LST[select], Option2LST[select], Option3LST[select], (Option4LST[select]).replace('1','Default').replace('2','Random').replace('3','Reverse') 
            elif source == 'IPTV M3U':
                self.log("IPTV M3U")
                select = selectDialog(self.ExternalPlaylistSources, 'Select IPTV M3U')
                if self.chnlst.CleanLabels(self.ExternalPlaylistSources[select]) == 'Community List':
                    self.log("IPTV M3U, Community List")
                    NameLst, PathLst, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('ExternalPlaylist','IPTV')
                    select = selectDialog(NameLst, 'Select IPTV Playlist')
                    NameLst, PathLst = self.chnlst.IPTVtuning('IPTV',PathLst[select])
                elif self.ExternalPlaylistSources[select] == 'Local File':
                    self.log("IPTV M3U, Local File")
                    retval = dlg.browse(1, "Select M3U", "video", ".m3u", False, False, "")
                    NameLst, PathLst = self.chnlst.IPTVtuning('IPTV',retval)
                elif self.ExternalPlaylistSources[select] == 'URL':
                    self.log("IPTV M3U, URL")
                    input, input = self.fillSources('','URL')
                    NameLst, PathLst = self.chnlst.IPTVtuning('IPTV',input)  
                    
                if len(NameLst) > 0:
                    select = selectDialog(NameLst, 'Select IPTV Feed')
                    return NameLst[select], PathLst[select]  
                else:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Invalid Selection", 1000, THUMB) )     
                    
            elif source == 'LiveStream XML':
                self.log("LiveStream XML")
                select = selectDialog(self.ExternalPlaylistSources, 'Select LiveStream XML')
                if self.chnlst.CleanLabels(self.ExternalPlaylistSources[select]) == 'Community List':
                    self.log("LiveStream XML, Community List")
                    NameLst, PathLst, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('ExternalPlaylist','LS')
                    select = selectDialog(NameLst, 'Select LiveStream Playlist')
                    NameLst, PathLst = self.chnlst.IPTVtuning('LS',PathLst[select])
                elif self.ExternalPlaylistSources[select] == 'Local File':
                    self.log("LiveStream XML, Local File")
                    retval = dlg.browse(1, "Select XML", "video", ".xml", False, False, "")
                    NameLst, PathLst = self.chnlst.IPTVtuning('LS',retval)
                elif self.ExternalPlaylistSources[select] == 'URL':
                    self.log("LiveStream XML, URL")
                    input, input = self.fillSources('','URL')
                    NameLst, PathLst = self.chnlst.IPTVtuning('LS',input)  
                    
                if len(NameLst) > 0:
                    select = selectDialog(NameLst, 'Select LiveStream Feed')
                    return NameLst[select], PathLst[select]  
                else:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Invalid Selection", 1000, THUMB) )  
            
            elif source == 'Navi-X PLX':
                self.log("Navi-X PLX")
                select = selectDialog(self.ExternalPlaylistSources, 'Select Navi-X PLX')
                if self.chnlst.CleanLabels(self.ExternalPlaylistSources[select]) == 'Community List':
                    self.log("Navi-X PLX, Community List")
                    NameLst, PathLst, Option2LST, Option3LST, Option4LST = self.chnlst.fillExternalList('ExternalPlaylist','Navix')
                    select = selectDialog(NameLst, 'Select Navi-X Playlist')
                    NameLst, PathLst = self.chnlst.IPTVtuning('Navix',PathLst[select])
                elif self.ExternalPlaylistSources[select] == 'Local File':
                    self.log("Navi-X PLX, Local File")
                    retval = dlg.browse(1, "Select PLX", "video", ".plx", False, False, "")
                    NameLst, PathLst = self.chnlst.IPTVtuning('Navix',retval)
                elif self.ExternalPlaylistSources[select] == 'URL':
                    self.log("Navi-X PLX, URL")
                    input, input = self.fillSources('','URL')
                    NameLst, PathLst = self.chnlst.IPTVtuning('Navix',input)
                    
                if len(NameLst) > 0:
                    select = selectDialog(NameLst, 'Select Navi-X Feed')
                    return NameLst[select], PathLst[select]
                else:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Invalid Selection", 1000, THUMB) )  
            else:
                return  
        except:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            buggalo.onExceptionRaised() 
            
            
    def help(self):
        BaseURL = 'https://pseudotv-live-community.googlecode.com/svn/'
        type = self.getControl(109).getLabel()  
        URL = BaseURL + "help_" + (type.lower()).replace(' ','%20')
        self.log("help URL = " + URL)
        title = type + ' Configuration Help'
        f = Open_URL(URL)
        text = f.read()
        showText(title, text)
          
          
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
