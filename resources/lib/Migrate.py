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
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import subprocess, os, re, sys, time, datetime
import xbmcaddon, xbmc, xbmcgui, xbmcvfs
import Settings, Globals, ChannelList
import urllib, urllib2, httplib, random

from Globals import *
from xml.etree import ElementTree as ET
from FileAccess import FileAccess
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
        chanlist.forceReset = True
        RAND = True
        
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))   
        
        self.log("autoTune, autoFindCustom " + str(Globals.REAL_SETTINGS.getSetting("autoFindCustom")))
        self.log("autoTune, autoFindSuperFav " + str(Globals.REAL_SETTINGS.getSetting("autoFindSuperFav")))
        self.log("autoTune, autoFindLivePVR " + str(Globals.REAL_SETTINGS.getSetting("autoFindLivePVR")))
        self.log("autoTune, autoFindLiveHD " + str(Globals.REAL_SETTINGS.getSetting("autoFindLiveHD")))
        self.log("autoTune, autoFindUSTVNOW " + str(Globals.REAL_SETTINGS.getSetting("autoFindUSTVNOW")))
        self.log("autoTune, autoFindUSIPTV " + str(Globals.REAL_SETTINGS.getSetting("autoFindUSIPTV")))
        self.log("autoTune, autoFindSmoothStreams " + str(Globals.REAL_SETTINGS.getSetting("autoFindSmoothStreams")))
        self.log("autoTune, autoFindFilmonFavourites " + str(Globals.REAL_SETTINGS.getSetting("autoFindFilmonFavourites")))
        self.log("autoTune, autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoTune, autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        self.log("autoTune, autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoTune, autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        self.log("autoTune, autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        self.log("autoTune, autoFind3DMovies " + str(Globals.REAL_SETTINGS.getSetting("autoFind3DMovies")))
        self.log("autoTune, autoFindRecent " + str(Globals.REAL_SETTINGS.getSetting("autoFindRecent")))
        self.log("autoTune, autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        self.log("autoTune, autoFindMusicVideosMusicTV " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosMusicTV")))
        self.log("autoTune, autoFindMusicVideosLastFM " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFM")))
        self.log("autoTune, autoFindMusicVideosYoutube " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosYoutube")))
        self.log("autoTune, autoFindMusicVideosVevoTV " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV")))
        self.log("autoTune, autoFindMusicVideosLocal " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal")))
        self.log("autoTune, autoFindYoutube " + str(Globals.REAL_SETTINGS.getSetting("autoFindYoutube")))
        self.log("autoTune, autoFindPlayonAmazon " + str(Globals.REAL_SETTINGS.getSetting("autoFindPlayonAmazon")))
        self.log("autoTune, autoFindPlayonHulu " + str(Globals.REAL_SETTINGS.getSetting("autoFindPlayonHulu")))
        self.log("autoTune, autoFindPlayonNetflix " + str(Globals.REAL_SETTINGS.getSetting("autoFindPlayonNetflix")))
        self.log("autoTune, autoFindCommunity_Source " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Source")))
        self.log("autoTune, autoFindCommunity_Plugins " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Plugins")))
        self.log("autoTune, autoFindCommunity_InternetTV " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_InternetTV")))
        self.log("autoTune, autoFindCommunity_RSS " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_RSS")))
        self.log("autoTune, autoFindCommunity_Youtube_Networks " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Networks")))
        self.log("autoTune, autoFindCommunity_Youtube_Seasonal " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Seasonal")))
        self.log("autoTune, autoFindCommunity_Youtube_Channels " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Channels")))
        self.log("autoTune, autoFindCommunity_Youtube_Playlists " + str(Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Playlists")))
        self.log("autoTune, autoFindInternetSamples " + str(Globals.REAL_SETTINGS.getSetting("autoFindInternetSamples")))
        self.log("autoTune, autoFindPopcorn " + str(Globals.REAL_SETTINGS.getSetting("autoFindPopcorn")))
        self.log("autoTune, autoFindCinema " + str(Globals.REAL_SETTINGS.getSetting("autoFindCinema")))
        self.log("autoTune, autoFindIPTV_Source " + str(Globals.REAL_SETTINGS.getSetting("autoFindIPTV_Source")))
        self.log("autoTune, autoFindLive_Source " + str(Globals.REAL_SETTINGS.getSetting("autoFindLive_Source")))
        self.log("autoTune, autoFindNavix_Source " + str(Globals.REAL_SETTINGS.getSetting("autoFindNavix_Source")))

        #Reserve channel check            
        if Globals.REAL_SETTINGS.getSetting("reserveChannels") == "true":
            print 'Reserved for Autotune'
            channelNum = 501
        else:
            channelNum = 1
        
        self.log('autoTune, Starting channelNum = ' + str(channelNum))
               
        updateDialogProgress = 0
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Live", "Auto Tune")
        Youtube = chanlist.youtube_player()
        PlayonPath = chanlist.playon_player()
        
        limit = MEDIA_LIMIT[int(Globals.REAL_SETTINGS.getSetting('MEDIA_LIMIT'))]
        if limit == 0 or limit > 200:
            limit = 200
            RAND = False
        elif limit < 25:
            limit = 25
            
        # Custom Playlists
        self.updateDialogProgress = 1
        if Globals.REAL_SETTINGS.getSetting("autoFindCustom") == "true" :
            self.log("autoTune, adding Custom Channel")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Custom Channels"," ")
            CChan = 0
            
            for CChan in range(999):
                if xbmcvfs.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(CChan + 1) + '.xsp'):
                    self.log("autoTune, adding Custom Music Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/music/') + "Channel_" + str(CChan + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(CChan + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
                    channelNum += 1
                elif xbmcvfs.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(CChan + 1) + '.xsp'):
                    self.log("autoTune, adding Custom Mixed Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/mixed/') + "Channel_" + str(CChan + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(CChan + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
                    channelNum += 1
                elif xbmcvfs.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(CChan + 1) + '.xsp'):
                    self.log("autoTune, adding Custom Video Playlist Channel")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/video/') + "Channel_" + str(CChan + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Globals.uni(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(CChan + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
                    channelNum += 1


        # Custom SuperFavs
        self.updateDialogProgress = 5
        if Globals.REAL_SETTINGS.getSetting("autoFindSuperFav") == "true" :
            self.log("BuildSuperFav")
            SuperFav = chanlist.plugin_ok('plugin.program.super.favourites')
            SF = 0
            
            if SuperFav == True:
                plugin_details = chanlist.PluginQuery('plugin://plugin.program.super.favourites')
                filter =['create new super folder','explore favourites','explore  favourites','explore xbmc favourites','explore kodi favourites','isearch','search']
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Super Favourites"," ")

                try:
                    Match = True
                    while Match:
                    
                        for SF in (plugin_details):
                            filetypes = re.search('"filetype" *: *"(.*?)"', SF)
                            labels = re.search('"label" *: *"(.*?)"', SF)
                            files = re.search('"file" *: *"(.*?)"', SF)

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
                                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Super Favourites",SFname)  
                                        channelNum += 1
                except:
                    pass
                            
        # LiveTV - PVR
        self.updateDialogProgress = 10
        if Globals.REAL_SETTINGS.getSetting("autoFindLivePVR") == "true":
            self.log("autoTune, adding Live PVR Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding PVR Channels"," ")
            
            #PVR Path by XBMC Version, no json paths?
            XBMCver = chanlist.XBMCversion()
            if XBMCver == 'Gotham':
                PVRverPath = "pvr://channels/tv/All TV channels/"
            else:
                PVRverPath = "pvr://channels/tv/All channels/"
                
            if Globals.REAL_SETTINGS.getSetting("xmltvLOC"):
                xmltvLOC = xbmc.translatePath(Globals.REAL_SETTINGS.getSetting("xmltvLOC"))
                xmlTvFile = os.path.join(xmltvLOC, 'xmltv.xml')
                PVRnum = 0
                
                try:
                    json_query = '{"jsonrpc":"2.0","method":"PVR.GetChannels","params":{"channelgroupid":2}, "id":1}'
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    file_detail = str(file_detail)
                    CHnameLST = re.findall('"label" *: *(.*?),', file_detail)
                    CHidLST = re.findall('"channelid" *: *(.*?),', file_detail)
                    chanlist.cached_json_detailed_xmltvChannels = []
                        
                    for PVRnum in range(len(file_detail)):
                        CHname = CHnameLST[PVRnum]
                        CHname = str(CHname).replace('"','').replace("'",'')
                        inSet = False
                        
                        if xbmcvfs.exists(xmlTvFile): 
                            CHSetName, CHzapit = chanlist.findZap2itID(CHname, xmlTvFile)
                            
                            if CHzapit != '0':
                                inSet = True
                        
                        if inSet == True:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", PVRverPath + str(PVRnum) + ".pvr")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")                        
                        else:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", PVRverPath + str(PVRnum) + ".pvr")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                        
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding PVR Channels",CHname)  
                        channelNum += 1 
                except:
                    pass
        
        # LiveTV - HDHomeRun
        self.updateDialogProgress = 11
        if Globals.REAL_SETTINGS.getSetting("autoFindLiveHD") != "0" and Globals.REAL_SETTINGS.getSetting("xmltvLOC") and Globals.REAL_SETTINGS.getSetting('autoFindLiveHDPath'):
            xmltvLOC = xbmc.translatePath(Globals.REAL_SETTINGS.getSetting("xmltvLOC"))
            xmlTvFile = os.path.join(xmltvLOC, 'xmltv.xml')
            chanlist.cached_json_detailed_xmltvChannels = []
            HDstrmPath = Globals.REAL_SETTINGS.getSetting('autoFindLiveHDPath') + '/'
            HDSTRMnum = 0
            
            # LiveTV - HDHomeRun - STRM
            if Globals.REAL_SETTINGS.getSetting("autoFindLiveHD") == "1":
                self.log("autoTune, adding Live HDHomeRun Strm Channels")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding HDHomeRun STRM Channels"," ")
                
                try:                
                    LocalLST = str(xbmcvfs.listdir(HDstrmPath)[1]).replace("[","").replace("]","").replace("'","")
                    LocalLST = LocalLST.split(", ")
                    
                    for HDSTRMnum in range(len(LocalLST)):
                        if '.strm' in (LocalLST[HDSTRMnum]):
                            LocalFLE = (LocalLST[HDSTRMnum])
                            filename = (HDstrmPath + LocalFLE)
                            CHname = os.path.splitext(LocalFLE)[0]
                            inSet = False
                            
                            if xbmcvfs.exists(xmlTvFile): 
                                CHSetName, CHzapit = chanlist.findZap2itID(CHname, xmlTvFile)
                                
                                if CHzapit != '0':
                                    inSet = True

                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")                            
                            else:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", filename)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding HDHomeRun STRM Channels",CHname)
                            channelNum += 1
                except:
                    pass

            # LiveTV - HDHomeRun - UPNP
            elif Globals.REAL_SETTINGS.getSetting("autoFindLiveHD") == "2":
                self.log("autoTune, adding Live HDHomeRun UPNP Channels")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding HDHomeRun UPNP Channels"," ")
                HDHome_details = chanlist.PluginInfo(HDstrmPath)
                HDUPNPnum = 0
                
                try:
                    for HDUPNPnum in range(len(HDHome_details)):
                        HDHome = (HDHome_details[HDUPNPnum]).split(',')
                        filetype = HDHome[0]
                        CHname = HDHome[1]
                        file = HDHome[5]
                        inSet = False
                        
                        if xbmcvfs.exists(xmlTvFile): 
                            CHSetName, CHzapit = chanlist.findZap2itID(CHname, xmlTvFile)
                            
                            if CHzapit != '0':
                                inSet = True
                                
                        if inSet == True:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", unquote(file))
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "xmltv")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")                        
                        else:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", unquote(file))
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' LiveTV')  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding HDHomeRun UPNP Channels",CHname)  
                        channelNum += 1 
                except:
                    pass
             
        # LiveTV - USTVnow
        self.updateDialogProgress = 13
        if Globals.REAL_SETTINGS.getSetting("autoFindUSTVNOW") == "true":
            self.log("autoTune, adding USTVnow Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding USTVnow Channels"," ")
            USTVnum = 0
            USTVnow = chanlist.plugin_ok('plugin.video.ustvnow')
                
            if USTVnow == True:
                    
                try:
                    json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.ustvnow/live?mode=live","media":"video","properties":["thumbnail"]},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    chanlist.cached_json_detailed_xmltvChannels = []

                    for USTVnum in file_detail:      
                        files = re.search('"file" *: *"(.*?)"', USTVnum)
                        labels = re.search('"label" *: *"(.*?)"', USTVnum)
                        thumbnails = re.search('"thumbnail" *: *"(.*?)"', USTVnum)
                      
                        if files and labels:
                            file = files.group(1)
                            label = labels.group(1)
                            CHname = str(label.split(' -')[0])
                            inSet = False
                                    
                            if thumbnails != None and len(thumbnails.group(1)) > 0:
                                thumbnail = thumbnails.group(1)
                                chanlist.GrabLogo(thumbnail, CHname + ' USTVnow')
                                
                            if xbmcvfs.exists(USTVnowXML):  
                                CHSetName, CHzapit = chanlist.findZap2itID(CHname, USTVnowXML)
                                
                                if CHzapit != '0':
                                    inSet = True
                                        
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file) #Raw RTMP Link
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ustvnow")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")                           
                            else:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file) #Raw RTMP Link
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name="+CHname+"&mode=play")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USTVnow')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding USTVnow Channels",CHname)
                            channelNum += 1
                except:
                    pass
                    
                    
        # LiveTV - USIPTV
        self.updateDialogProgress = 14
        if Globals.REAL_SETTINGS.getSetting("autoFindUSIPTV") == "true":
            self.log("autoTune, adding USIPTV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding USIPTV Channels"," ")
            USIPTVnum = 0
            USIPTV = chanlist.plugin_ok('plugin.video.usiptv')
            
            if USIPTV == True: 
                try:
                    json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.usiptv","properties":["thumbnail"]},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    USIPTVXML = (xbmc.translatePath(os.path.join(XMLTV_CACHE_LOC, 'usiptv.xml')))
                    print file_detail
                    
                    for USIPTVnum in file_detail:      
                        files = re.search('"file" *: *"(.*?)"', USIPTVnum)
                        labels = re.search('"label" *: *"(.*?)"', USIPTVnum)
                        thumbnails = re.search('"thumbnail" *: *"(.*?)"', USIPTVnum)
                        
                        if files and labels:
                            file = files.group(1)
                            CHname = labels.group(1)
                            inSet = False
                                    
                            if thumbnails != None and len(thumbnails.group(1)) > 0:
                                thumbnail = thumbnails.group(1)
                                chanlist.GrabLogo(thumbnail, CHname + ' USIPTV')
                                
                            if xbmcvfs.exists(USIPTVXML):  
                                CHSetName, CHzapit = chanlist.findZap2itID(CHname, USIPTVXML)
                                
                                if CHzapit != '0':
                                    inSet = True
                                    
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(CHzapit))
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "usiptv")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USIPTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            else:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", 'Listing Unavailable')
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' USIPTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")

                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding USIPTV Channels",CHname)
                            channelNum += 1
                except:
                    pass
        
        # LiveTV - smoothstreams
        self.updateDialogProgress = 14
        if Globals.REAL_SETTINGS.getSetting("autoFindSmoothStreams") == "true":
            self.log("autoTune, adding SmoothStream Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding SmoothStream Channels"," ")
            SSTVnum = 0
            SSTV = chanlist.plugin_ok('plugin.video.mystreamstv.beta')
            
            if SSTV == True:
                try:
                    json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.mystreamstv.beta/?path=/root/channels","media":"video","properties":["thumbnail"]},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    SSTVXML = (xbmc.translatePath(os.path.join(XMLTV_CACHE_LOC, 'smoothstreams.xml')))
                        
                    for SSTVnum in file_detail:      
                        files = re.search('"file" *: *"(.*?)"', SSTVnum)
                        labels = re.search('"label" *: *"(.*?)"', SSTVnum)
                        thumbnails = re.search('"thumbnail" *: *"(.*?)"', SSTVnum)
                        
                        if files and labels:
                            file = files.group(1)
                            label = labels.group(1)
                            CHzapit = int(label.split(' - ')[0].replace('#',''))
                            CHname = label.split(' - ')[1]
                            CHnum = "%02d" % (CHzapit)
                            print CHzapit, CHname, CHnum
                            inSet = False
                                    
                            if thumbnails != None and len(thumbnails.group(1)) > 0:
                                thumbnail = thumbnails.group(1)
                                print thumbnail
                                chanlist.GrabLogo(thumbnail, CHname + ' SS')
                            
                            if xbmcvfs.exists(SSTVXML):
                                if CHzapit and CHzapit != 0:
                                    inSet = True
                                    
                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(CHzapit))
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.mystreamstv.beta/?path=/root/channels/&action=play_channel&chan="+CHnum)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "smoothstreams")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", CHname)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' SS')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            else:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.mystreamstv.beta/?path=/root/channels/&action=play_channel&chan="+CHnum)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", 'Listing Unavailable')
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", CHname + ' SS')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")

                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding SmoothStream Channels",CHname)
                            channelNum += 1
                except:
                    pass
           
           
        # Plugin - F.T.V Favourites
        self.updateDialogProgress = 90
        if Globals.REAL_SETTINGS.getSetting("autoFindFilmonFavourites") == "true":
            self.log("autoTune, adding F.T.V Favourite Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding F.T.V Favourite Channels"," ")
            addonini = 'https://dl.dropboxusercontent.com/s/s6c4kqhvel3f721/addon.ini'
            FTVnum = 0
            FTV = chanlist.plugin_ok('plugin.video.F.T.V')
            
            if FTV == True:
                try:
                    json_query = ('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"plugin://plugin.video.F.T.V/?url=url&mode=415&name=Favourite+Channels&ch_fanart=","media":"video","properties":["thumbnail"]},"id":1}')
                    json_folder_detail = chanlist.sendJSON(json_query)
                    file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
                    FTVXML = (xbmc.translatePath(os.path.join(XMLTV_CACHE_LOC, 'ftvguide.xml')))
                    chanlist.cached_json_detailed_xmltvChannels = []

                    for FTVnum in file_detail:   
                        files = re.search('"file" *: *"(.*?)"', FTVnum)
                        labels = re.search('"label" *: *"(.*?)"', FTVnum)
                        thumbnails = re.search('"thumbnail" *: *"(.*?)"', FTVnum)
                        
                        if files and labels:
                            file = files.group(1)
                            label = labels.group(1)
                            inSet = False
                                        
                            if thumbnails != None and len(thumbnails.group(1)) > 0:
                                thumbnail = thumbnails.group(1)
                                print thumbnail
                                chanlist.GrabLogo(thumbnail, label + ' FTV')
                                
                            if xbmcvfs.exists(FTVXML):                                        
                                CHSetName, CHzapit = chanlist.findZap2itID(label, FTVXML)
                                                        
                                if CHzapit != 0:
                                    inSet = True

                            if inSet == True:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", CHzapit)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ftvguide")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", label + ' FTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "24")  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")                                
                            else:
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", file)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", label)
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "TV Listing Unavailable, Check your xmltv file")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", label + ' FTV')  
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding F.T.V Favourites",label)
                            channelNum += 1                
                except:
                    pass    

                    
        #TV - Networks/Genres
        self.updateDialogProgress = 20
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("autoTune, Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for TV Channels"," ")
            chanlist.fillTVInfo()

        # need to add check for auto find network channels
        self.updateDialogProgress = 21
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("autoTune, adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding TV Networks"," ")

            for i in range(len(chanlist.networkList)):
                # channelNum = self.initialAddChannels(chanlist.networkList, 1, channelNum)
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1",Globals.uni(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding TV Network",Globals.uni(chanlist.networkList[i]))
                channelNum += 1
        
        self.updateDialogProgress = 22
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("autoTune, adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding TV Genres","")

            # channelNum = self.initialAddChannels(chanlist.showGenreList, 3, channelNum)
            for i in range(len(chanlist.showGenreList)):
                # add network presets
                if chanlist.showGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.showGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding TV Genres",Globals.uni(chanlist.showGenreList[i]) + " TV")
                    channelNum += 1
        
        self.updateDialogProgress = 23
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        self.updateDialogProgress = 24
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("autoTune, adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Movie Studios"," ")

            for i in range(len(chanlist.studioList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Movie Studios",Globals.uni(chanlist.studioList[i]))
                channelNum += 1
                
        self.updateDialogProgress = 25
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("autoTune, adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Movie Genres"," ")

            # channelNum = self.initialAddChannels(chanlist.movieGenreList, 4, channelNum)
            for i in range(len(chanlist.movieGenreList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                if chanlist.movieGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.movieGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Movie Genres","Found " + Globals.uni(chanlist.movieGenreList[i]) + " Movies")
                    channelNum += 1
                
        self.updateDialogProgress = 26
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Mixed Channels"," ")
            chanlist.fillMixedGenreInfo()
        
        self.updateDialogProgress = 27
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("autoTune, adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Mixed Genres","")

            for i in range(len(chanlist.mixedGenreList)):
                # add network presets
                if chanlist.mixedGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.mixedGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Mixed Genres",Globals.uni(chanlist.mixedGenreList[i]) + " Mix")
                    channelNum += 1
        
        
        #recent movie/tv
        self.updateDialogProgress = 28  
        if Globals.REAL_SETTINGS.getSetting("autoFindRecent") == "true":
            self.log("autoTune, adding Recent TV/Movies")
            
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recent TV"," ")
            TVflename = chanlist.createRecentlyAddedTV()
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", TVflename)
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "3")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Recent TV")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "12")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_id", "13")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_opt_1", "4")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
            channelNum += 1
            
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recent Movies"," ")
            Movieflename = chanlist.createRecentlyAddedMovies()     
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Movieflename)
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Recent Movies")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
            channelNum += 1
            
        self.updateDialogProgress = 40
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Music Channels"," ")
            chanlist.fillMusicInfo()

        
        #Music Genre
        self.updateDialogProgress = 50
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.log("autoTune, adding Music Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Music Genres"," ")

            for i in range(len(chanlist.musicGenreList)):
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.musicGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Music Genres",Globals.uni(chanlist.musicGenreList[i]) + " Music")
                channelNum += 1
        
        
        #Music Videos - My Music
        self.updateDialogProgress = 53
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosMusicTV") == "true":
            self.log("autoTune, adding My MusicTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding My MusicTV Music Videos"," ")
               
            MusicTV = False
            MusicTV = chanlist.plugin_ok('plugin.video.my_music_tv')
            
            if MusicTV == True:
                for i in range(999):
                    path = xbmc.translatePath("special://profile/addon_data/plugin.video.my_music_tv/cache/plist")
                    fle = os.path.join(path,"Channel_" + str(i) + ".xml.plist")
                    
                    if xbmcvfs.exists(xbmc.translatePath(fle)):
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
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding My MusicTV Music Videos","Channel " + str(i))
                        channelNum += 1
 
        
        #Music Videos - Last.fm user
        self.updateDialogProgress = 53
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFM") == "true":
            self.log("autoTune, adding Last.FM Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Last.FM Music Videos"," ")
               
            if Youtube != False:
                user = Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFMuser")
                
                # add Last.fm user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", user)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "3")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Last.FM")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "18")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "No")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_id", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_3_opt_1", "24")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Last.FM Music Videos","User " + user)
                channelNum += 1

        
        #Music Videos - Youtube
        self.updateDialogProgress = 55
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosYoutube") == "true":
            self.log("autoTune, adding Youtube Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Music Videos"," ")

            if Youtube != False:

                # add HungaryRChart presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "HungaryRChart")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "HRChart")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                # add BillbostdHot100 presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "BillbostdHot100")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "BillbostdHot100")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                # add TheTesteeTop50Charts presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "TheTesteeTop50Charts")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "TheTesteeTop50Charts")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                self.logDebug('channelNum = ' + str(channelNum))
            
            
        #Music Videos - VevoTV
        self.updateDialogProgress = 58
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV") == "true":
            self.log("autoTune, adding VevoTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding VevoTV Music Videos"," ")
            
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
                channelNum += 1
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.vevo_tv/?url=TIVEVSTRUS01&mode=playOfficial")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "VEVO TV (US: Flow)")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "VevoTV - Flow")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                self.logDebug('channelNum = ' + str(channelNum))
            
            
        #Music Videos - Local
        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal") != "":
            self.log("autoTune, adding Local Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Local Music Videos"," ")
            LocalVideo = str(Globals.REAL_SETTINGS.getSetting('autoFindMusicVideosLocal'))
            
            # add Local presets
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +LocalVideo+ "")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Music Videos")  
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")         
            channelNum += 1
            self.logDebug('channelNum = ' + str(channelNum))
        
        
        #Plugin - Youtube
        self.updateDialogProgress = 63
        if Globals.REAL_SETTINGS.getSetting("autoFindYoutube") == "true":
            self.log("autoTune, adding Youtube Favourites & Subscriptions")
            Username = Globals.REAL_SETTINGS.getSetting("autoFindYoutubeUser")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Favourites & Subscriptions","User " + Username)
            
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
                channelNum += 1
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Username)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "4")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(limit))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", Username + "Favourites")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                self.logDebug('channelNum = ' + str(channelNum))
        
        
        # Playon
        if Globals.REAL_SETTINGS.getSetting("autoFindPlayonAmazon") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindPlayonHulu") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindPlayonNetflix") == "true":
            if PlayonPath != False:
                self.updateDialogProgress = 95
                self.log("Playon")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Playon"," ")
        
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonAmazon") == "true":
                    self.log("Playon - Amazon") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Playon","Amazon")

                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Amazon Instant Video/Prime Watchlist/TV Shows')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Amazon MyTV")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
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
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Amazon MyMovies")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonHulu") == "true":
                    self.log("Playon - Hulu") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Playon","Hulu")
                    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", 'Hulu/Your Subscriptions')
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "25")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Hulu MySubs")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
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
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
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
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
                    
                if Globals.REAL_SETTINGS.getSetting("autoFindPlayonNetflix") == "true":
                    self.log("Playon - Netflix") 
                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Playon","Netflix")
                    
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
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
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
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1       

                    
        #Recommend lists#
        if int(REAL_SETTINGS.getSetting('autoFindCommunity_Source')) == 1: 
            Community = False
        else:
            Community = True
        
        genre_filter = []
        
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
        if Globals.REAL_SETTINGS.getSetting("CN_Music") == "true":
            genre_filter.append('Music') 
        if Globals.REAL_SETTINGS.getSetting("CN_Other") == "true":
            genre_filter.append('Other') 
        
        genre_filter = ([x.lower() for x in genre_filter if x != ''])
        print 'genre_filter', genre_filter
            
        #Plugin
        self.updateDialogProgress = 70
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Plugins") == "true":
            self.log("autoTune, adding Recommend Plugins")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recommend Plugins"," ")
            
            if Community:
                url = 'https://pseudotv-live-community.googlecode.com/svn/addons.xml'
            else:
                url = BASEURL + 'addons.ini'
                
            channelNum = self.RecTune(url, genre_filter, channelNum, limit, RAND)
           
        #Playon
        self.updateDialogProgress = 71
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Playon") == "true":
            self.log("autoTune, adding Recommend Playon")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recommend Playon"," ")
            
            if Community:
                url = 'https://pseudotv-live-community.googlecode.com/svn/playon.xml'
            else:
                url = BASEURL + 'playon.ini'
            
            channelNum = self.RecTune(url, genre_filter, channelNum, limit, RAND)
            
        #InternetTV
        self.updateDialogProgress = 72
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_InternetTV") == "true":
            self.log("autoTune, adding Recommend InternetTV")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recommend InternetTV"," ")
           
            if Community:
                url = 'https://pseudotv-live-community.googlecode.com/svn/internettv.xml'
            else:
                url = BASEURL + 'internettv.ini'
            
            channelNum = self.RecTune(url, genre_filter, channelNum, limit, True)
        
        # RSS
        self.updateDialogProgress = 73
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_RSS") == "true":
            self.log("autoTune, adding Recommend RSS")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recommend RSS"," ")
            url = 'https://pseudotv-live-community.googlecode.com/svn/rss.xml'
            fileNum = 0
            
            try: 
                f = Open_URL(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                
                if RAND == True:
                    random.shuffle(data)#shuffle
            except:
                return
            
            try:
                for i in range(limit):
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                    
                    #If List Formatting is bad return
                    if len(line) == 2:
                        setting_1 = line[0]
                        channel_name = (line[1]).replace('\n','').replace('\r','')
                
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
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Randomly Recommend RSS",channel_name)
                        channelNum += 1
                        fileNum += 1
                        
                        if fileNum >= limit:
                            break
                    else:
                        print line
                        print "!!!!COMMUNITY LIST RSS FORMATING ERROR!!!!"
                        pass
            except:
                pass
            
            
        #Youtube Network
        #todo switch format to multi youtube type
        self.updateDialogProgress = 74
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Networks") == "true":
            self.log("autoTune, adding Youtube Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Networks"," ")    
            Channel_List = 'https://pseudotv-live-community.googlecode.com/svn/youtube_channels_networks.xml'
            Playlist_List = 'https://pseudotv-live-community.googlecode.com/svn/youtube_playlists_networks.xml'
            fileNum = 0
            
            try:
                f = Open_URL(Channel_List)
                linesLST = f.readlines()
                linesLST = linesLST[2:]#remove first two lines
                f.close
            except:
                return
            
            for i in range(len(linesLST)):
                line = str(linesLST[i]).replace("\n","").replace('""',"")
                line = line.split("|")
            
                #If List Formatting is bad return
                if len(line) == 7:  
                    genre = line[0]
                    chtype = line[1]
                    setting_1 = (line[2]).replace(",","|")
                    setting_2 = line[3]
                    setting_3 = line[4]
                    setting_4 = line[5]
                    channel_name = line[6]
                    CHname = channel_name
                    
                    if Youtube != False:
                        if genre.lower() in genre_filter:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "8")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Networks",channel_name)
                            channelNum += 1
                            fileNum += 1
                            
                            if fileNum >= limit:
                                break
                else:   
                    print line
                    print "!!!!COMMUNITY LIST Youtube Network FORMATING ERROR!!!!"
                            
            try:
                f = Open_URL(Playlist_List)
                linesLST = f.readlines()
                linesLST = linesLST[2:]#remove first two lines
                f.close
            except:
                return
            fileNum = 0
            
            for i in range(len(linesLST)):
                line = str(linesLST[i]).replace("\n","").replace('""',"")
                line = line.split("|")
            
                #If List Formatting is bad return
                if len(line) == 7:  
                    genre = line[0]
                    chtype = line[1]
                    setting_1 = (line[2]).replace(",","|")
                    setting_2 = line[3]
                    setting_3 = line[4]
                    setting_4 = line[5]
                    channel_name = line[6]
                    CHname = channel_name
                    
                    if Youtube != False:
                        if genre.lower() in genre_filter:
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "7")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name)  
                            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Networks",channel_name)
                            channelNum += 1                            
                            fileNum += 1
                            
                            if fileNum >= limit:
                                break
                else:   
                    print line
                    print "!!!!COMMUNITY LIST Youtube Network FORMATING ERROR!!!!"

                    
        #Youtube Network - Seasonal
        self.updateDialogProgress = 74
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Seasonal") == "true":
           if Youtube != False:
                today = datetime.datetime.now()
                month = today.strftime('%B')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", month)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "31")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Seasonal Channel")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "168")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Youtube Networks","Seasonal Channel")
                channelNum += 1 
                
                          
        #Youtube Channels
        self.updateDialogProgress = 75    
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Channels") == "true":
            self.log("autoTune, adding Recommend Youtube Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Random Recommend Youtube Channels"," ")
            url = 'https://pseudotv-live-community.googlecode.com/svn/youtube_channels.xml'
            
            try: 
                f = Open_URL(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                if RAND == True:
                    random.shuffle(data)#shuffle channel table
            except:
                return
                
            for i in range(limit):
                try:
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                    
                    #If List Formatting is bad return
                    if len(line) != 2:
                        print "!!!!COMMUNITY LIST Youtube FORMATING ERROR!!!!"
                        pass
                    
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
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Random Recommend Youtube Channels",channel_name)
                        channelNum += 1
                except:
                    pass
            
            
        #Youtube Playlists
        self.updateDialogProgress = 76
        if Globals.REAL_SETTINGS.getSetting("autoFindCommunity_Youtube_Playlists") == "true":
            self.log("autoTune, adding Recommend Youtube Playlists")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Random Recommend Youtube Playlists"," ")
            url = 'https://pseudotv-live-community.googlecode.com/svn/youtube_playlists.xml'
            
            try: 
                f = Open_URL(url)
                data = f.readlines()
                f.close()
                data = data[2:] #remove first two unwanted lines
                if RAND == True:
                    random.shuffle(data)#shuffle channel table
            except:
                return
                
            for i in range(limit):
                try:
                    line = str(data[i]).replace("\n","").replace('""',"")
                    line = line.split(",")
                                   
                    #If List Formatting is bad return
                    if len(line) != 2:
                        print "!!!!COMMUNITY LIST Youtube Playlists FORMATING ERROR!!!!"
                        pass
                        
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
                        self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Random Recommend Youtube Playlists",channel_name)
                        channelNum += 1
                except:
                    pass

        # Extras - Bringthepopcorn
        self.updateDialogProgress = 81
        if Globals.REAL_SETTINGS.getSetting("autoFindPopcorn") == "true" and Donor_Downloaded == True:
            self.log("autoTune, adding Bring The Popcorn Movies")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Bring The Popcorn Movies"," ")
            
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
                channelNum += 1
                self.logDebug('channelNum = ' + str(channelNum))
           
           
        # Extras - Cinema Experience 
        self.updateDialogProgress = 82
        if Globals.REAL_SETTINGS.getSetting("autoFindCinema") == "true" and Donor_Downloaded == True:
            self.log("autoTune, adding Cinema Experience ")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Cinema Experience"," ")
            flename = chanlist.createCinemaExperiencePlaylist() #create playlist
            THEME_NAMES = ['Default','IMAX']
            THEME = THEME_NAMES[int(Globals.REAL_SETTINGS.getSetting('autoFindCinema_Theme'))]
            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "14")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "cinema")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", flename)
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", THEME)
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
            channelNum += 1
            self.logDebug('channelNum = ' + str(channelNum))
  
  
        # Extras - IPTV
        self.updateDialogProgress = 83
        if Globals.REAL_SETTINGS.getSetting("autoFindIPTV_Source") != "0" and Donor_Downloaded == True:
            self.log("autoTune, adding IPTV Channels")
            self.updateDialog.update(self.updateDialogProgress,"adding IPTV Channels","This could take a few minutes","Please Wait...")
            # IPTVurl = 'http://xty.me/vdubt25'
            # IPTVxml = 'http://is.gd/vguide2'
            IPTVnum = 0
            
            if Globals.REAL_SETTINGS.getSetting("autoFindIPTV_Source") == "1":
                IPTVurl = Globals.REAL_SETTINGS.getSetting('autoFindIPTV_Path_Local')
            else:
                IPTVurl = Globals.REAL_SETTINGS.getSetting('autoFindIPTV_Path_Online')
            
            IPTVlst = chanlist.IPTVtuning(IPTVurl)
            IPTVname = IPTVurl.replace('//','/')
            
            for IPTVnum in range(len(IPTVlst)):
                if channelNum == 999:
                    return
            
                IPTV = IPTVlst[IPTVnum]
                title = IPTV[0]
                link = IPTV[1]
                Pluginvalid = chanlist.Valid_ok(link)
                
                if Pluginvalid != False:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", link)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", title)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "IPTV - " + IPTVname)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", title)  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
        
        
        # Extras - LiveStream
        self.updateDialogProgress = 83
        if Globals.REAL_SETTINGS.getSetting("autoFindLive_Source") != "0" and Donor_Downloaded == True:
            self.log("autoTune, adding LiveStream Channels")
            self.updateDialog.update(self.updateDialogProgress,"adding LiveStream Channels","This could take a few minutes","Please Wait...")
            LSTVnum = 0
                        
            if Globals.REAL_SETTINGS.getSetting("autoFindLive_Source") == "1":
                LSTVurl = Globals.REAL_SETTINGS.getSetting('autoFindLive_Path_Local')
            else:
                LSTVurl = Globals.REAL_SETTINGS.getSetting('autoFindLive_Path_Online')
            
            LSTVlst = chanlist.LSTVtuning(LSTVurl)
            LSTVname = LSTVurl.replace('//','/')
            
            for LSTVnum in range(len(LSTVlst)):
                if channelNum == 999:
                    return
            
                LSTV = LSTVlst[LSTVnum]
                title = LSTV[0]
                link = LSTV[1]
                Pluginvalid = chanlist.Valid_ok(link)
                
                if Pluginvalid != False:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", link)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", title)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "LiveStream - " + LSTVname)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", title)  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    channelNum += 1
        
        
        # Extras - Navi-X
        self.updateDialogProgress = 83
        if Globals.REAL_SETTINGS.getSetting("autoFindNavix_Source") != "0" and Donor_Downloaded == True:
            self.log("autoTune, adding Navi-X Channels")
            self.updateDialog.update(self.updateDialogProgress,"adding Navi-X Channels","This could take a few minutes","Please Wait...")
            NaviXnum = 0
                        
            if Globals.REAL_SETTINGS.getSetting("autoFindNavix_Source") == "1":
                NaviXurl = Globals.REAL_SETTINGS.getSetting('autoFindNavix_Path_Local')
            else:
                NaviXurl = Globals.REAL_SETTINGS.getSetting('autoFindNavix_Path_Online')
            
            NaviXlst = chanlist.NaviXtuning(NaviXurl)
            NaviXname = NaviXurl.replace('//','/')
            
            for NaviXnum in range(len(NaviXlst)):
                if channelNum == 999:
                    return
            
                NaviX = NaviXlst[NaviXnum]
                title = NaviX[0]
                link = NaviX[1]
                Pluginvalid = chanlist.Valid_ok(link)
                
                if Pluginvalid != False:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", link)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", title)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Navi-X - " + NaviXname)
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", title)  
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
        Globals.REAL_SETTINGS.setSetting('autoFindLiveHD', "0")
        Globals.REAL_SETTINGS.setSetting('autoFindUSTVNOW', "false")  
        Globals.REAL_SETTINGS.setSetting('autoFindUSIPTV', "false") 
        Globals.REAL_SETTINGS.setSetting('autoFindSmoothStreams', "false")  
        Globals.REAL_SETTINGS.setSetting("autoFindFilmonFavourites","false")
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFind3DMovies","false")    
        Globals.REAL_SETTINGS.setSetting("autoFindRecent","false")      
        Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosMusicTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLastFM","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")
        Globals.REAL_SETTINGS.setSetting("autoFindYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonAmazon","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonHulu","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPlayonNetflix","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Plugins","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Playon","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Networks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Seasonal","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_InternetTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_RSS","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Channels","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Playlists","false")
        Globals.REAL_SETTINGS.setSetting("autoFindPopcorn","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCinema","false")
        Globals.REAL_SETTINGS.setSetting("autoFindIPTV_Source","0")    
        Globals.REAL_SETTINGS.setSetting("autoFindLive_Source","0")    
        Globals.REAL_SETTINGS.setSetting("autoFindNavix_Source","0")    
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

        
    def RecTune(self, url, genre_filter, channelNum, limit=200, RAND=False):
        self.log('RecTune, URL = ' + url + ', Limit = ' + str(limit) + ', Random = ' + str(RAND))
        chanlist = ChannelList.ChannelList()
        duplicate = []
        fileNum = 0
        
        try:
            data = Open_URL_UP(url, USERPASS)
            data = data[2:] #remove first two unwanted lines
            data = ([x for x in data if x != '']) #remove empty lines      
            i = 0
            
            if RAND == True:
                random.shuffle(data)

            for i in range(len(data)):
                line = str(data[i]).replace("\n","").replace('""',"")
                line = line.split("|")

                if len(line) == 7:
                    if str(line).startswith(';'):
                        print 'line commented out'
                    else:
                        genre = line[0]
                        chtype = line[1]
                        setting_1 = line[2]
                        setting_2 = line[3]
                        setting_3 = line[4]
                        setting_4 = line[5]
                        channel_name = line[6]
                        CHname = ((channel_name.lower()).replace(' hd','').replace('hd',''))
                        
                        if genre.lower() in genre_filter:
                            if CHname not in duplicate:
                            
                                if chtype == '15':
                                    STRMtype = 'PluginTV'
                                    Pluginvalid = chanlist.plugin_ok(setting_1)
                                elif chtype == '16':
                                    STRMtype = 'PlayonTV'
                                    Pluginvalid = chanlist.playon_player()
                                elif chtype == '9':
                                    STRMtype = 'InternetTV'
                                    if setting_2[0:6] == 'plugin':
                                        #Call Plugin_ok directly to avoid Valid_ok Override.
                                        Pluginvalid = chanlist.plugin_ok(setting_2)
                                    else:
                                        Pluginvalid = chanlist.Valid_ok(setting_2)
                                    
                                if Pluginvalid != False:
                                    duplicate.append(CHname)
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", chtype)
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", setting_1)
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", setting_2)
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", setting_3)
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", setting_4)
                                    
                                    if STRMtype == 'PlayonTV':
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "2")
                                    else:
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                                        
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", channel_name.title()) 

                                    if STRMtype == 'PlayonTV':                                
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_id", "13")
                                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_2_opt_1", "4")  
                                        
                                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                                    self.updateDialog.update(self.updateDialogProgress,"Auto Tune","adding Recommend " + STRMtype, channel_name.title())
                                    channelNum += 1
                                    fileNum += 1
                else:
                    if line != '':
                        print line
                        print "!!!!Recommended LIST FORMATING ERROR!!!!"
                  
                if fileNum >= limit:
                    break
        except:
            pass
            
        return channelNum