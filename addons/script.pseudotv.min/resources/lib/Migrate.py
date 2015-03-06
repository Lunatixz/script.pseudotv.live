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
    
class Migrate:
    def log(self, msg, level = xbmc.LOGNOTICE):
        logGlob('Migrate: ' + msg, level)
    
    def logDebug(self, msg):
        logGlob('Migrate: ' + msg)
    
    def logError(self, msg):
        logGlob('Migrate: ' + msg, xbmc.LOGERROR)
            
    
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
        
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
        self.log("autoTune, autoFindRecent " + str(Globals.REAL_SETTINGS.getSetting("autoFindRecent")))
        self.log("autoTune, autoFindCustom " + str(Globals.REAL_SETTINGS.getSetting("autoFindCustom")))
        self.log("autoTune, autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoTune, autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        self.log("autoTune, autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoTune, autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        self.log("autoTune, autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        self.log("autoTune, autoFind3DMovies " + str(Globals.REAL_SETTINGS.getSetting("autoFind3DMovies")))
        #self.log("autoTune, autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        #self.log("autoTune, autoFindMusicVideosLocal " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal")))

        #Reserve channel check            
        if Globals.REAL_SETTINGS.getSetting("reserveChannels") == "true":
            print 'Reserved for Autotune'
            channelNum = 501
        else:
            channelNum = 1
        
        self.log('autoTune, Starting channelNum = ' + str(channelNum))
               
        updateDialogProgress = 0
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Min", "Auto Tune")
        #Youtube = chanlist.youtube_player()
        #PlayonPath = chanlist.playon_player()
        
        self.limit = MEDIA_LIMIT[int(Globals.REAL_SETTINGS.getSetting('MediaLimit'))]
        if REAL_SETTINGS.getSetting('MediaLimitWarning') == 'false':
            self.limit = 50
        
        if self.limit == 0 or self.limit > 200:
            self.limit = 200
        elif self.limit < 11:
            self.limit = 11
            
        CChan = 0
        
        #TV/Movies - Recent - find/add
        self.updateDialogProgress = 1
        if Globals.REAL_SETTINGS.getSetting("autoFindRecent") == "true":
            self.log("autoTune, adding Recent TV/Movies")
            
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Recent TV"," ")
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
            
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Recent Movies"," ")
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
            
        # Custom Playlists
        self.updateDialogProgress = 20
        if Globals.REAL_SETTINGS.getSetting("autoFindCustom") == "true" :
            self.log("autoTune, adding Custom Channel")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Custom Channels"," ")
            
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
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Min","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
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
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Min","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
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
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Min","Found " + Globals.uni(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(CChan + 1) + '.xsp')),"")
                    channelNum += 1
        
        
        #TV - Networks/Genres - find
        self.updateDialogProgress = 40
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("autoTune, Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","Searching for TV Channels"," ")
            chanlist.fillTVInfo()

        # TV - Networks - add
        # need to add check for auto find network channels
        self.updateDialogProgress = 50
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("autoTune, adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding TV Networks"," ")

            for i in range(len(chanlist.networkList)):
                # channelNum = self.initialAddChannels(chanlist.networkList, 1, channelNum)
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1",Globals.uni(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding TV Network",Globals.uni(chanlist.networkList[i]))
                channelNum += 1
        
        # TV - Genres - add
        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("autoTune, adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding TV Genres","")

            # channelNum = self.initialAddChannels(chanlist.showGenreList, 3, channelNum)
            for i in range(len(chanlist.showGenreList)):
                # add network presets
                if chanlist.showGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.showGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding TV Genres",Globals.uni(chanlist.showGenreList[i]) + " TV")
                    channelNum += 1
        
        # Movie - Studios/Genres - find
        self.updateDialogProgress = 70
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        # Movie - Studios - add
        self.updateDialogProgress = 80
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("autoTune, adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Movie Studios"," ")

            for i in range(len(chanlist.studioList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Movie Studios",Globals.uni(chanlist.studioList[i]))
                channelNum += 1
        
        # Movie - Genres - add
        self.updateDialogProgress = 85
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("autoTune, adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Movie Genres"," ")

            # channelNum = self.initialAddChannels(chanlist.movieGenreList, 4, channelNum)
            for i in range(len(chanlist.movieGenreList)):
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                if chanlist.movieGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.movieGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Movie Genres","Found " + Globals.uni(chanlist.movieGenreList[i]) + " Movies")
                    channelNum += 1
        
        # TV/Movie - Genres - find
        self.updateDialogProgress = 90
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","Searching for Mixed Channels"," ")
            chanlist.fillMixedGenreInfo()
        
        # TV/Movie - Genres - add
        self.updateDialogProgress = 95
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("autoTune, adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Mixed Genres","")

            for i in range(len(chanlist.mixedGenreList)):
                # add network presets
                if chanlist.mixedGenreList[i] != '':
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", Globals.uni(chanlist.mixedGenreList[i]))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"AutoTuning","adding Mixed Genres",Globals.uni(chanlist.mixedGenreList[i]) + " Mix")
                    channelNum += 1
        
        
        #Recommend lists#
        CommunityList = False
        
        self.genre_filter = []
        if Globals.REAL_SETTINGS.getSetting("CN_TV") == "true":
            self.genre_filter.append('TV') 
        if Globals.REAL_SETTINGS.getSetting("CN_Movies") == "true":
            self.genre_filter.append('Movies') 
        if Globals.REAL_SETTINGS.getSetting("CN_Episodes") == "true":
            self.genre_filter.append('Episodes') 
        '''if Globals.REAL_SETTINGS.getSetting("CN_Sports") == "true":
            self.genre_filter.append('Sports') 
        if Globals.REAL_SETTINGS.getSetting("CN_News") == "true":
            self.genre_filter.append('News') 
        if Globals.REAL_SETTINGS.getSetting("CN_Kids") == "true":
            self.genre_filter.append('Kids') 
        if Globals.REAL_SETTINGS.getSetting("CN_Music") == "true":
            self.genre_filter.append('Music') 
        if Globals.REAL_SETTINGS.getSetting("CN_Other") == "true":
            self.genre_filter.append('Other')'''
        
        self.genre_filter = ([x.lower() for x in self.genre_filter if x != ''])
        print 'genre_filter', self.genre_filter
        
        
        Globals.ADDON_SETTINGS.writeSettings()

        #set max channels
        # chanlist.setMaxChannels()
        
        self.updateDialogProgress = 100
        # reset auto tune settings
        Globals.REAL_SETTINGS.setSetting('Autotune', "false")
        Globals.REAL_SETTINGS.setSetting('Warning1', "false")
        Globals.REAL_SETTINGS.setSetting("autoFindCustom","false")
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","true")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","true")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","true")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","true")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","true")
        Globals.REAL_SETTINGS.setSetting("autoFind3DMovies","false")
        Globals.REAL_SETTINGS.setSetting("autoFindRecent","true")
        #Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        #Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")  
        Globals.REAL_SETTINGS.setSetting("ForceChannelReset","true")
        Globals.ADDON_SETTINGS.setSetting('LastExitTime', str(int(curtime)))
        self.updateDialog.close()

        
    def tuneList(self, channelNum, chtype, NameLst, Option1LST, Option2LST, Option3LST, Option4LST):
        self.log('tuneList')
        print channelNum, chtype, NameLst, Option1LST, Option2LST, Option3LST, Option4LST
        filecount = 0
        chanlist = ChannelList.ChannelList()
        for i in range(len(NameLst)):
            found = True
            try:
                title = chanlist.CleanLabels(NameLst[i])
                try:
                    title, genre = title.split(' - ')
                    print title, genre
                    if genre.lower() not in self.genre_filter:
                        found = False
                except:
                    pass
                
                if not found:
                    raise
                
                self.updateDialog.update(self.updateDialogProgress,"AutoTuning","",NameLst[i])
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", str(chtype))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(Option1LST[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", str(Option2LST[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", str(Option3LST[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", str(Option4LST[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", title)
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                channelNum += 1
                filecount += 1
            except:
                pass
            if filecount >= self.limit:
                break
        return channelNum
        
        
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
