#   Copyright (C) 2013 Lunatixz
#
#
# This file is part of PseudoTV.
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

import subprocess, os, re, sys, time
import xbmcaddon, xbmc, xbmcgui, xbmcvfs
import Settings, Globals, ChannelList
import urllib, urllib2, httplib, random

from Globals import *
from xml.etree import ElementTree as ET
from FileAccess import FileLock, FileAccess
from urllib import unquote
from utils import *

try:
    from Donor import *
    Donor_Downloaded = True
    xbmc.log("script.pseudotv.live-Migrate: Donor Imported")
except Exception,e:
    Donor_Downloaded = False
    xbmc.log("script.pseudotv.live-Migrate: Donor Import Failed, Disabling Donor Features" + str(e))
    pass
       
class Migrate:

    def log(self, msg, level = xbmc.LOGDEBUG):
        Globals.log('Migrate: ' + msg, level)

        
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if Globals.DEBUG == 'true':
            Globals.log('Migrate: ' + msg, level)
            
            
    def migrate(self):
        self.log("migrate")
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))    
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.forceReset = True
        chanlist.createlist = True
        
        # If Autotune is enabled direct to autotuning
        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":
            self.log("autoTune, migrate")
            if self.autoTune():
                return True

        
    def autoTune(self):
        self.log('autoTune, Init')
        curtime = time.time()
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.makenewlists = True
        
        #Reserve channel check            
        if Globals.REAL_SETTINGS.getSetting("reserveChannels") == "true":
            print 'Reserved for Autotune'
            channelNum = 501
        else:
            channelNum = 1
        
        print 'channelNum', channelNum
        
        if channelNum == 999:
            return
        
        updateDialogProgress = 0
                
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Live", "Auto Tune")
        Youtube = chanlist.youtube_player()
        PlayonPath = chanlist.playon_player()
        
        limit = MEDIA_LIMIT[int(Globals.REAL_SETTINGS.getSetting('MEDIA_LIMIT'))]
        if limit == 0 or limit < 25 or limit >= 100:
            limit = 25

        # Custom Playlists
        self.updateDialogProgress = 1
        if Globals.REAL_SETTINGS.getSetting("autoFindCustom") == "true" :
            self.log("autoTune, Adding Custom Channel")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Custom Channel","")

            for i in range(999):
                if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Video Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/video/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
                    channelNum += 1
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Mixed Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/mixed/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp')),"")
                    channelNum += 1
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Music Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/music/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp')),"")
                    channelNum += 1
  
        
        # Custom SuperFavs
        self.updateDialogProgress = 5
        if Globals.REAL_SETTINGS.getSetting("autoFindSuperFav") == "true" :
            self.log("BuildSuperFav")
            SuperFav = chanlist.plugin_ok('plugin.program.super.favourites')
            
            if SuperFav == True:
                plugin_details = chanlist.PluginQuery('plugin://plugin.program.super.favourites')
                filter =['create new super folder','explore favourites','explore  favourites','explore xbmc favourites','explore kodi favourites','isearch','search']
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Super Favourites","")

                try:
                    Match = True
                    while Match:
                        
                        for f in (plugin_details):
                            filetypes = re.search('"filetype" *: *"(.*?)"', f)
                            labels = re.search('"label" *: *"(.*?)"', f)
                            files = re.search('"file" *: *"(.*?)"', f)

                            #if core variables have info proceed
                            if filetypes and files and labels:

                                filetype = filetypes.group(1)
                                file = (files.group(1))
                                label = (labels.group(1))

                                if label.lower() not in filter and label != '':
                                    if filetype == 'directory':
                                        SFmatch = unquote(file)
                                        SFmatch = SFmatch.split('Super+Favourites')[1].replace('\\','/')
                                        print SFmatch
                                        if SFmatch == '/PseudoTV_Live':
                                            plugin_details = chanlist.PluginQuery(file)
                                            break
                                        else:
                                            if SFmatch[0:9] != '/Channel_':
                                                Match = False
                                    
                                        SFname = SFmatch.replace('/PseudoTV_Live/','').replace('/','')
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "15")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'plugin://plugin.program.super.favourites' + SFmatch)
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "Create New Super Folder,Explore favourites,iSearch")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", SFname)
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                        channelNum += 1
                except:
                    pass
                            
        # LiveTV - PVR
        self.updateDialogProgress = 10
        if Globals.REAL_SETTINGS.getSetting("autoFindLivePVR") == "true":
            self.log("autoTune, Adding Live PVR Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live PVR Channels","")
            CHnum = 0
            RCHnum = 0
            CHid = 0
            CHlst = ''
            CHname = ''
            CHzapit = ''
            
            if Globals.REAL_SETTINGS.getSetting('xmltvLOC') != '':

                try:
                    json_query = '{"jsonrpc":"2.0","method":"PVR.GetChannels","params":{"channelgroupid":2}, "id":1}'
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    self.xmlTvFile = xbmc.translatePath(os.path.join(Globals.REAL_SETTINGS.getSetting('xmltvLOC'), 'xmltv.xml'))

                    f = FileAccess.open(self.xmlTvFile, "rb")
                    tree = ET.parse(f)
                    root = tree.getroot()
                    f.close()

                    file_detail = str(file_detail)
                    CHnameLST = re.findall('"label" *: *(.*?),', file_detail)
                    CHidLST = re.findall('"channelid" *: *(.*?),', file_detail)
                        
                    for CHnum in range(len(file_detail)):
                        CHname = CHnameLST[CHnum]
                        CHname = str(CHname)
                        CHname = CHname.split('"', 1)[-1]
                        CHname = CHname.split('"')[0]
                        CHlst = (CHname + ',' + CHidLST[CHnum])
                        inSet = False
                        # search xmltv for channel name, then find its id
                        for elem in root.getiterator():
                            if elem.tag == ("channel"):
                                name = elem.findall('display-name')
                                for i in name:
                                    RCHnum = (CHnum + 1)
                                    if CHname == i.text:
                                        CHzapit = elem.attrib
                                        CHzapit = str(CHzapit)
                                        CHzapit = CHzapit.split(": '", 1)[-1]
                                        CHzapit = CHzapit.split("'")[0]
                                        CHlst = (CHlst + ',' + str(CHzapit))
                                        inSet = True
                        
                        if inSet == True:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "pvr://channels/tv/All TV channels/" + str(CHnum) + ".pvr")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live PVR Channels",CHname)  
                            channelNum += 1
                        
                        if inSet == False:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "pvr://channels/tv/All TV channels/" + str(CHnum) + ".pvr")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Unavailable")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live PVR Channels",CHname)  
                            channelNum += 1 
                
                except:
                    pass
                
        
        # LiveTV - HDhomerun
        self.updateDialogProgress = 13
        if Globals.REAL_SETTINGS.getSetting("autoFindLiveHD") == "true" and (Globals.REAL_SETTINGS.getSetting('xmltvLOC') != '' or Globals.REAL_SETTINGS.getSetting('EPGDB') == "true"):
            self.log("autoTune, Adding Live HDhomerun Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live HDhomerun Channels","")
            CHnum = 0
            RCHnum = 0
            CHid = 0
            CHlst = ''
            CHname = ''
            CHzapit = ''
            LocalLST = []
            LocalFle = ''
            
            if Globals.REAL_SETTINGS.getSetting('xmltvLOC') != '' and Globals.REAL_SETTINGS.getSetting('autoFindLiveHDPath') != '':

                try:
                    HDstrmPath = Globals.REAL_SETTINGS.getSetting('autoFindLiveHDPath')  
                    self.xmlTvFile = xbmc.translatePath(os.path.join(Globals.REAL_SETTINGS.getSetting('xmltvLOC'), 'xmltv.xml')) 
                
                    f = FileAccess.open(self.xmlTvFile, "rb")
                    tree = ET.parse(f)
                    root = tree.getroot()
                    f.close()

                    LocalFLE = ''
                    LocalLST = str(xbmcvfs.listdir(HDstrmPath)[1]).replace("[","").replace("]","").replace("'","")
                    LocalLST = LocalLST.split(", ")
                    
                    for n in range(len(LocalLST)):
                        if '.strm' in (LocalLST[n]):
                            inSet = False
                            LocalFLE = (LocalLST[n])
                            filename = (HDstrmPath + LocalFLE)
                            CHname = os.path.splitext(LocalFLE)[0]
                            for elem in root.getiterator():
                                if elem.tag == ("channel"):
                                    name = elem.findall('display-name')

                                    for i in name:
                                        CHlst = ''
                                        RCHnum = (CHnum + 1)
                                        if CHname == i.text:
                                            inSet = True
                                            CHzapit = elem.attrib
                                            CHzapit = str(CHzapit)
                                            CHzapit = CHzapit.split(": '", 1)[-1]
                                            CHzapit = CHzapit.split("'")[0]
                                            CHlst = (CHlst + ',' + str(CHzapit))

                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live HDhomerun Channels",CHname)
                                channelNum += 1
                            
                            if inSet == False:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Unavailable")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Live HDhomerun Channels",CHname)
                                channelNum += 1
                except:
                    pass
        
        
        # LiveTV - USTVnow
        self.updateDialogProgress = 15
        if Globals.REAL_SETTINGS.getSetting("autoFindUSTVNOW") == "true":
            self.log("autoTune, Adding USTVnow Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channels","")
            CHnum = 0
            RCHnum = 0
            CHlst = ''
            CHid = 0
            CHname = ''
            CHzapit = ''
            LocalLST = []
            LocalFle = ''   
            f = ''
            
            USTVnow = chanlist.plugin_ok('plugin.video.ustvnow')
                
            if USTVnow == True:
                    
                try:
                    json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.ustvnow/live?mode=live"},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    url = 'https://docs.google.com/uc?export=download&id=0BxfXty1Ovu-EMzNTRmpDUTZ0VXM'
                    url_bak = 'https://docs.google.com/uc?export=download&id=0BxfXty1Ovu-ERlNKazAxWjBFSFE'
                    
                    try: 
                        f = urllib2.urlopen(url)
                        self.log("ustvnow, INFO: URL Connected...")
                    except urllib2.URLError as e:
                        f = urllib2.urlopen(url_bak)
                        self.log("ustvnow, INFO: URL_BAK Connected...")
                    except urllib2.URLError as e:
                        pass

                    tree = ET.parse(f)
                    root = tree.getroot()
                    f.close()
                  
                    for f in file_detail:                    
                        inSet = False
                        file = re.search('"file" *: *"(.*?)"', f)
                        label = re.search('"label" *: *"(.*?)"', f)
                        if file and label:
                            file = file.group(1)
                            label = label.group(1)
                            CHname = str(label.split(' -')[0])
                            
                            for elem in root.getiterator():
                                if elem.tag == ("channel"):
                                    name = elem.findall('display-name')

                                    for i in name:
                                        RCHnum = (CHnum + 1)
                                        if CHname == i.text:
                                            inSet = True
                                            CHzapit = elem.attrib
                                            CHzapit = str(CHzapit)
                                            CHzapit = CHzapit.split(": '", 1)[-1]
                                            CHzapit = CHzapit.split("'")[0]
                                            
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file) #Raw RTMP Link
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ustvnow")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channels",CHname)
                                channelNum += 1
                            
                            if inSet == False:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file) #Raw RTMP Link
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname + ' USTVnow')
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Unavailable")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channels",CHname)
                                channelNum += 1
                except:
                    pass
        
        # # LiveTV - smoothstreams
        
        #Needs rewrite, parse for zapit ids then match
        
        # self.updateDialogProgress = 16
        # if Globals.REAL_SETTINGS.getSetting("autoFindSmoothStreams") == "true":
            # self.log("autoTune, Adding SmoothStreams Channels")
            # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding SmoothStreams Channels","")
            # CHnum = 0
            # RCHnum = 0
            # CHlst = ''
            # CHid = 0
            # CHname = ''
            # CHzapit = ''
            # LocalLST = []
            # LocalFle = ''
            # f = ''

            # smoothstreams = chanlist.plugin_ok('plugin.video.mystreamstv.beta')

            # if smoothstreams == True:

                    # try:
                        # url = 'http://smoothstreams.tv/schedule/feed.xml'

                        # try:
                            # f = urllib2.urlopen(url)
                            # self.log("SmoothStreams, INFO: URL Connected...")
                        # except urllib2.URLError as e:
                            # pass

                        # tree = ET.parse(f)
                        # root = tree.getroot()
                        # f.close()

                        # for child in root:
                            # if child.tag == 'channel':
                                # CHid = child.get('id')
                                # #Fill needed so we get leading 0 for single-digit channels
                                # CHnum = str(CHid).zfill(2)
                                # CHname = child.find('display-name').text

                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.mystreamstv.beta/?path=/root/channels/&action=play_channel&chan="+CHnum)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", 'SS' + CHname)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Unavailable")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", 'SS' + CHname)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                # self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding SmoothStreams Channels",CHname)
                                # channelNum += 1
                    # except:
                        # pass
                        
        #TV - Networks/Genres
        self.updateDialogProgress = 20
        self.log("autoTune, autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoTune, autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("autoTune, Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for TV Channels","")
            chanlist.fillTVInfo()

        # need to add check for auto find network channels
        self.updateDialogProgress = 23
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("autoTune, Adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Networks","")

            for i in range(len(chanlist.networkList)):
                # channelNum = self.initialAddChannels(chanlist.networkList, 1, channelNum)
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1",Globals.uni(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Network",Globals.uni(chanlist.networkList[i]))
                channelNum += 1
        
        self.updateDialogProgress = 25
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("autoTune, Adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres","")

            # channelNum = self.initialAddChannels(chanlist.showGenreList, 3, channelNum)
            for i in range(len(chanlist.showGenreList)):
                # add network presets
                if chanlist.showGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.showGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres",Globals.uni(chanlist.showGenreList[i]) + " TV")
                    channelNum += 1
        
        self.updateDialogProgress = 28
        self.log("autoTune, autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoTune, autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        self.updateDialogProgress = 30
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("autoTune, Adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios","")

            for i in range(len(chanlist.studioList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios",Globals.uni(chanlist.studioList[i]))
                channelNum += 1
                
        self.updateDialogProgress = 33
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("autoTune, Adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","")

            # channelNum = self.initialAddChannels(chanlist.movieGenreList, 4, channelNum)
            for i in range(len(chanlist.movieGenreList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                if chanlist.movieGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.movieGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","Found " + Globals.uni(chanlist.movieGenreList[i]) + " Movies")
                    channelNum += 1
                
        self.updateDialogProgress = 35
        self.log("autoTune, autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Mixed Channels","")
            chanlist.fillMixedGenreInfo()
        
        self.updateDialogProgress = 38
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("autoTune, Adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres","")

            for i in range(len(chanlist.mixedGenreList)):
                # add network presets
                if chanlist.mixedGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.mixedGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres",Globals.uni(chanlist.mixedGenreList[i]) + " Mix")
                    channelNum += 1

        self.updateDialogProgress = 40
        self.log("autoTune, autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Music Channels","")
            chanlist.fillMusicInfo()

        self.updateDialogProgress = 50
        #Music Genre
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.log("autoTune, Adding Music Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres","")

            for i in range(len(chanlist.musicGenreList)):
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.musicGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres",Globals.uni(chanlist.musicGenreList[i]) + " Music")
                channelNum += 1
        
        #Music Videos - My Music
        self.updateDialogProgress = 53
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosMusicTV") == "true":
            self.log("autoTune, Adding My MusicTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding My MusicTV Music Videos","")
               
            MusicTV = False
            MusicTV = chanlist.plugin_ok('plugin.video.my_music_tv')
            
            if MusicTV == True:
                for i in range(999):
                    path = xbmc.translatePath("special://profile/addon_data/plugin.video.my_music_tv/cache/plist")
                    fle = os.path.join(path,"Channel_" + str(i) + ".xml.plist")
                    
                    if os.path.exists(xbmc.translatePath(fle)):
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "13")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "2")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "Channel_" + str(i))
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "My MusicTV " + str(i))  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "18")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "No")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding My MusicTV Music Videos","Channel " + str(i))
                        channelNum += 1
 
        #Music Videos - Last.fm user
        self.updateDialogProgress = 53
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFM") == "true":
            self.log("autoTune, Adding Last.FM Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Last.FM Music Videos","")
               
            if Youtube != False:
                user = Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFMuser")
                
                # add Last.fm user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", user)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Last.FM")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "18")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "No")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Last.FM Music Videos","User " + user)
                channelNum += 1

        #Music Videos - Youtube
        self.updateDialogProgress = 55
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosYoutube") == "true":
            self.log("autoTune, Adding Youtube Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Youtube Music Videos","")

            if Youtube != False:

                # add HungaryRChart presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "HungaryRChart")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "HRChart")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                # add BillbostdHot100 presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "BillbostdHot100")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "BillbostdHot100")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                # add TheTesteeTop50Charts presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "TheTesteeTop50Charts")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "TheTesteeTop50Charts")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")
                       
                channelNum = channelNum + 3
                self.logDebug('channelNum = ' + str(channelNum))
            
            
        #Music Videos - VevoTV
        self.updateDialogProgress = 58
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV") == "true":
            self.log("autoTune, Adding VevoTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding VevoTV Music Videos","")
            
            VevoTV = False
            VevoTV = chanlist.plugin_ok('plugin.video.vevo_tv')
            
            if VevoTV == True:

                # add VevoTV presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.vevo_tv/?url=TIVEVSTRUS00&mode=playOfficial")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "VEVO TV (US: Hits)")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "VevoTV - Hits")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "plugin://plugin.video.vevo_tv/?url=TIVEVSTRUS01&mode=playOfficial")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "VEVO TV (US: Flow)")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "VevoTV - Flow")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                       
                channelNum = channelNum + 2
                self.logDebug('channelNum = ' + str(channelNum))
            
            
        #Music Videos - Local
        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal") != "":
            self.log("autoTune, Adding Local Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Local Music Videos","")
            LocalVideo = str(Globals.REAL_SETTINGS.getSetting('autoFindMusicVideosLocal'))
            
            # add Local presets
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +LocalVideo+ "")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Music Videos")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")        
       
            channelNum = channelNum + 1
            self.logDebug('channelNum = ' + str(channelNum))
        
        
        #Plugin - Youtube
        self.updateDialogProgress = 63
        if Globals.REAL_SETTINGS.getSetting("autoFindYoutube") == "true":
            self.log("autoTune, Adding Youtube Favourites & Subscriptions")
            Username = Globals.REAL_SETTINGS.getSetting("autoFindYoutubeUser")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Youtube Favourites & Subscriptions","User " + Username)
            
            if Youtube != False:
            
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Username)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "3")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Username + "Subscriptions")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", Username)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "4")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", Username + "Favourites")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
            
                channelNum = channelNum + 2
                self.logDebug('channelNum = ' + str(channelNum))
        
        
        #Community lists#
        
        #Plugin
        self.updateDialogProgress = 70
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Plugins") == "true":
            self.log("autoTune, Adding Community Plugins")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Plugins","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/addons.xml'
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
            except urllib2.URLError as e:
                return
            
            try:
                for i in range(len(data)):
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split("|")
                    chtype = line[0]
                    setting_1 = line[1]
                    setting_2 = line[2]
                    setting_3 = line[3]
                    setting_4 = line[4]
                    channel_name = line[5]
                    
                    Pluginvalid = chanlist.plugin_ok(setting_1)
                    
                    if Pluginvalid == True:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", chtype)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", setting_2)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Plugins",channel_name)
                        channelNum += 1
            except:
                pass
                      
        #Playon
        self.updateDialogProgress = 71
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Playon") == "true":
            self.log("autoTune, Adding Community Playon")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Playon","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/playon.xml'
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
            except urllib2.URLError as e:
                return
            
            try:
                for i in range(len(data)):
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split("|")
                    chtype = line[0]
                    setting_1 = line[1]
                    setting_2 = line[2]
                    setting_3 = line[3]
                    setting_4 = line[4]
                    channel_name = line[5]

                    if PlayonPath != False:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", chtype)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", setting_2)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        channelNum += 1
                        
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Playon",channel_name)
            except:
                pass

        #Youtube Network
        self.updateDialogProgress = 72
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Networks") == "true":
            self.log("autoTune, Adding Community Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Networks","")    
            
            genre_filter = []
            Chan = []
            ChanLst = []
            Channel_List = 'https://pseudotv-live-community.googlecode.com/svn/youtube_channels_networks.xml'
            Playlist_List = 'https://pseudotv-live-community.googlecode.com/svn/youtube_playlists_networks.xml'
            
            if Globals.REAL_SETTINGS.getSetting("CN_TV") == "true":
                genre_filter.append('TV') 
            if Globals.REAL_SETTINGS.getSetting("CN_Movies") == "true":
                genre_filter.append('Movies') 
            if Globals.REAL_SETTINGS.getSetting("CN_Episodes") == "true":
                genre_filter.append('Episodes') 
            if Globals.REAL_SETTINGS.getSetting("CN_Sports") == "true":
                genre_filter.append('Sports') 
            if Globals.REAL_SETTINGS.getSetting("CN_News") == "true":
                genre_filter.append('News') 
            if Globals.REAL_SETTINGS.getSetting("CN_Kids") == "true":
                genre_filter.append('Kids') 
            if Globals.REAL_SETTINGS.getSetting("CN_Other") == "true":
                genre_filter.append('Other') 
            
            try:
                f = urllib2.urlopen(Channel_List)
                linesLST = f.readlines()
                linesLST = linesLST[2:]#remove first two lines
                f.close
            except urllib2.URLError as e:
                return
            
            try:
                for i in range(len(linesLST)):#parse list for info
                    line = str(linesLST[i])
                    line = line.split('|')
                    genre = line[0]
                    chanNum = line[1]
                    YoutubeID = line[2]
                    chanNam = line[3].replace('\n','')
                    if genre in genre_filter:#filter wanted genres
                        Chan.append(chanNum +'|'+ genre +'|'+ chanNam)

                Chan.sort()#sort, remove dupes
                ChanLst = sorted(set(Chan),key=Chan.index)

                for i in range(len(ChanLst)):
                    Chan = ChanLst[i].split('|')
                    ChanNum = Chan[0]
                    ChanGenre = Chan[1]
                    ChanNam = Chan[2]

                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "17")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", ChanNum)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", ChanGenre)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", ChanNam)  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community Networks",ChanNam)  
                    channelNum += 1 
            except:
                pass
            
            try:
                f = urllib2.urlopen(Playlist_List)
                linesLST = f.readlines()
                linesLST = linesLST[2:]#remove first two lines
                f.close
            except urllib2.URLError as e:
                return
            
            try:
                Chan = []
                ChanLst = []
                
                for i in range(len(linesLST)):#parse list for info
                    line = str(linesLST[i])
                    line = line.split('|')
                    genre = line[0]
                    chanNum = line[1]
                    YoutubeID = line[2]
                    chanNam = line[3].replace('\n','')
                    chanNam = chanNam.split('_')[0]
                    if genre in genre_filter:#filter wanted genres
                        Chan.append(chanNum +'|'+ genre +'|'+ chanNam)

                Chan.sort()#sort, remove dups
                ChanLst = sorted(set(Chan),key=Chan.index)

                for i in range(len(ChanLst)):
                    Chan = ChanLst[i].split('|')
                    ChanNum = Chan[0]
                    ChanGenre = Chan[1]
                    ChanNam = Chan[2]

                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "17")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "Playlist")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", ChanNum)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", ChanGenre)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", ChanNam)  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
            except:
                pass
                
                
        #InternetTV
        self.updateDialogProgress = 72
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_InternetTV") == "true":
            self.log("autoTune, Adding Community InternetTV")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community InternetTV","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/internettv.xml'
            fileNum = 0
            duplicate = []
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines    
                random.shuffle(data)#shuffle channel table
            except urllib2.URLError as e:
                return
            try:
                for i in range(len(data)):
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split("|")
                    chtype = line[0]
                    setting_1 = line[1]
                    setting_2 = line[2]
                    setting_3 = line[3]
                    setting_4 = line[4]
                    channel_name = line[5]

                    urlValid = chanlist.Valid_ok(setting_2)
                    
                    if urlValid == True and channel_name.lower() not in duplicate:
                        duplicate.append(channel_name.lower())
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", chtype)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", setting_2)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        channelNum += 1
                        
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Community InternetTV",channel_name)
                        fileNum += 1
                        
                    if fileNum >= limit:
                        break
            except:
                pass
                

        # RSS
        self.updateDialogProgress = 75
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_RSS") == "true":
            self.log("autoTune, Adding Community RSS")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community RSS","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/rss.xml'
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                random.shuffle(data)#shuffle channel table
            except urllib2.URLError as e:
                return
                
            for i in range(limit):
                try:
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                    setting_1 = line[0]
                    channel_name = line[1]
            
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "11")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community RSS",channel_name)
                    channelNum += 1
                except:
                    pass
            
        #Youtube Channels
        self.updateDialogProgress = 75    
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Channels") == "true":
            self.log("autoTune, Adding Community Youtube Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community Youtube Channels","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/youtube_channels.xml'
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                random.shuffle(data)#shuffle channel table
            except urllib2.URLError as e:
                return
                
            for i in range(limit):
                try:
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                    setting_1 = line[0]
                    channel_name = line[1]
                                        
                    if Youtube != False:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community Youtube Channels",channel_name)
                        channelNum += 1
                except:
                    pass
            
        #Youtube Playlists
        self.updateDialogProgress = 78
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Playlists") == "true":
            self.log("autoTune, Adding Community Youtube Playlists")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community Youtube Playlists","")
            url = 'https://pseudotv-live-community.googlecode.com/svn/youtube_playlists.xml'
            
            try: 
                f = urllib2.urlopen(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                random.shuffle(data)#shuffle channel table
            except urllib2.URLError as e:
                return
                
            for i in range(limit):
                try:
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                    setting_1 = line[0]
                    channel_name = line[1]
                                        
                    if Youtube != False:
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "2")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Random Community Youtube Playlists",channel_name)
                        channelNum += 1
                except:
                    pass

                    
        #InternetTV - Strms
        self.updateDialogProgress = 80
        if Globals.REAL_SETTINGS.getSetting("autoFindInternetSamples") == "true":
            self.log("autoTune, Adding InternetTV Strms")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Youtube & RSS Examples","")

            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "BBCWorldwide")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "BBC World News")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "11")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "http://revision3.com/hdnation/feed/Quicktime-High-Definition")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", str(limit))
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "HD Nation")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
            
            channelNum = channelNum + 2
            self.logDebug('channelNum = ' + str(channelNum))  
        
        
        # Extras - Bringthepopcorn
        self.updateDialogProgress = 83
        if Globals.REAL_SETTINGS.getSetting("autoFindPopcorn") == "true" and Donor_Downloaded == True:
            self.log("autoTune, Adding Bring The Popcorn Movies")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Bring The Popcorn Movies","")
            
            if Youtube != False:
            
                # AT_PopCat = ['action','adventure','animation','british','comedy','crime','disaster','documentary','drama','eastern','erotic','family','fan+film','fantasy','film+noir','foreign','history','holiday','horror','indie','kids','music','musical','mystery','neo-noir','road+movie','romance','science+fiction','short','sport','sports+film','suspense','thriller','tv+movie','war','western']
                # ATPopCat = AT_PopCat[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornGenre'))]
                   
                # AT_PopYear = ['2010-Now','2000-2010','1990-2000','1980-1990','1970-1980','1960-1970','1950-1960','1940-1950','1930-1940','1920-1930','1910-1920']
                # ATPopYear = AT_PopYear[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornYear'))]
                
                # AT_PopRes = ['480','720','1080']
                # ATPopRes = AT_PopRes[int(Globals.REAL_SETTINGS.getSetting('autoFindPopcornResoultion'))]    
                  
                # if Globals.REAL_SETTINGS.getSetting('autoFindPopcornPop') == "true":
                    # ATPopCat = 'pop|' + ATPopCat
                
                # add Bringthepopcorn user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "14")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "popcorn")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", 'autotune')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", '')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", '')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "BringThePopcorn")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum = channelNum + 1
                self.logDebug('channelNum = ' + str(channelNum))
           
        # Extras - Cinema Experience 
        if Globals.REAL_SETTINGS.getSetting("autoFindCinema") == "true" and Globals.REAL_SETTINGS.getSetting("CinemaPack") == "true" and Donor_Downloaded == True:
            self.log("autoTune, Adding Cinema Experience ")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Cinema Experience","")
            flename = chanlist.createCinemaExperiencePlaylist() #create playlist
            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "14")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "cinema")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", flename)
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", 'IMAX')
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", '')            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "5")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "PseudoCinema")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "8")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_id", "14")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_opt_1", "No")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_4_id", "17")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_4_opt_1", "No")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_5_id", "15")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_5_opt_1", "No")    
            
            channelNum = channelNum + 1
            self.logDebug('channelNum = ' + str(channelNum))

        # Plugin - F.T.V Favourites
        self.updateDialogProgress = 90
        if Globals.REAL_SETTINGS.getSetting("autoFindFilmonFavourites") == "true":
            self.log("autoTune, Adding F.T.V Favourites")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding F.T.V Favourites","")
            
            addonini = 'https://dl.dropboxusercontent.com/s/s6c4kqhvel3f721/addon.ini'
            url = 'https://docs.google.com/uc?export=download&id=0BxfXty1Ovu-ETE0xYVUtc2ZCLVU'
            url_bak = 'https://docs.google.com/uc?export=download&id=0BxfXty1Ovu-EeXZGRlRJcFVSWEE'
            FTV = chanlist.plugin_ok('plugin.video.F.T.V')
            
            if FTV == True:
                    
                try:
                    json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.F.T.V/?url=url&mode=415&name=Favourite+Channels"},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    
                    try: 
                        f = urllib2.urlopen(url)
                        self.log("ftvguide, INFO: URL Connected...")
                    except urllib2.URLError as e:
                        f = urllib2.urlopen(url_bak)
                        self.log("ftvguide, INFO: URL_BAK Connected...")
                    except urllib2.URLError as e:
                        pass

                    tree = ET.parse(f)
                    root = tree.getroot()
                    f.close()
                  
                    for f in file_detail:                    
                        inSet = False
                        file = re.search('"file" *: *"(.*?)"', f)
                        label = re.search('"label" *: *"(.*?)"', f)
                        if file and label:
                            file = file.group(1)
                            label = label.group(1)
                            CHname = ['W'+label[0:8], label[0:8]]
                            
                            for elem in root.getiterator():
                                if elem.tag == ("channel"):
                                    name = elem.findall('display-name')

                                    for i in name:
                                        print CHname
                                        print i.text
                                        if i.text in CHname:
                                            inSet = True
                                            CHzapit = elem.attrib
                                            CHzapit = str(CHzapit)
                                            CHzapit = CHzapit.split(": '", 1)[-1]
                                            CHzapit = CHzapit.split("'")[0]
                                            
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ftvguide")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", label + ' FTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                channelNum += 1
                            
                            if inSet == False:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", label + ' F.T.V')
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Unavailable")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", label + ' FTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                channelNum += 1
                                
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding F.T.V Favourites",label)
                except:
                    pass 
                                
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "15")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'plugin://plugin.video.F.T.V/Favourite Movies')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", '')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", '25')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", '1')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", 'F.T.V Movies')  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding F.T.V Favourites",'F.T.V Movies')
                channelNum = channelNum + 1
                self.logDebug('channelNum = ' + str(channelNum))
        
        # Playon
        if Globals.REAL_SETTINGS.getSetting("autoFindPlayonAmazon") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindPlayonHulu") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindPlayonNetflix") == "true":
            if PlayonPath != False:
                self.updateDialogProgress = 95
                self.log("Playon")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Playon","")
        
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonAmazon") == "true":
                    self.log("Playon - Amazon") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Playon","Amazon")

                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Amazon Instant Video/Prime Watchlist/TV Shows')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Amazon My TV")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Amazon Instant Video/Prime Watchlist/Movies')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Amazon My Movies")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonHulu") == "true":
                    self.log("Playon - Hulu") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Playon","Hulu")
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Hulu/Your Subscriptions')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Hulu My Subs")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Hulu/Popular/Popular Feature Films')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Hulu Popular Movies")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Hulu/Recently Added/Recently Added Feature Films')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Hulu Recent Movies")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonNetflix") == "true":
                    self.log("Playon - Netflix") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Playon","Netflix")
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Netflix/My List')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", 'Netflix My List')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1       
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Netflix/Recently Added')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", 'Netflix Recently Added')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1       
        
        Globals.ADDON_SETTINGS.writeSettings()

        #set max channels
        # chanlist.setMaxChannels()
        
        self.updateDialogProgress = 100
        # reset auto tune settings        
        Globals.REAL_SETTINGS.setSetting('Autotune', "false")
        Globals.REAL_SETTINGS.setSetting('Warning1', "false") 
        Globals.REAL_SETTINGS.setSetting("autoFindCustom","false")
        Globals.REAL_SETTINGS.setSetting("autoFindSuperFav","false") 
        Globals.REAL_SETTINGS.setSetting('autoFindLivePVR', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindLiveHD', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindUSTVNOW', "false")  
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosMusicTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLastFM","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")
        Globals.REAL_SETTINGS.setSetting("autoFindYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Plugins","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Playon","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Networks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_InternetTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_RSS","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Channels","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Playlists","false")
        Globals.REAL_SETTINGS.setSetting("autoFindInternetStrms","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPopcorn","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCinema","false")
        Globals.REAL_SETTINGS.setSetting("autoFindFilmonFavourites","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonAmazon","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonHulu","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonNetflix","false")
        Globals.REAL_SETTINGS.setSetting("ForceChannelReset","true")
        Globals.ADDON_SETTINGS.setSetting('LastExitTime', str(int(curtime)))
        self.updateDialog.close()

        
    def findMaxChannels(self):
        self.log('findMaxChannels')
        self.maxChannels = 0
        self.enteredChannelCount = 0

        for i in range(999):
            chtype = 9999
            chsetting1 = ''
            chsetting2 = ''
            chsetting3 = ''
            chsetting4 = ''

            try:
                chtype = int(Globals.ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chsetting1 = Globals.ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_1')
                chsetting2 = Globals.ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_2')
                chsetting3 = Globals.ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_3')
                chsetting4 = Globals.ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_4')
            except:
                pass

            if chtype == 0:
                if FileAccess.exists(xbmc.translatePath(chsetting1)):
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype <= 16:
                if len(chsetting1) > 0:
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
           
            if self.forceReset and (chtype != 9999):
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_changed', "True")
                
        return self.enteredChannelCount

    
    def initialAddChannels(self, thelist, chantype, currentchan):
        if len(thelist) > 0:
            counted = 0
            lastitem = 0
            curchancount = 1
            lowerlimit = 1
            lowlimitcnt = 0

            for item in thelist:
                if item[1] > lowerlimit:
                    if item[1] != lastitem:
                        if curchancount + counted <= 10 or counted == 0:
                            counted += curchancount
                            curchancount = 1
                            lastitem = item[1]
                        else:
                            break
                    else:
                        curchancount += 1

                    lowlimitcnt += 1

                    if lowlimitcnt == 3:
                        lowlimitcnt = 0
                        lowerlimit += 1
                else:
                    break

            if counted > 0:
                for item in thelist:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", str(chantype))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", item[0])
                    counted -= 1
                    currentchan += 1

                    if counted == 0:
                        break

        return currentchan
