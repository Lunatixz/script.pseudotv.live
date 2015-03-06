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

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import subprocess, os, sys, re, xmltv
import time, datetime, threading, _strptime, calendar
import httplib, urllib, urllib2, feedparser, socket, json
import base64, shutil, random, errno
import Globals, tvdb_api, tmdb_api

from urllib import unquote
from urllib import urlopen
from xml.etree import ElementTree as ET
from xml.dom.minidom import parse, parseString
from subprocess import Popen, PIPE, STDOUT
from Playlist import Playlist
from Globals import *
from Channel import Channel
from VideoParser import VideoParser
from FileAccess import FileAccess
from tvdb import *
from tmdb import *
from urllib2 import urlopen
from urllib2 import HTTPError, URLError
from datetime import date
from utils import *
from datetime import timedelta, timedelta

socket.setdefaulttimeout(30)
    
# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
   
from metahandler import metahandlers

class ChannelList:
    def __init__(self):
        self.networkList = []
        self.studioList = []
        self.mixedGenreList = []
        self.showGenreList = []
        self.movieGenreList = []
        self.movie3Dlist = []
        #self.musicGenreList = []
        self.FavouritesPathList = []
        self.FavouritesNameList = []
        self.showList = []
        self.channels = []
        self.cached_json_detailed_TV = []
        self.cached_json_detailed_Movie = []
        #self.cached_json_detailed_trailers = []
        self.cached_json_detailed_xmltvChannels_local = []
        self.videoParser = VideoParser()
        self.httpJSON = True
        self.autoplaynextitem = False
        self.sleepTime = 0
        self.discoveredWebServer = False
        self.threadPaused = False
        self.runningActionChannel = 0
        self.runningActionId = 0
        self.enteredChannelCount = 0
        self.background = True
        self.seasonal = False
        self.limit = MEDIA_LIMIT[int(REAL_SETTINGS.getSetting('MediaLimit'))]
        if REAL_SETTINGS.getSetting('MediaLimitWarning') == 'false':
            self.limit = 50
        self.Override_ok = REAL_SETTINGS.getSetting('Override_ok') == "true"
        random.seed()

        
    def readConfig(self):
        self.ResetChanLST = list(REAL_SETTINGS.getSetting('ResetChanLST'))
        self.log('Channel Reset List is ' + str(self.ResetChanLST))
        self.channelResetSetting = int(REAL_SETTINGS.getSetting("ChannelResetSetting"))
        self.log('Channel Reset Setting is ' + str(self.channelResetSetting))
        self.forceReset = REAL_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.log('Force Reset is ' + str(self.forceReset))
        self.updateDialog = xbmcgui.DialogProgress()
        self.startMode = int(REAL_SETTINGS.getSetting("StartMode"))
        self.log('Start Mode is ' + str(self.startMode))
        self.backgroundUpdating = int(REAL_SETTINGS.getSetting("ThreadMode"))
        self.inc3D = REAL_SETTINGS.getSetting('Include3D') == "true"
        self.log("Include 3D is " + str(self.inc3D))
        self.incIceLibrary = REAL_SETTINGS.getSetting('IncludeIceLib') == "true"
        self.log("IceLibrary is " + str(self.incIceLibrary))
        self.t = tvdb_api.Tvdb()
        self.tvdbAPI = TVDB(TVDB_API_KEY)
        self.tmdbAPI = TMDB(TMDB_API_KEY)
        self.limit = MEDIA_LIMIT[int(REAL_SETTINGS.getSetting('MediaLimit'))]
        if REAL_SETTINGS.getSetting('MediaLimitWarning') == 'false':
            self.limit = 50
        self.log('Channel Media Limit is ' + str(self.limit))
        self.findMaxChannels()
        
        if self.forceReset:
            REAL_SETTINGS.setSetting("INTRO_PLAYED","false")
            REAL_SETTINGS.setSetting('ForceChannelReset', 'false')
            REAL_SETTINGS.setSetting('StartupMessage', 'false')    
            self.forceReset = False

        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.logError("LastResetTime not found")
            self.lastResetTime = 0

        try:
            self.lastExitTime = int(ADDON_SETTINGS.getSetting("LastExitTime"))
        except:
            self.logError("LastExitTime not found")
            self.lastExitTime = int(time.time())
            
            
    def setupList(self):
        self.log("setupList")
        self.readConfig()
        self.updateDialog.create("PseudoTV Min", "Updating channel list")
        self.updateDialog.update(0, "Updating channel list")
        self.updateDialogProgress = 0
        foundvalid = False
        makenewlists = False
        self.background = False
        
        if self.backgroundUpdating > 0 and self.myOverlay.isMaster == True:
            makenewlists = True
            
        # Go through all channels, create their arrays, and setup the new playlist
        for i in range(self.maxChannels):
            self.updateDialogProgress = i * 100 // self.enteredChannelCount
            self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(i + 1), "waiting for file lock", "")
            self.channels.append(Channel())
            
            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('Update channels cancelled')
                self.updateDialog.close()
                return None
                
            self.setupChannel(i + 1, self.background, makenewlists, False)
            
            if self.channels[i].isValid:
                foundvalid = True

        if makenewlists == True:
            REAL_SETTINGS.setSetting('ForceChannelReset', 'false')

        if foundvalid == False and makenewlists == False:
            for i in range(self.maxChannels):
                self.updateDialogProgress = i * 100 // self.enteredChannelCount
                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(i + 1), "waiting for file lock", '')
                self.setupChannel(i + 1, self.background, True, False)

                if self.channels[i].isValid:
                    foundvalid = True
                    break

        self.updateDialog.update(100, "Channel List Update complete")
        self.updateDialog.close()
        return self.channels 

        
    def log(self, msg, level = xbmc.LOGNOTICE):
        logGlob('ChannelList: ' + msg, level)
    
    def logDebug(self, msg):
        logGlob('ChannelList: ' + msg)
    
    def logError(self, msg):
        logGlob('ChannelList: ' + msg, xbmc.LOGERROR)
            
            
    # Determine the maximum number of channels by opening consecutive
    # playlists until we don't find one
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
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_1')
                chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_2')
                chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_3')
                chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_4')
            except Exception,e:
                pass

            if chtype == 0:
                if FileAccess.exists(xbmc.translatePath(chsetting1)):
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype <= 20:
                if len(chsetting1) > 0:
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
                    
            if self.forceReset and (chtype != 9999):
                ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_changed', "True")

        self.log('findMaxChannels return ' + str(self.maxChannels))


    def determineWebServer(self):
        if self.discoveredWebServer:
            return

        self.discoveredWebServer = True
        self.webPort = 8080
        self.webUsername = ''
        self.webPassword = ''
        fle = xbmc.translatePath("special://profile/guisettings.xml")

        try:
            xml = FileAccess.open(fle, "r")
        except Exception,e:
            self.logError("determineWebServer Unable to open the settings file")
            self.httpJSON = False
            return

        try:
            dom = parse(xml)
        except Exception,e:
            self.logError('determineWebServer Unable to parse settings file')
            self.httpJSON = False
            return

        xml.close()
                
        try:
            plname = dom.getElementsByTagName('webserver')
            self.httpJSON = (plname[0].childNodes[0].nodeValue.lower() == 'true')
            self.log('determineWebServer is ' + str(self.httpJSON))
            autoplaynextitem = dom.getElementsByTagName('autoplaynextitem')
            self.autoplaynextitem  = (autoplaynextitem[1].childNodes[0].nodeValue.lower() == 'true')
            self.log('autoplaynextitem is ' + str(self.autoplaynextitem))
            
            if self.httpJSON == True:
                plname = dom.getElementsByTagName('webserverport')
                self.webPort = int(plname[0].childNodes[0].nodeValue)
                self.log('determineWebServer port ' + str(self.webPort))
                plname = dom.getElementsByTagName('webserverusername')
                self.webUsername = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer username ' + self.webUsername)
                plname = dom.getElementsByTagName('webserverpassword')
                self.webPassword = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer password is ' + self.webPassword)
        except Exception,e:
            return

    
    # Code for sending JSON through http adapted from code by sffjunkie (forum.xbmc.org/showthread.php?t=92196)
    def sendJSON(self, command):
        self.log('sendJSON')
        data = ''
        usedhttp = False

        self.determineWebServer()
        self.log('sendJSON command: ' + command)

        # If there have been problems using the server, just skip the attempt and use executejsonrpc
        if self.httpJSON == True:
            try:
                payload = command.encode('utf-8')
            except Exception,e:
                self.logError('JSON payload ' + str(e))
                return data

            headers = {'Content-Type': 'application/json-rpc; charset=utf-8'}

            if self.webUsername != '':
                userpass = base64.encodestring('%s:%s' % (self.webUsername, self.webPassword))[:-1]
                headers['Authorization'] = 'Basic %s' % userpass

            try:
                conn = httplib.HTTPConnection('127.0.0.1', self.webPort)
                conn.request('POST', '/jsonrpc', payload, headers)
                response = conn.getresponse()

                if response.status == 200:
                    data = uni(response.read())
                    usedhttp = True
                conn.close()
            except Exception,e:
                self.log("Exception when getting JSON data")

        if usedhttp == False:
            self.httpJSON = False
            
            try:
                data = xbmc.executeJSONRPC(uni(command))
            except UnicodeEncodeError:
                data = xbmc.executeJSONRPC(ascii(command))

        return uni(data)
        
     
    def setupChannel(self, channel, background = False, makenewlist = False, append = False):
        self.log('setupChannel ' + str(channel))
        returnval = False
        createlist = makenewlist
        chtype = 9999
        chsetting1 = ''
        chsetting2 = ''
        chsetting3 = ''
        chsetting4 = ''
        needsreset = False
        self.background = background
        self.settingChannel = channel

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1')
            chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2')
            chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3')
            chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_4')
        except Exception,e:
            pass

        while len(self.channels) < channel:
            self.channels.append(Channel())

        if chtype == 9999:
            self.channels[channel - 1].isValid = False
            return False

        self.channels[channel - 1].type = chtype
        self.channels[channel - 1].isSetup = True
        self.channels[channel - 1].loadRules(channel)
        self.runActions(RULES_ACTION_START, channel, self.channels[channel - 1])

        try:
            needsreset = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_changed') == 'True'
                
            if needsreset:
                if chtype <= 7:
                    localTV.delete("%")
                self.channels[channel - 1].isSetup = False
        except Exception,e:
            pass

        # If possible, use an existing playlist
        # Don't do this if we're appending an existing channel
        # Don't load if we need to reset anyway
        if FileAccess.exists(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') and append == False and needsreset == False:
            try:
                self.channels[channel - 1].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_time', True))
                createlist = True

                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(channel), "reading playlist", '')

                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    self.channels[channel - 1].isValid = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    returnval = True

                    # If this channel has been watched for longer than it lasts, reset the channel
                    if self.channelResetSetting == 0 and self.channels[channel - 1].totalTimePlayed < self.channels[channel - 1].getTotalDuration():
                        createlist = False

                    if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                        timedif = time.time() - self.lastResetTime

                        if self.channelResetSetting == 1 and timedif < (60 * 60 * 24): # 24 hours
                            createlist = False

                        if self.channelResetSetting == 2 and timedif < (60 * 60 * 24 * 7): # 1 week
                            createlist = False

                        if self.channelResetSetting == 3 and timedif < (60 * 60 * 24 * 30): # 1 month
                            createlist = False

                        if timedif < 0:
                            createlist = False

                    if self.channelResetSetting == 4:
                        createlist = False
            except Exception,e:
                pass

        if createlist or needsreset:
            self.channels[channel - 1].isValid = False

            if makenewlist:
                self.logDebug('makenewlist: ' + CHANNELS_LOC)
                try:#remove old playlist
                    xbmcvfs.delete(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u')
                except Exception,e:
                    pass

                append = False

                if createlist:
                    ADDON_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

        if append == False:
            if chtype == 6 and chsetting2 == str(MODE_ORDERAIRDATE):
                self.channels[channel - 1].mode = MODE_ORDERAIRDATE

            # if there is no start mode in the channel mode flags, set it to the default
            if self.channels[channel - 1].mode & MODE_STARTMODES == 0:
                if self.startMode == 0:
                    self.channels[channel - 1].mode |= MODE_RESUME
                elif self.startMode == 1:
                    self.channels[channel - 1].mode |= MODE_REALTIME
                elif self.startMode == 2:
                    self.channels[channel - 1].mode |= MODE_RANDOM

        if ((createlist or needsreset) and makenewlist) or append:
            if self.background == False:
                self.updateDialogProgress = (channel - 1) * 100 // self.enteredChannelCount
                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(channel), "", '')

            if self.makeChannelList(channel, chtype, chsetting1, chsetting2, chsetting3, chsetting4, append) == True:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    returnval = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    self.channels[channel - 1].isValid = True
                    
                    # Don't reset variables on an appending channel
                    if append == False:
                        self.channels[channel - 1].totalTimePlayed = 0
                        ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', '0')

                        if needsreset:
                            if channel not in self.ResetChanLST:
                                ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_changed', 'False')
                            REAL_SETTINGS.setSetting('ResetChanLST', '')
                            self.channels[channel - 1].isSetup = True
                    
        self.runActions(RULES_ACTION_BEFORE_CLEAR, channel, self.channels[channel - 1])

        # Don't clear history when appending channels
        if self.background == False and append == False and self.myOverlay.isMaster:
            self.updateDialogProgress = (channel - 1) * 100 // self.enteredChannelCount
            self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(channel), "clearing history", '')
            self.clearPlaylistHistory(channel)

        if append == False:
            self.runActions(RULES_ACTION_BEFORE_TIME, channel, self.channels[channel - 1])

            if self.channels[channel - 1].mode & MODE_ALWAYSPAUSE > 0:
                self.channels[channel - 1].isPaused = True

            if self.channels[channel - 1].mode & MODE_RANDOM > 0:
                self.channels[channel - 1].showTimeOffset = random.randint(0, self.channels[channel - 1].getTotalDuration())

            if self.channels[channel - 1].mode & MODE_REALTIME > 0:
                timedif = int(self.myOverlay.timeStarted) - self.lastExitTime
                self.channels[channel - 1].totalTimePlayed += timedif

            if self.channels[channel - 1].mode & MODE_RESUME > 0:
                self.channels[channel - 1].showTimeOffset = self.channels[channel - 1].totalTimePlayed
                self.channels[channel - 1].totalTimePlayed = 0

            while self.channels[channel - 1].showTimeOffset > self.channels[channel - 1].getCurrentDuration():
                self.channels[channel - 1].showTimeOffset -= self.channels[channel - 1].getCurrentDuration()
                self.channels[channel - 1].addShowPosition(1)

        self.channels[channel - 1].name = self.getChannelName(chtype, chsetting1)

        if ((createlist or needsreset) and makenewlist) and returnval:
            self.runActions(RULES_ACTION_FINAL_MADE, channel, self.channels[channel - 1])
        else:
            self.runActions(RULES_ACTION_FINAL_LOADED, channel, self.channels[channel - 1])
        
        return returnval

        
    def clearPlaylistHistory(self, channel):
        self.logDebug("clearPlaylistHistory")

        if self.channels[channel - 1].isValid == False:
            iBadChan = channel -1
            self.log("channel [%s] already clear, ignoring" %iBadChan)
            return

        # if we actually need to clear anything
        if self.channels[channel - 1].totalTimePlayed > (60 * 60 * 24 * 2):
            try:
                fle = FileAccess.open(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', 'w')
            except Exception,e:
                self.logError("clearPlaylistHistory Unable to open the smart playlist")
                return

            flewrite = uni("#EXTM3U\n")
            tottime = 0
            timeremoved = 0

            for i in range(self.channels[channel - 1].Playlist.size()):
                tottime += self.channels[channel - 1].getItemDuration(i)

                if tottime > (self.channels[channel - 1].totalTimePlayed - (60 * 60 * 12)):
                    tmpstr = str(self.channels[channel - 1].getItemDuration(i)) + ','
                    tmpstr += self.channels[channel - 1].getItemTitle(i) + "//" + self.channels[channel - 1].getItemEpisodeTitle(i) + "//" + self.channels[channel - 1].getItemDescription(i) + "//" + self.channels[channel - 1].getItemgenre(i) + "//" + self.channels[channel - 1].getItemtimestamp(i) + "//" + self.channels[channel - 1].getItemLiveID(i)
                    tmpstr = uni(tmpstr[:2036])
                    tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                    tmpstr = uni(tmpstr) + uni('\n') + uni(self.channels[channel - 1].getItemFilename(i))
                    flewrite += uni("#EXTINF:") + uni(tmpstr) + uni("\n")
                else:
                    timeremoved = tottime

            fle.write(flewrite)
            fle.close()

            if timeremoved > 0:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == False:
                    self.channels[channel - 1].isValid = False
                else:
                    self.channels[channel - 1].totalTimePlayed -= timeremoved
                    # Write this now so anything sharing the playlists will get the proper info
                    ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', str(self.channels[channel - 1].totalTimePlayed))


    def getChannelName(self, chtype, setting1):
        self.logDebug('getChannelName ' + str(chtype))
        
        if chtype <= 7:
            if len(setting1) == 0:
                return ''

        if chtype == 0:
            return self.getSmartPlaylistName(setting1)
        elif chtype == 1 or chtype == 2 or chtype == 5 or chtype == 6:
            return setting1
        elif chtype == 3:
            return setting1 + " TV"
        elif chtype == 4:
            return setting1 + " Movies"
        #elif chtype == 12:
        #    return setting1 + " Music"
        elif chtype == 7:
            if setting1[-1] == '/' or setting1[-1] == '\\':
                return os.path.split(setting1[:-1])[1]
            else:
                return os.path.split(setting1)[1]
        #elif chtype == 8:
        #    setting1 = channel
        #    return ADDON_SETTINGS.getSetting("Channel_" + str(setting1) + "_opt_1")        
        return ''


    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        self.logDebug('getSmartPlaylistName')
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except Exception,e:
            self.logError("getSmartPlaylistName Unable to open the smart playlist")
            return ''

        try:
            dom = parse(xml)
        except Exception,e:
            self.logError('getSmartPlaylistName Problem parsing playlist')
            xml.close()
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log('getSmartPlaylistName return ' + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except Exception,e:
            self.logError("Unable to get the playlist name.")
            return ''
    
    
    # Based on a smart playlist, create a normal playlist that can actually be used by us
    def makeChannelList(self, channel, chtype, setting1, setting2, setting3, setting4, append = False):
        self.logDebug('makeChannelList, CHANNEL: ' + str(channel))
        fileListCHK = False
        israndom = False  
        reverseOrder = False
        fileList = []
        limit = self.limit
        setting4 = setting4.replace('Default','0').replace('Random','1').replace('Reverse','2') 
        
        if setting4 == '0':
            #DEFAULT
            israndom = False  
            reverseOrder = False
        elif setting4 == '1':
            #RANDOM
            israndom = True
            reverseOrder = False
        elif setting4 == '2':
            #REVERSE ORDER
            israndom = False
            reverseOrder = True
        
        # Directory
        if chtype == 7:
            self.logDebug('-Making Directory Playlist')
            fileList = self.createDirectoryPlaylist(setting1, setting3, setting4, limit)
        else:
            if chtype == 0:
                if FileAccess.copy(setting1, MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                    if FileAccess.exists(MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                        self.logError("Unable to copy or find playlist " + setting1)
                        return False

                fle = MADE_CHAN_LOC + os.path.split(setting1)[1]
            else:
                fle = self.makeTypePlaylist(chtype, setting1, setting2)
            
            if len(fle) == 0:
                self.logError('Unable to locate the playlist for channel' + str(channel))
                return False
            
            try:
                xml = FileAccess.open(fle, "r")
            except Exception,e:
                self.logError("makeChannelList Unable to open the smart playlist")
                return False
            
            try:
                dom = parse(xml)
            except Exception,e:
                self.logError('makeChannelList Problem parsing playlist')
                xml.close()
                return False
            
            xml.close()
            
            
            if self.getSmartPlaylistType(dom) == 'mixed':
                self.logDebug('makeChannelList, CHANNEL: ' + str(channel) + ' | mixed list')
                fileList = self.buildMixedFileList(dom, channel, limit)
            
            elif self.getSmartPlaylistType(dom) == 'movies':
                self.logDebug('makeChannelList, CHANNEL: ' + str(channel) + ' | movies')
                fileList = self.buildFileList(fle, channel, limit)
            
            elif self.getSmartPlaylistType(dom) == 'episodes':
                self.logDebug('makeChannelList, CHANNEL: ' + str(channel) + ' | episodes')
                fileList = self.buildFileList(fle, channel, limit)
            
            else:
                self.logDebug('makeChannelList, CHANNEL: ' + str(channel) + ' | else')
                fileList = self.buildFileList(fle, channel, limit)

            try:
                order = dom.getElementsByTagName('order')

                if order[0].childNodes[0].nodeValue.lower() == 'random':
                    israndom = True
            except Exception,e:
                pass

        try:
            if append == True:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "r+")
                channelplaylist.seek(0, 2)
            else:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w")
        except Exception,e:
            self.logError('Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u')
            return False

        if append == False:
            channelplaylist.write(uni("#EXTM3U\n"))
            #first queue m3u
            
        if fileList != None:  
            if len(fileList) == 0:
                self.logError("Unable to get information about channel " + str(channel))
                channelplaylist.close()
                return False

        if israndom:
            random.shuffle(fileList)
            
        if reverseOrder:
            fileList.reverse()

        if len(fileList) > 16384:
            fileList = fileList[:16384]

        fileList = self.runActions(RULES_ACTION_LIST, channel, fileList)
        self.channels[channel - 1].isRandom = israndom

        if append:
            if len(fileList) + self.channels[channel - 1].Playlist.size() > 16384:
                fileList = fileList[:(16384 - self.channels[channel - 1].Playlist.size())]
        else:
            if len(fileList) > 16384:
                fileList = fileList[:16384]

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write(uni("#EXTINF:") + uni(string) + uni("\n"))
            
        channelplaylist.close()
        self.log('makeChannelList return')
        return True

        
    def makeTypePlaylist(self, chtype, setting1, setting2):
    
        if chtype == 1:
            if len(self.networkList) == 0:
                self.fillTVInfo()
            return self.createNetworkPlaylist(setting1)
            
        elif chtype == 2:
            self.logDebug('CREATE STUDIO LIST')
            if len(self.studioList) == 0:
                self.fillMovieInfo()
            return self.createStudioPlaylist(setting1)
            
        elif chtype == 3:
            self.logDebug('CREATE GENRE E LIST')
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            return self.createGenrePlaylist('episodes', chtype, setting1)
            
        elif chtype == 4:
            self.logDebug('CREATE GENRE M LIST')
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()
            return self.createGenrePlaylist('movies', chtype, setting1)
            
        elif chtype == 5:
            if len(self.mixedGenreList) == 0:
                if len(self.showGenreList) == 0:
                    self.fillTVInfo()

                if len(self.movieGenreList) == 0:
                    self.fillMovieInfo()

                self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
                self.mixedGenreList.sort(key=lambda x: x.lower())
            return self.createGenreMixedPlaylist(setting1)
            
        elif chtype == 6:
            if len(self.showList) == 0:
                self.fillTVInfo()
            return self.createShowPlaylist(setting1, setting2)
        
        self.logError('makeTypePlaylists invalid channel type: ' + str(chtype))
        return ''    
    
    
    def createNetworkPlaylist(self, network):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'network_' + network + '.xsp')
        limit = self.limit
        
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to network playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the network playlist cache file ' + flename)
            return ''

        self.writeXSPHeader(fle, "episodes", self.getChannelName(1, network))
        network = network.lower()
        added = False

        fle.write('    <rule field="tvshow" operator="is">\n')
        
        for i in range(len(self.showList)):
            if self.threadPause() == False:
                fle.close()
                return ''

            if self.showList[i][1].lower() == network:
                theshow = self.cleanString(self.showList[i][0])                
                fle.write('        <value>' + theshow + '</value>\n')            
                added = True
        
        fle.write('    </rule>\n')
        
        self.writeXSPFooter(fle, limit, "random")
        fle.close()

        if added == False:
            return ''
        return flename


    def createShowPlaylist(self, show, setting2):
        order = 'random'

        try:
            setting = int(setting2)
            if setting & MODE_ORDERAIRDATE > 0:
                order = 'episode'
        except Exception,e:
            pass

        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Show_' + show + '_' + order + '.xsp')
        limit = self.limit
        
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to show playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the show playlist cache file ' + flename)
            return ''

        self.writeXSPHeader(fle, 'episodes', self.getChannelName(6, show))
        show = self.cleanString(show)
        fle.write('    <rule field="tvshow" operator="is">\n')
        fle.write('        <value>' + show + '</value>\n')
        fle.write('    </rule>\n')
        
        self.writeXSPFooter(fle, limit, order)
        fle.close()
        return flename

    
    def fillMixedGenreInfo(self):
        if len(self.mixedGenreList) == 0:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()

            self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
            self.mixedGenreList.sort(key=lambda x: x.lower())

    
    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break
        return newlist
    
    
    def createGenreMixedPlaylist(self, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'mixed_' + genre + '.xsp')
        limit = self.limit
        
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to genre-mixed playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the genre-mixed playlist cache file ' + flename)
            return ''

        epname = os.path.basename(self.createGenrePlaylist('episodes', 3, genre))
        moname = os.path.basename(self.createGenrePlaylist('movies', 4, genre))
        self.writeXSPHeader(fle, 'mixed', self.getChannelName(5, genre))
        fle.write('    <rule field="playlist" operator="is">' + epname + '</rule>\n')
        fle.write('    <rule field="playlist" operator="is">' + moname + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename


    def createGenrePlaylist(self, pltype, chtype, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + '_' + genre + '.xsp')
        limit = self.limit
        
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to genre playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the genre playlist cache file ' + flename)
            return ''

        self.writeXSPHeader(fle, pltype, self.getChannelName(chtype, genre))
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">\n')
        fle.write('        <value>' + genre + '</value>\n')
        fle.write('    </rule>\n')
        
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename


    def createStudioPlaylist(self, studio):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Studio_' + studio + '.xsp')
        limit = self.limit
        
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to studio playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the studio playlist cache file ' + flename)
            return ''

        self.writeXSPHeader(fle, "movies", self.getChannelName(2, studio))
        studio = self.cleanString(studio)
        fle.write('    <rule field="studio" operator="is">\n')
        fle.write('        <value>' + studio + '</value>\n')
        fle.write('    </rule>\n')
        
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename
    
    
    
    def createRecentlyAddedTV(self):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'episodes_RecentlyAddedTV.xsp')
        limit = self.limit
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to recently-added-tv playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the recently-tv playlist cache file ' + flename)
            return ''

        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="episodes">\n')
        fle.write('    <name>Recently Added TV</name>\n')
        fle.write('    <match>all</match>\n')
        fle.write('    <rule field="dateadded" operator="inthelast">\n')
        fle.write('        <value>14</value>\n')
        fle.write('    </rule>\n')
        fle.write('    <limit>'+str(limit)+'</limit>\n')
        fle.write('    <order direction="descending">dateadded</order>\n')
        fle.write('</smartplaylist>\n')
        fle.close()
        return flename
        
    
    def createRecentlyAddedMovies(self):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'movies_RecentlyAddedMovies.xsp')
        limit = self.limit
        try:
            fle = FileAccess.open(flename, "w")
            self.logDebug('adding to recently-added-movies playlist: ' + flename)
        except Exception,e:
            self.logError('Unable to open the recently-movies playlist cache file ' + flename)
            return ''

        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="movies">\n')
        fle.write('    <name>Recently Added Movies</name>\n')
        fle.write('    <match>all</match>\n')
        fle.write('    <rule field="dateadded" operator="inthelast">\n')
        fle.write('        <value>14</value>\n')
        fle.write('    </rule>\n')
        fle.write('    <limit>'+str(limit)+'</limit>\n')
        fle.write('    <order direction="descending">dateadded</order>\n')
        fle.write('</smartplaylist>\n')
        fle.close()
        return flename
        

    def createDirectoryPlaylist(self, setting1, setting3, setting4, limit):
        self.log("createDirectoryPlaylist" + setting1)
        fileList = []
        LocalLST = []
        LocalFLE = ''
        filecount = 0 
        LiveID = 'other|0|0|False|1|NR|'
        LocalLST = self.walk(setting1)
        
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "getting file list")
        
        for f in LocalLST:         
            if self.threadPause() == False:
                del fileList[:]
                break
                
        for i in range(len(LocalLST)):    
            LocalFLE = (LocalLST[i])[0]
            duration = self.videoParser.getVideoLength(LocalFLE)
                                            
            '''if duration == 0 and LocalFLE[-4:].lower() == 'strm':
                duration = 3600
                self.log("createDirectoryPlaylist, no strm duration found defaulting to 3600")'''
                    
            if duration > 0:
                filecount += 1
                
                if self.background == False:
                    if filecount == 1:
                        self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "added " + str(filecount) + " entry")
                    else:
                        self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "added " + str(filecount) + " entries")
                
                title = (os.path.split(LocalFLE)[1])
                title = os.path.splitext(title)[0].replace('.', ' ')
                description = LocalFLE.replace('//','/').replace('/','\\')
                
                tmpstr = str(duration) + ',' + title + "//" + 'Directory Video' + "//" + description + "//" + 'Unknown' + "////" + LiveID + '\n' + (LocalFLE)
                tmpstr = tmpstr[:2036]
                fileList.append(tmpstr)
                
                if setting3 != '':
                    if filecount >= int(setting3):
                        print 'createDirectoryPlaylist, filecount override break'
                        break
                else:
                    #zero limit equals unlimited.
                    if limit != 0:
                        if filecount >= limit:
                            print 'createDirectoryPlaylist, filecount break'
                            break
        
        if filecount == 0:
            self.log('Unable to access Videos files in ' + setting1)
        return fileList


    def writeXSPHeader(self, fle, pltype, plname):
        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="'+pltype+'">\n')
        plname = self.cleanString(plname)
        fle.write('    <name>'+plname+'</name>\n')
        fle.write('    <match>one</match>\n')


    def writeXSPFooter(self, fle, limit, order):
        if limit > 0:
            fle.write('    <limit>'+str(limit)+'</limit>\n')
        fle.write('    <order direction="ascending">' + order + '</order>\n')
        fle.write('</smartplaylist>\n')

    
    def cleanString(self, string):
        newstr = uni(string)
        newstr = newstr.replace('&', '&amp;')
        newstr = newstr.replace('>', '&gt;')
        newstr = newstr.replace('<', '&lt;')
        return uni(newstr)

    
    def uncleanString(self, string):
        self.log("uncleanString")
        newstr = string
        newstr = newstr.replace('&amp;', '&')
        newstr = newstr.replace('&gt;', '>')
        newstr = newstr.replace('&lt;', '<')
        return uni(newstr)
               
            
    def fillMusicInfo(self, sortbycount = False):
        self.log("fillMusicInfo")
        self.musicGenreList = []
        json_query = ('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties":["genre"]}, "id": 1}')
        
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding music", "reading music data")

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.musicGenreList[:]
                return

            match = re.search('"genre" *: *\[(.*?)\]', f)
          
            if match:
                genres = match.group(1).split(',')
               
                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.musicGenreList)):
                        if self.threadPause() == False:
                            del self.musicGenreList[:]
                            return
                            
                        itm = self.musicGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.musicGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.musicGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.musicGenreList.append(genre.strip('"').strip())
    
        if sortbycount:
            self.musicGenreList.sort(key=lambda x: x[1], reverse = True)
        else:
            self.musicGenreList.sort(key=lambda x: x.lower())

        if (len(self.musicGenreList) == 0):
            self.logDebug(json_folder_detail)

        self.log("found genres " + str(self.musicGenreList))
     
    
    def fillTVInfo(self, sortbycount = False):
        self.log("fillTVInfo")
        json_query = ('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties":["studio", "genre"]}, "id": 1}')

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "reading TV data")

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.networkList[:]
                del self.showList[:]
                del self.showGenreList[:]
                return

            match = re.search('"studio" *: *\[(.*?)\]', f)
            network = ''

            if match:
                network = (match.group(1).split(','))[0]
                network = network.strip('"').strip()
                found = False

                for item in range(len(self.networkList)):
                    if self.threadPause() == False:
                        del self.networkList[:]
                        del self.showList[:]
                        del self.showGenreList[:]
                        return

                    itm = self.networkList[item]

                    if sortbycount:
                        itm = itm[0]

                    if itm.lower() == network.lower():
                        found = True

                        if sortbycount:
                            self.networkList[item][1] += 1

                        break

                if found == False and len(network) > 0:
                    if sortbycount:
                        self.networkList.append([network, 1])
                    else:
                        self.networkList.append(network)

            match = re.search('"label" *: *"(.*?)",', f)

            if match:
                show = match.group(1).strip()
                self.showList.append([show, network])
                
            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(',')
                
                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.showGenreList)):
                        if self.threadPause() == False:
                            del self.networkList[:]
                            del self.showList[:]
                            del self.showGenreList[:]
                            return

                        itm = self.showGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.showGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.showGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.showGenreList.append(genre.strip('"').strip())

        if sortbycount:
            self.networkList.sort(key=lambda x: x[1], reverse = True)
            self.showGenreList.sort(key=lambda x: x[1], reverse = True)
        else:
            self.networkList.sort(key=lambda x: x.lower())
            self.showGenreList.sort(key=lambda x: x.lower())

        if (len(self.showList) == 0) and (len(self.showGenreList) == 0) and (len(self.networkList) == 0):
            self.logDebug(json_folder_detail)

        self.log("found shows " + str(self.showList))
        self.log("found genres " + str(self.showGenreList))
        self.log("fillTVInfo return " + str(self.networkList))


    def fillMovieInfo(self, sortbycount = False):
        self.log("fillMovieInfo")
        studioList = []
        json_query = ('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties":["studio", "genre"]}, "id": 1}')

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "reading movie data")

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.movieGenreList[:]
                del self.studioList[:]
                del studioList[:]
                break

            match = re.search('"genre" *: *\[(.*?)\]', f)

            if match:
                genres = match.group(1).split(',')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.movieGenreList)):
                        itm = self.movieGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.movieGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.movieGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.movieGenreList.append(genre.strip('"').strip())

            match = re.search('"studio" *: *\[(.*?)\]', f)
           
            if match:
                studios = match.group(1).split(',')
                
                for studio in studios:
                    curstudio = studio.strip('"').strip()
                    found = False

                    for i in range(len(studioList)):
                        if studioList[i][0].lower() == curstudio.lower():
                            studioList[i][1] += 1
                            found = True
                            break

                    if found == False and len(curstudio) > 0:
                        studioList.append([curstudio, 1])

        maxcount = 0

        for i in range(len(studioList)):
            if studioList[i][1] > maxcount:
                maxcount = studioList[i][1]

        bestmatch = 1
        lastmatch = 1000
        counteditems = 0

        for i in range(maxcount, 0, -1):
            itemcount = 0

            for j in range(len(studioList)):
                if studioList[j][1] == i:
                    itemcount += 1

            if abs(itemcount + counteditems - 8) < abs(lastmatch - 8):
                bestmatch = i
                lastmatch = itemcount

            counteditems += itemcount

        if sortbycount:
            studioList.sort(key=lambda x: x[1], reverse=True)
            self.movieGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            studioList.sort(key=lambda x: x[0].lower())
            self.movieGenreList.sort(key=lambda x: x.lower())

        for i in range(len(studioList)):
            if studioList[i][1] >= bestmatch:
                if sortbycount:
                    self.studioList.append([studioList[i][0], studioList[i][1]])
                else:
                    self.studioList.append(studioList[i][0])

        if (len(self.movieGenreList) == 0) and (len(self.studioList) == 0):
            self.logDebug(json_folder_detail)

        self.log("found genres " + str(self.movieGenreList))
        self.log("fillMovieInfo return " + str(self.studioList))


    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        self.log("makeMixedList return " + str(newlist))
        return newlist
        
    # pack to string for playlist
    def packGenreLiveID(self, GenreLiveID):
        self.log("packGenreLiveID")
        genre = GenreLiveID[0]
        GenreLiveID.pop(0)
        LiveID = (str(GenreLiveID)).replace("u'",'').replace(',','|').replace('[','').replace(']','').replace("'",'').replace(" ",'') + '|'
        return genre, LiveID
        
        
    # unpack to list for parsing
    def unpackLiveID(self, LiveID):
        self.log("unpackLiveID")
        LiveID = LiveID.split('|')
        return LiveID

         
    def isMedia3D(self, path):
        if Cache_Enabled == True:
            try:
                result = parsers.cacheFunction(self.isMedia3D_NEW, path)
            except:
                result = self.isMedia3D_NEW(path)
                pass
        else:
            result = self.isMedia3D_NEW(path)
        if not result:
            result = False
        return result  

         
    def isMedia3D_NEW(self, path):
        flag3d = False
        for i in range(len(FILTER_3D)):
            if FILTER_3D[i] in path:   
                flag3d = True                        
                break
        return flag3d
        
        
    def buildFileList(self, dir_name, channel, limit):
        self.log("buildFileList Cache")
        if Cache_Enabled == True:
            try:
                result = localTV.cacheFunction(self.buildFileList_NEW, dir_name, channel, limit)
            except:
                result = self.buildFileList_NEW(dir_name, channel, limit)
                pass
        else:
            result = self.buildFileList_NEW(dir_name, channel, limit)
        if not result:
            result = []
        return result  
        
        
    def buildFileList_NEW(self, dir_name, channel, limit, FleType = 'video'):
        self.log("buildFileList")
        fileList = []
        seasoneplist = []
        file_detail = []
        filecount = 0
        LiveID = 'other|0|0|False|1|NR|'
        json_query = uni('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "properties":["title","year","mpaa","imdbnumber","description","season","episode","playcount","genre","duration","runtime","showtitle","album","artist","plot","plotoutline","tagline","tvshowid"]}, "id": 1}' % (self.escapeDirJSON(dir_name), FleType))

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "querying database")
        
        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in file_detail:
            if self.threadPause() == False:
                del fileList[:]
                break
                
            istvshow = False
            flag3d = False
            Managed = False
            match = re.search('"file" *: *"(.*?)",', f)
            
            if match:
                if not self.videoParser.extCheck(match.group(1)):
                    self.log('Omitting %s' %match.group(1))
                elif(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    fileList.extend(self.buildFileList(match.group(1), channel, limit))
                else:
                    f = self.runActions(RULES_ACTION_JSON, channel, f)
                    duration = re.search('"duration" *: *([0-9]*?),', f)
                    dur = 0
                    
                    # If duration doesn't exist, try to figure it out, skip strms
                    if dur == 0:
                        try:
                            dur = self.videoParser.getVideoLength(uni(match.group(1)).replace("\\\\", "\\"))
                        except Exception,e:
                            dur = 0
                            self.logError('Cannot get video duration.. attempt 1')
                            
                    # As a last resort (since it's not as accurate), use runtime
                    if dur == 0:
                        duration = re.search('"runtime" *: *([0-9]*?),', f)
                        try:
                            dur = int(duration.group(1))
                        except Exception,e:
                            dur = 0
                            self.logError('Cannot get video duration.. attempt 2')
                    
                    # Filter 3D Media.
                    '''if self.inc3D == False:
                        flag3d = self.isMedia3D(match.group(1).replace("\\\\", "\\").lower())
                        self.log('3D check: %s' %str(flag3d))'''
                    
                    self.log("buildFileList, dur = " + str(dur))
                    if dur == 0:
                        self.logError('Cannot get video duration.. all attempts failed')
                    
                    try:
                        if dur > 0:
                            filecount += 1
                            seasonval = -1
                            epval = -1

                            if self.background == False:
                                if filecount == 1:
                                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "added " + str(filecount) + " entry")
                                else:
                                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding Videos", "added " + str(filecount) + " entries")
                            
                            tmpstr = str(dur) + ','
                            titles = re.search('"label" *: *"(.*?)"', f)
                            showtitles = re.search('"showtitle" *: *"(.*?)"', f)
                            plots = re.search('"plot" *: *"(.*?)",', f)
                            plotoutlines = re.search('"plotoutline" *: *"(.*?)",', f)
                            years = re.search('"year" *: *([\d.]*\d+)', f)
                            genres = re.search('"genre" *: *\[(.*?)\]', f)
                            playcounts = re.search('"playcount" *: *([\d.]*\d+),', f)
                            imdbnumbers = re.search('"imdbnumber" *: *"(.*?)"', f)
                            ratings = re.search('"mpaa" *: *"(.*?)"', f)
                            descriptions = re.search('"description" *: *"(.*?)"', f)
                            
                            if showtitles != None and len(showtitles.group(1)) > 0:
                                type = 'tvshow'
                                dbids = re.search('"tvshowid" *: *([\d.]*\d+),', f)   
                            else:
                                type = 'movie'
                                dbids = re.search('"id" *: *([\d.]*\d+),', f)

                            # if possible find year by title
                            if years == None and len(years.group(1)) == 0:
                                try:
                                    year = int(((showtitles.group(1)).split(' ('))[1].replace(')',''))
                                except Exception,e:
                                    try:
                                        year = int(((titles.group(1)).split(' ('))[1].replace(')',''))
                                    except:
                                        year = 0
                                        pass
                            else:
                                year = 0
                                
                            if genres != None and len(genres.group(1)) > 0:
                                genre = ((genres.group(1).split(',')[0]).replace('"',''))
                            else:
                                genre = 'Unknown'
                            
                            if playcounts != None and len(playcounts.group(1)) > 0:
                                playcount = playcounts.group(1)
                            else:
                                playcount = 1
                    
                            if ratings != None and len(ratings.group(1)) > 0:
                                rating = self.cleanRating(ratings.group(1))
                                if type == 'movie':
                                    rating = rating[0:5]
                                    try:
                                        rating = rating.split(' ')[0]
                                    except:
                                        pass
                            else:
                                rating = 'NR'
                            
                            if imdbnumbers != None and len(imdbnumbers.group(1)) > 0:
                                imdbnumber = imdbnumbers.group(1)
                            else:
                                imdbnumber = 0
                                
                            if dbids != None and len(dbids.group(1)) > 0:
                                dbid = dbids.group(1)
                            else:
                                dbid = 0

                            if plots != None and len(plots.group(1)) > 0:
                                theplot = (plots.group(1)).replace('\\','').replace('\n','')
                            elif descriptions != None and len(descriptions.group(1)) > 0:
                                theplot = (descriptions.group(1)).replace('\\','').replace('\n','')
                            else:
                                theplot = (titles.group(1)).replace('\\','').replace('\n','')
                            
                            try:
                                theplot = (self.trim(theplot, 350, '...'))
                            except Exception,e:
                                self.log("Plot Trim failed" + str(e))
                                theplot = (theplot[:350])

                            # This is a TV show
                            if showtitles != None and len(showtitles.group(1)) > 0:
                                season = re.search('"season" *: *(.*?),', f)
                                episode = re.search('"episode" *: *(.*?),', f)
                                swtitle = (titles.group(1)).replace('\\','')
                                swtitle = (swtitle.split('.', 1)[-1]).replace('. ','')
                                
                                try:
                                    seasonval = int(season.group(1))
                                    epval = int(episode.group(1))
                                    swtitle = (('0' if seasonval < 10 else '') + str(seasonval) + 'x' + ('0' if epval < 10 else '') + str(epval) + ' - ' + (swtitle)).replace('  ',' ')
                                except Exception,e:
                                    self.log("Season/Episode formatting failed" + str(e))
                                    seasonval = -1
                                    epval = -1

                                if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':  
                                    #print 'EnhancedGuideData'

                                    if imdbnumber == 0:
                                        imdbnumber = self.getTVDBID(showtitles.group(1), year)
                                            
                                    if genre == 'Unknown':
                                        genre = (self.getGenre(type, showtitles.group(1), year))
                                        
                                    if rating == 'NR':
                                        rating = (self.getRating(type, showtitles.group(1), year, imdbnumber))

                                    '''if imdbnumber != 0:
                                        Managed = self.sbManaged(imdbnumber)'''

                                GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating] 
                                genre, LiveID = self.packGenreLiveID(GenreLiveID)
                                
                                tmpstr += (showtitles.group(1)) + "//" + swtitle + "//" + theplot + "//" + genre + "////" + (LiveID)
                                istvshow = True

                            else:
                                if year != 0:
                                    try:
                                        tmpstr += titles.group(1) + ' (' + str(year) + ')' + "//"
                                    except:
                                        tmpstr += titles.group(1) + "//"
                                        pass    
                                else:
                                    tmpstr += titles.group(1) + "//"
                                    
                                album = re.search('"album" *: *"(.*?)"', f)

                                # This is a movie
                                if not album or len(album.group(1)) == 0:
                                    taglines = re.search('"tagline" *: *"(.*?)"', f)
                                    
                                    if taglines != None and len(taglines.group(1)) > 0:
                                        tmpstr += (taglines.group(1)).replace('\\','')
                                    
                                    if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':     
                                    
                                        if imdbnumber == 0:
                                            imdbnumber = self.getIMDBIDmovie(titles.group(1), year)

                                        if genre == 'Unknown':
                                            genre = (self.getGenre(type, titles.group(1), year))

                                        if rating == 'NR':
                                            rating = (self.getRating(type, titles.group(1), year, imdbnumber))

                                    '''if imdbnumber != 0:
                                        Managed = self.cpManaged(titles.group(1), imdbnumber)'''
                                            
                                    GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating]
                                    genre, LiveID = self.packGenreLiveID(GenreLiveID)           
                                    tmpstr += "//" + theplot + "//" + (genre) + "////" + (LiveID)
                                
                                else: #Music
                                    LiveID = 'music|0|0|False|1|NR|'
                                    artist = re.search('"artist" *: *"(.*?)"', f)
                                    tmpstr += album.group(1) + "//" + artist.group(1) + "//" + 'Music' + "////" + LiveID
                            
                            file = unquote(match.group(1))
                            tmpstr = tmpstr
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + file.replace("\\\\", "\\")
                            
                            if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
                                seasoneplist.append([seasonval, epval, tmpstr])                        
                            else:
                                if flag3d == True:
                                    self.movie3Dlist.append(tmpstr)
                                else:
                                    fileList.append(tmpstr)
                        else:
                            self.logError('Video dur = 0, failed to build list')
                    except Exception,e:
                        self.logError('buildFileList, failed...' + str(e))
            else:
                self.logDebug('not a match')

        if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
            seasoneplist.sort(key=lambda seep: seep[1])
            seasoneplist.sort(key=lambda seep: seep[0])

            for seepitem in seasoneplist:
                fileList.append(seepitem[2])

        if filecount == 0:
            self.logDebug(json_folder_detail)

        self.log("buildFileList return")
        return fileList


    def buildMixedFileList(self, dom1, channel, limit):
        self.log('buildMixedFileList')
        fileList = []
        try:
            rules = dom1.getElementsByTagName('rule')
            order = dom1.getElementsByTagName('order')
        except Exception,e:
            self.logError('buildMixedFileList Problem parsing playlist ' + filename)
            xml.close()
            
            return fileList

        for rule in rules:
            rulename = rule.childNodes[0].nodeValue

            if FileAccess.exists(xbmc.translatePath('special://profile/playlists/video/') + rulename):
                FileAccess.copy(xbmc.translatePath('special://profile/playlists/video/') + rulename, MADE_CHAN_LOC + rulename)
                fileList.extend(self.buildFileList(MADE_CHAN_LOC + rulename, channel, limit))
            else:
                fileList.extend(self.buildFileList(GEN_CHAN_LOC + rulename, channel, limit))

        self.log("buildMixedFileList returning")
        return fileList
    
    
    # *Thanks sphere, taken from plugin.video.ted.talks
    # People still using Python <2.7 201303 :(
    def __total_seconds__(self, delta):
        try:
            return delta.total_seconds()
        except AttributeError:
            return float((delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10 ** 6)) / 10 ** 6

            
    def parsePVRDate(self, tmpDate):
        t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
        tmpDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        timestamp = calendar.timegm(tmpDate.timetuple())
        local_dt = datetime.datetime.fromtimestamp(timestamp)
        assert tmpDate.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=tmpDate.microsecond) 
       
       
    def parseXMLTVDate(self, dateString, offset=0):
        if dateString is not None:
            if dateString.find(' ') != -1:
                # remove timezone information
                dateString = dateString[:dateString.find(' ')]
            t = time.strptime(dateString, '%Y%m%d%H%M%S')
            d = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
            d += datetime.timedelta(hours = offset)
            return d
        else:
            return None
    
    
    def xmltv_ok(self, setting3):
        self.log("xmltv_ok, setting3 = " + str(setting3))
        self.xmltvValid = False

        if setting3[0:4] == 'http':
            self.xmltvValid = self.url_ok(setting3)
        elif setting3[0:3] == 'pvr':
            self.xmltvValid = True
        elif setting3 != '':
            self.xmlTvFile = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('xmltvLOC'), str(setting3) +'.xml'))
            if FileAccess.exists(self.xmlTvFile):
                self.xmltvValid = True
        else:
            self.logError("ERROR ERROR ERROR ERROR ERROR")

        self.log("xmltvValid = " + str(self.xmltvValid))
        return self.xmltvValid
    
    
    def url_ok(self, url):
        self.log("url_ok Cache")
        if Cache_Enabled == True:
            try:
                result = bidaily.cacheFunction(self.url_ok_NEW, url)
            except:
                result = self.url_ok_NEW(url)
                pass
        else:
            result = self.url_ok_NEW(url)
        if not result:
            result = False
        return result
   
        
    def url_ok_NEW(self, url):
        self.urlValid = False
        url = unquote(url)
        try: 
            request = urllib2.Request(url)
            request.get_method = lambda : 'HEAD'
            try:
                response = urllib2.urlopen(request)
                self.log("url_ok, INFO: Connected...")
                self.urlValid = True
            except urllib2.HTTPError:
                self.log("url_ok, ERROR: HTTP URL NOT VALID, ERROR: " + str(e))
                self.urlValid = False
        except:
            pass
        self.log("urlValid = " + str(self.urlValid))
        return self.urlValid
    
    
    def trim(self, content, limit, suffix):
        if len(content) <= limit:
            return content
        else:
            return content[:limit].rsplit(' ', 1)[0]+suffix
    
    
    def GetRatingList(self, chtype, chname, channel, fileList):
        self.log("GetRatingList_NEW")
        newFileList = []
        
        if self.youtube_ok != False:
            URL = self.youtube_ok + 'qlRaA8tAfc0'
            Ratings = (['NR','qlRaA8tAfc0'],['R','s0UuXOKjH-w'],['NC-17','Cp40pL0OaiY'],['PG-13','lSg2vT5qQAQ'],['PG','oKrzhhKowlY'],['G','QTKEIFyT4tk'],['18','g6GjgxMtaLA'],['16','zhB_xhL_BXk'],['12','o7_AGpPMHIs'],['6','XAlKSm8D76M'],['0','_YTMglW0yk'])

            for i in range(len(fileList)):
                file = fileList[i]
                lineLST = (fileList[i]).split('movie|')[1]
                mpaa = (lineLST.split('\n')[0]).split('|')[4]
                
                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(channel), "adding Ratings", str(mpaa))
                                
                for i in range(len(Ratings)):
                    rating = Ratings[i]        
                    if mpaa == rating[0]:
                        ID = rating[1]
                        URL = self.youtube_ok + ID
                
                tmpstr = '7,//////Rating////' + 'movie|0|0|False|1|'+str(mpaa)+'|' + '\n' + (URL) + '\n' + '#EXTINF:' + file
                newFileList.append(tmpstr)

        return newFileList
    
    
    # Adapted from Ronie's screensaver.picture.slideshow * https://github.com/XBMC-Addons/screensaver.picture.slideshow/blob/master/resources/lib/utils.py    
    def walk(self, path):     
        VIDEO_TYPES = ('.avi', '.mp4', '.m4v', '.3gp', '.3g2', '.f4v', '.mov', '.mkv', '.flv', '.ts', '.m2ts')
        video = []
        folders = []
        # multipath support
        if path.startswith('multipath://'):
            # get all paths from the multipath
            paths = path[12:-1].split('/')
            for item in paths:
                folders.append(urllib.unquote_plus(item))
        else:
            folders.append(path)
        for folder in folders:
            if FileAccess.exists(xbmc.translatePath(folder)):
                print 'folder'
                # get all files and subfolders
                dirs,files = xbmcvfs.listdir(folder)
                print dirs, files
                # natural sort
                convert = lambda text: int(text) if text.isdigit() else text
                alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
                files.sort(key=alphanum_key)
                for item in files:
                    # filter out all video
                    if os.path.splitext(item)[1].lower() in VIDEO_TYPES:
                        video.append([os.path.join(folder,item), ''])
                for item in dirs:
                    # recursively scan all subfolders
                    video += self.walk(os.path.join(folder,item,'')) # make sure paths end with a slash
        self.log("walk return")
        return video
        
    
    def writeCache(self, thelist, thepath, thefile):
        self.log("writeCache")  
        now = datetime.datetime.today()

        if not FileAccess.exists(os.path.join(thepath)):
            FileAccess.makedirs(os.path.join(thepath))
        
        thefile = uni(thepath + thefile)        
        try:
            fle = FileAccess.open(thefile, "w")
            fle.write("%s\n" % now)
            for item in thelist:
                fle.write("%s\n" % item)
            fle.close()
        except Exception,e:
            pass
        
    
    def readCache(self, thepath, thefile):
        self.log("readCache") 
        thelist = []  
        thefile = (thepath + thefile)
        
        if FileAccess.exists(thefile):
            try:
                fle = FileAccess.open(thefile, "r")
                thelist = fle.readlines()
                LastItem = len(thelist) - 1
                thelist.pop(LastItem)#remove last line (empty line)
                thelist.pop(0)#remove first line (datetime)
                fle.close()
            except Exception,e:
                pass
                
            self.logDebug("readCache, thelist.count = " + str(len(thelist)))
            return thelist
    
    
    def Cache_ok(self, thepath, thefile):
        self.log("Cache_ok")   
        CacheExpired = False
        thefile = (thepath + thefile)
        now = datetime.datetime.today()
        self.logDebug("Cache_ok, now = " + str(now))
        
        if FileAccess.exists(thefile):
            try:
                fle = FileAccess.open(thefile, "r")
                cacheline = fle.readlines()
                cacheDate = str(cacheline[0])
                cacheDate = cacheDate.split('.')[0]
                cacheDate = datetime.datetime.strptime(cacheDate, '%Y-%m-%d %H:%M:%S')
                self.logDebug("Cache_ok, cacheDate = " + str(cacheDate))
                cacheDateEXP = (cacheDate + datetime.timedelta(days=30))
                self.logDebug("Cache_ok, cacheDateEXP = " + str(cacheDateEXP))
                fle.close()  
                
                if now >= cacheDateEXP or len(cacheline) == 2:
                    CacheExpired = True         
            except Exception,e:
                self.logDebug("Cache_ok, exception")
        else:
            CacheExpired = True    
            
        self.log("Cache_ok, CacheExpired = " + str(CacheExpired))
        return CacheExpired
    
     
    def extras(self, setting1, setting2, setting3, setting4, channel):
        self.log("extras")
        limit = self.limit
        showList = []
        
        return showList

    
    def copyanything(self, src, dst):
        try:
            shutil.copytree(src, dst)
        except OSError as exc:
            if exc.errno == errno.ENOTDIR:
                shutil.copy(src, dst)
            else: raise


    def getGenre(self, type, title, year):
        self.log("getGenre")
        genre = 'Unknown'
        
        try:
            self.log("metahandlers")
            self.metaget = metahandlers.MetaData(preparezip=False)
            genre = str(self.metaget.get_meta(type, title)['genre'])
            try:
                genre = str(genre.split(',')[0])
            except Exception as e:
                pass
            try:
                genre = str(genre.split(' / ')[0])
            except Exception as e:
                pass
            if not genre:
                genre = 'Unknown'
        except Exception,e:
            genre = 'Unknown'
            pass

        if genre == 'Unknown':

            if type == 'tvshow':
                try:
                    self.log("tvdb_api")
                    genre = str((self.t[title]['genre']))
                    try:
                        genre = str((genre.split('|'))[1])
                    except:
                        pass
                    if not genre or genre == 'Empty' or genre == 'None':
                        genre = 'Unknown'
                except Exception,e:
                    genre = 'Unknown'
                    pass
            else:
                self.log("tmdb")
                movieInfo = str(self.tmdbAPI.getMovie(title, year))
                try:
                    genre = str(movieInfo['genres'][0])
                    genre = str(genre.split("u'")[3]).replace("'}",'')
                    if not genre or genre == 'Empty' or genre == 'None':
                        genre = 'Unknown'
                except Exception,e:
                    genre = 'Unknown'
                    pass

        genre = genre.replace('NA','Unknown')
        return genre
        
    
    def cleanRating(self, rating):
        self.log("cleanRating")
        rating = rating.replace('Rated ','').replace('US:','').replace('UK:','').replace('Unrated','NR').replace('NotRated','NR').replace('N/A','NR').replace('NA','NR').replace('Approved','NR')
        return rating
        # rating = rating.replace('Unrated','NR').replace('NotRated','NR').replace('N/A','NR').replace('Approved','NR')
    
    
    def getRating(self, type, title, year, imdbid):
        self.log("getRating")
        rating = 'NR'

        try:
            self.log("getRating, metahandlers")     
            self.metaget = metahandlers.MetaData(preparezip=False)
            rating = self.metaget.get_meta(type, title)['mpaa']
            
            if not rating or rating == 'Empty' or rating == 'None':
                rating = 'NR'
        
        except Exception,e:
            pass
        
        if rating == 'NR':
            if type == 'tvshow':
                try:
                    self.log("getRating, tvdb_api")
                    rating = str(self.t[title]['contentrating'])
                    try:
                        rating = rating.replace('|','')
                    except:
                        pass 
                    if not rating or rating == 'Empty' or rating == 'None':
                        rating = 'NR'
                except Exception,e:
                    rating = 'NR'
                    pass
            else:
                if imdbid and imdbid != 0:
                    try:
                        self.log("getRating, tmdb")
                        rating = str(self.tmdbAPI.getMPAA(imdbid)) 
                        if not rating or rating == 'Empty' or rating == 'None':
                            rating = 'NR'
                    except Exception,e:
                        rating = 'NR'
                        pass

        rating = (self.cleanRating(rating))
        print rating
        return rating
        

    def getTVDBID(self, title, year):
        self.log("getTVDBID")
        tvdbid = 0
        if year and year != 0:
            try:
                title = title + ' (' + str(year) + ')'
            except:
                title = title
                pass 
        try:
            self.log("getTVDBID, metahandlers")
            self.metaget = metahandlers.MetaData(preparezip=False)
            tvdbid = self.metaget.get_meta('tvshow', title)['tvdb_id']
            if not tvdbid or tvdbid == 'Empty':
                tvdbid = 0
        except Exception,e:
            tvdbid = 0
            pass

        if tvdbid == 0:
            try:
                self.log("getTVDBID, tvdb_api")
                tvdbid = int(self.t[title]['id'])
            except Exception,e:
                tvdbid = 0
                pass

        if tvdbid == 0:
            try:
                self.log("getTVDBID, getTVDBIDbyIMDB")
                imdbid = self.getIMDBIDtv(title)
                if imdbid:
                    tvdbid = int(self.getTVDBIDbyIMDB(imdbid))
                if not tvdbid or tvdbid == 'Empty':
                    tvdbid = 0
            except Exception,e:
                tvdbid = 0
                pass
        return tvdbid


    def getIMDBIDtv(self, title):
        print 'getIMDBIDtv'
        imdbid = 0

        try:
            self.log("metahandlers")
            self.metaget = metahandlers.MetaData(preparezip=False)
            imdbid = self.metaget.get_meta('tvshow', title)['imdb_id']
        except Exception,e:
            pass

        if not imdbid or imdbid == 0:
            try:
                self.log("tvdb_api")
                imdbid = self.t[title]['imdb_id']
                if not imdbid:
                    imdbid = 0
            except Exception,e:
                pass

        if not imdbid or imdbid == 'None' or imdbid == 'Empty':
            imdbid = 0

        return imdbid


    def getTVDBIDbyIMDB(self, imdbid):
        print 'getTVDBIDbyIMDB'
        tvdbid = 0

        try:
            tvdbid = self.tvdbAPI.getIdByIMDB(imdbid)
        except Exception,e:
            pass

        if not tvdbid or tvdbid == 'None' or tvdbid == 'Empty':
            tvdbid = 0
            
        return tvdbid

                 
    def getIMDBIDmovie(self, showtitle, year):
        print 'getIMDBIDmovie'
        imdbid = 0
        try:
            self.log("metahandlers")
            self.metaget = metahandlers.MetaData(preparezip=False)
            imdbid = (self.metaget.get_meta('movie', showtitle)['imdb_id'])
            if not imdbid or imdbid == 'Empty':
                imdbid = 0
        except Exception,e:
            imdbid = 0
            pass

        if imdbid == 0:
            try:
                self.log("tmdb")
                movieInfo = (self.tmdbAPI.getMovie(showtitle, year))
                imdbid = (movieInfo['imdb_id'])
                if not imdbid or imdbid == 'Empty':
                    imdbid = 0
            except Exception,e:
                imdbid = 0
                pass
        return imdbid
        
    
    def getTVDBIDbyZap2it(self, dd_progid):
        print 'getTVDBIDbyZap2it'
        tvdbid = 0
        
        try:
            tvdbid = self.tvdbAPI.getIdByZap2it(dd_progid)
            if not tvdbid or tvdbid == 'Empty':
                tvdbid = 0
        except Exception,e:
            pass

        print tvdbid
        return tvdbid
        
        
    def getTVINFObySubtitle(self, title, subtitle):
        print 'getTVINFObySubtitle'
        
        try:
            episode = self.t[title].search(subtitle, key = 'episodename')
            # Output example: [<Episode 01x01 - My First Day>]
            episode = str(episode[0])
            episode = episode.split('x')
            seasonNumber = int(episode[0].split('Episode ')[1])
            episodeNumber = int(episode[1].split(' -')[0])
            episodeName = str(episode[1]).split('- ')[1].replace('>','')
            if not episodeName or episodeName == 'Empty':
                episodeName = ''
            if not seasonNumber or seasonNumber == 'Empty':
                seasonNumber = 0    
            if not episodeNumber or episodeNumber == 'Empty':
                episodeNumber = 0
        except Exception,e:
            episodeName = ''
            seasonNumber = 0
            episodeNumber = 0
            pass
            
        return episodeName, seasonNumber, episodeNumber

        
    def getTVINFObySE(self, title, seasonNumber, episodeNumber):
        print 'getTVINFObySE'
        
        try:
            episode = self.t[title][seasonNumber][episodeNumber]
            episodeName = str(episode['episodename'])
            episodeDesc = str(episode['overview'])
            episodeGenre = str(self.t[title]['genre'])
            # Output ex. Comedy|Talk Show|
            episodeGenre = str(episodeGenre)
            try:
                episodeGenre = str(episodeGenre.split('|')[1])
            except:
                pass
        except Exception,e:
            episode = ''
            episodeName = ''
            episodeDesc = ''
            episodeGenre = 'Unknown'
            pass
        
        return episodeName, episodeDesc, episodeGenre
        
        
    def getMovieINFObyTitle(self, title, year):
        print 'getMovieINFObyTitle'
        imdbid = 0
        
        try:
            movieInfo = self.tmdbAPI.getMovie((title), year)
            imdbid = movieInfo['imdb_id']
            try:
                plot = str(movieInfo['overview'])
            except:
                plot = ''
                pass
            try:
                tagline = str(movieInfo['tagline'])
            except:
                tagline = ''
                pass
            try:
                genre = str(movieInfo['genres'][0])
                genre = str((genre.split("u'")[3])).replace("'}",'')
            except:
                genre = 'Unknown'
                pass
                
            if not imdbid or imdbid == 'None' or imdbid == 'Empty':
                imdbid = 0
                
        except Exception,e:
            plot = ''
            tagline = ''
            genre = 'Unknown'
            pass

        return imdbid, plot, tagline, genre
    
    
    # Run rules for a channel
    def runActions(self, action, channel, parameter):
        self.log("runActions " + str(action) + " on channel " + str(channel))
        if channel < 1:
            return

        self.runningActionChannel = channel
        index = 0

        for rule in self.channels[channel - 1].ruleList:
            if rule.actions & action > 0:
                self.runningActionId = index

                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "processing rule " + str(index + 1), '')

                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter


    def threadPause(self):
        if threading.activeCount() > 1:
            while self.threadPaused == True and self.myOverlay.isExiting == False:
                xbmc.sleep(int(self.sleepTime))

            # This will fail when using config.py
            try:
                if self.myOverlay.isExiting == True:
                    self.log("IsExiting")
                    return False
            except Exception,e:
                pass
                
        return True


    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)

        if (mydir.find(":")):
            mydir = mydir.replace("\\", "\\\\")
        return mydir


    def getSmartPlaylistType(self, dom):
        self.log('getSmartPlaylistType')

        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            return pltype[0].attributes['type'].value
        except Exception,e:
            self.logError("Unable to get the playlist type.")
            return ''
            
        
    '''def findZap2itID(self, CHname, filename):
        self.log("findZap2itID, CHname = " + CHname)
        orgCHname = CHname
        XMLTVMatchlst = []
        sorted_XMLTVMatchlst = []
        found = False
        try:
            if filename == 'pvr':
                self.log("findZap2itID, pvr backend")
                if not self.cached_json_detailed_xmltvChannels_pvr:
                    self.log("findZap2itID, no cached_json_detailed_xmltvChannels")
                    json_query = uni('{"jsonrpc":"2.0","method":"PVR.GetChannels","params":{"channelgroupid":2}, "id": 1 }')
                    json_detail = self.sendJSON(json_query)
                    self.cached_json_detailed_xmltvChannels_pvr = re.compile( "{(.*?)}", re.DOTALL ).findall(json_detail)
                file_detail = self.cached_json_detailed_xmltvChannels_pvr
                
                for f in file_detail:
                    CHids = re.search('"channelid" *: *(.*?),', f)
                    dnames = re.search('"label" *: *"(.*?)"', f)
                    if CHids and dnames:
                        CHid = CHids.group(1)
                        dname = dnames.group(1)
                        
                        CHname = CHname.replace('-DT','DT').replace(' DT','DT').replace('DT','').replace('-HD','HD').replace(' HD','HD').replace('HD','').replace('-SD','SD').replace(' SD','SD').replace('SD','')
                        matchLST = [CHname.upper(), 'W'+CHname.upper(), orgCHname, 'W'+orgCHname.upper()]
                        self.logDebug("findZap2itID, Cleaned CHname = " + CHname)
                        self.logDebug("findZap2itID, matchLST = " + str(matchLST))

                        dnameID = dname + ' : ' + CHid
                        self.logDebug("findZap2itID, dnameID = " + str(dnameID))
                        XMLTVMatchlst.append(dnameID)
            else:
                if filename[0:4] == 'http':
                    self.log("findZap2itID, filename http = " + filename)
                    if not self.cached_json_detailed_xmltvChannels_http:
                        self.log("findZap2itID, no cached_json_detailed_xmltvChannels")
                        self.cached_json_detailed_xmltvChannels_http = str(xmltv.read_channels(Open_URL(filename)))
                    json_details = self.cached_json_detailed_xmltvChannels_http
                else:
                    self.log("findZap2itID, filename local = " + filename)
                    fle = FileAccess.open(filename, "r")
                    if not self.cached_json_detailed_xmltvChannels_local:
                        self.log("findZap2itID, no cached_json_detailed_xmltvChannels")
                        self.cached_json_detailed_xmltvChannels_local = str(xmltv.read_channels(fle))
                    json_details = self.cached_json_detailed_xmltvChannels_local
                
                xbmc.sleep(100)
                fle.close()
                file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_details)
                
                try:
                    CHnum = CHname.split(' ')[0]
                    CHname = CHname.split(' ')[1]
                except:
                    CHnum = ''
                    pass
                
                CHname = CHname.replace('-DT','DT').replace(' DT','DT').replace('DT','').replace('-HD','HD').replace(' HD','HD').replace('HD','').replace('-SD','SD').replace(' SD','SD').replace('SD','')
                matchLST = [CHname.upper(), 'W'+CHname.upper(), orgCHname, 'W'+orgCHname.upper()]
                self.logDebug("findZap2itID, Cleaned CHname = " + CHname)
                self.logDebug("findZap2itID, matchLST = " + str(matchLST))
                
                for f in (file_detail):
                    found = False
                    dnameID = []
                    CHid = '0'
                    match = re.search("'display-name' *: *\[(.*?)\]", f)
                    id = re.search("'id': (.+)", f)
                    
                    if match != None and len(match.group(1)) > 0 and id != None and len(id.group(1)) > 0:
                        dnames = match.group(1)
                        dnames = (dnames.replace("('",'').replace("', '')",'')).split(', ')
                        CHid = (id.group(1)).replace("'",'')
                        
                        for i in range(len(dnames)):
                            dname = dnames[i].replace('-DT','DT').replace(' DT','DT').replace('DT','').replace('-HD','HD').replace(' HD','HD').replace('HD','').replace('-SD','SD').replace(' SD','SD').replace('SD','').replace("'",'').replace(')','')
                            dnameID = dname + ' : ' + CHid
                            XMLTVMatchlst.append(dnameID)
                            
            sorted_XMLTVMatchlst = sorted_nicely(XMLTVMatchlst)
            self.logDebug("findZap2itID, sorted_XMLTVMatchlst = " + str(sorted_XMLTVMatchlst))
            
            for n in range(len(sorted_XMLTVMatchlst)):
                CHid = '0'
                dnameID = sorted_XMLTVMatchlst[n]
                dname = dnameID.split(' : ')[0]
                CHid = dnameID.split(' : ')[1]
                
                if dname.upper() in matchLST: 
                    self.log("findZap2itID, Match Found: " + str(CHname.upper()) +' == '+ str(dname.upper()) + ' ' + str(CHid))  
                    found = True
                    return orgCHname, CHid
                        
            if not found:
                select = selectDialog(sorted_XMLTVMatchlst, 'Select matching id to [B]%s[/B]' % orgCHname)
                dnameID = sorted_XMLTVMatchlst[select]
                CHid = dnameID.split(' : ')[1]
                return orgCHname, CHid
            
        except Exception:
            self.logError("Error with findZap2itID")'''
    
    
    def CleanLabels(self, text):
        self.logDebug('CleanLabels, in = ' + text)
        text = re.sub('\[COLOR (.+?)\]', '', text)
        text = re.sub('\[/COLOR\]', '', text)
        text = re.sub('\[COLOR=(.+?)\]', '', text)
        text = re.sub('\[color (.+?)\]', '', text)
        text = re.sub('\[/color\]', '', text)
        text = re.sub('\[Color=(.+?)\]', '', text)
        text = re.sub('\[/Color\]', '', text)
        text = text.replace("\ ",'')
        text = text.replace("\\",'')
        text = text.replace("/ ",'')
        text = text.replace("//",'')
        text = text.replace("[B]",'')
        text = text.replace("[/B]",'')
        text = text.replace("[HD]",'')
        text = text.replace("[CC]",'')
        text = text.replace("[Cc]",'')
        text = text.replace("(SUB)",'')
        text = text.replace("(DUB)",'')
        text = text.replace("\n", "")
        text = text.replace("\r", "")
        text = (text.title()).replace("'S","'s")
        self.logDebug('CleanLabels, out = ' + text)
        return text
    
    
    def GrabLogo(self, url, title):
        self.log("GrabLogo")
        url = ''
        LogoFile = ''
        try:
            if REAL_SETTINGS.getSetting('ChannelLogoFolder') != '':
                LogoPath = xbmc.translatePath(REAL_SETTINGS.getSetting('ChannelLogoFolder'))
                LogoFile = os.path.join(LogoPath, title[0:18] + '.png')
                url = url.replace('.png/','.png').replace('.jpg/','.jpg')
                if not FileAccess.exists(LogoFile):
                    if url.startswith('http'):
                        Download_URL(url, LogoFile)
                    elif url.startswith('image'):
                        url = unquote(url).replace("image://",'')
                        if url.startswith('http'):
                            Download_URL(url, LogoFile)
            print url, LogoFile
        except:
            pass

            
    def XBMCversion(self):
        json_query = uni('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
        json_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_detail)
        
        for f in detail:
            majors = re.search('"major" *: *([0-9]*?),', f)
            if majors:
                major = int(majors.group(1))

        if major == 13:
            version = 'Gotham'
        elif major < 13:
            version = 'Frodo'
        else:
            version = 'Helix'
        
        self.log('Kodi version = ' + version)
        return version
    
    
    def fillFavourites(self):
        self.log('fillFavourites')
        json_query = uni('{"jsonrpc":"2.0","method":"Favourites.GetFavourites","params":{"properties":["path"]},"id":3}')
        json_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_detail)
        TMPfavouritesList = []

        for f in detail:
            paths = re.search('"path" *: *"(.*?)",', f)
            names = re.search('"title" *: *"(.*?)",', f)
            types = re.search('"type" *: *"(.*?)"', f)
            if types != None and len(types.group(1)) > 0:
                type = types.group(1)
                if type == 'media' and names and paths:
                    name = self.CleanLabels(names.group(1))
                    path = paths.group(1)
                    TMPfavouritesList.append(name+','+path)  

        SortedFavouritesList = sorted_nicely(TMPfavouritesList)
        for i in range(len(SortedFavouritesList)):  
            self.FavouritesNameList.append((SortedFavouritesList[i]).split(',')[0])
            self.FavouritesPathList.append((SortedFavouritesList[i]).split(',')[1])