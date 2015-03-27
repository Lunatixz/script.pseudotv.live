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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random, traceback

from ChannelList import ChannelList
from Channel import Channel
from Globals import *

class ChannelListThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.myOverlay = None
        sys.setcheckinterval(25)
        self.chanlist = ChannelList()
        self.paused = False
        self.fullUpdating = True

        
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelListThread: ' + msg, level)


    def run(self):
        self.log("Starting")
        self.chanlist.exitThread = False
        self.chanlist.readConfig()
        self.chanlist.sleepTime = 1

        if self.myOverlay == None:
            self.log("Overlay not defined. Exiting.")
            return
            
        self.chanlist.myOverlay = self.myOverlay
        self.fullUpdating = (self.myOverlay.backgroundUpdating == 0)
        validchannels = 0

        for i in range(self.myOverlay.maxChannels):
            self.chanlist.channels.append(Channel())

            if self.myOverlay.channels[i].isValid:
                validchannels += 1
                
        # Don't load invalid channels if minimum threading mode is on
        if self.fullUpdating and self.myOverlay.isMaster:
            if validchannels < self.chanlist.enteredChannelCount:
                title = 'PseudoTV Live, Background Loading...'
                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s)' % (title, 4000 , THUMB))

            for i in range(self.myOverlay.maxChannels):
                if self.myOverlay.channels[i].isValid == False:
                    while True:
                        if self.myOverlay.isExiting:
                            self.log("Closing thread")
                            return

                        time.sleep(1)

                        if self.paused == False:
                            break

                    self.chanlist.channels[i].setAccessTime(self.myOverlay.channels[i].lastAccessTime)

                    try:
                        if self.chanlist.setupChannel(i + 1, True, True, False) == True:
                            while self.paused:
                                if self.myOverlay.isExiting:
                                    self.log("IsExiting")
                                    return

                                time.sleep(1)

                            self.myOverlay.channels[i] = self.chanlist.channels[i]

                            if self.myOverlay.channels[i].isValid == True:
                                title = "PseudoTV Live, Channel " + str(i + 1) + " Added"
                                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s)' % (title, 4000, THUMB))
                                
                    except Exception,e:
                        self.log("Unknown Channel Creation Exception", xbmc.LOGERROR)
                        self.log(traceback.format_exc(), xbmc.LOGERROR)
                        return

        REAL_SETTINGS.setSetting('ForceChannelReset', 'false')
        self.chanlist.sleepTime = 3

        if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true":
            InfoTimer = INFOBAR_TIMER[int(REAL_SETTINGS.getSetting('InfoTimer'))]
            self.myOverlay.ArtServiceThread = threading.Timer(float(InfoTimer), self.myOverlay.ArtService)
            self.myOverlay.ArtServiceThread.name = "ArtServiceThread"
            self.myOverlay.ArtServiceThread.start()

        if REAL_SETTINGS.getSetting("EnableSettop") == "true":
            self.log('onInit, Settop Enabled')
            self.myOverlay.channelThread_Timer = threading.Timer(float(SETTOP_REFRESH), self.myOverlay.Settop)
            self.myOverlay.channelThread_Timer.name = "channelThread_Timer"
            self.myOverlay.channelThread_Timer.start() 
            
        while True:
            for i in range(self.myOverlay.maxChannels):
                modified = True

                while modified == True and self.myOverlay.channels[i].getTotalDuration() < PREP_CHANNEL_TIME and self.myOverlay.channels[i].Playlist.size() < 16288:
                    # If minimum updating is on, don't attempt to load invalid channels
                    if self.fullUpdating == False and self.myOverlay.channels[i].isValid == False and self.myOverlay.isMaster:
                        break

                    modified = False

                    if self.myOverlay.isExiting:
                        self.log("Closing thread")
                        return

                    time.sleep(2)
                    try:
                        curtotal = self.myOverlay.channels[i].getTotalDuration()
                        if self.myOverlay.isMaster:
                            if curtotal > 0:
                                # When appending, many of the channel variables aren't set, so copy them over.
                                # This needs to be done before setup since a rule may use one of the values.
                                # It also needs to be done after since one of them may have changed while being setup.
                                self.chanlist.channels[i].playlistPosition = self.myOverlay.channels[i].playlistPosition
                                self.chanlist.channels[i].showTimeOffset = self.myOverlay.channels[i].showTimeOffset
                                self.chanlist.channels[i].lastAccessTime = self.myOverlay.channels[i].lastAccessTime
                                self.chanlist.channels[i].totalTimePlayed = self.myOverlay.channels[i].totalTimePlayed
                                self.chanlist.channels[i].isPaused = self.myOverlay.channels[i].isPaused
                                self.chanlist.channels[i].mode = self.myOverlay.channels[i].mode
                                # Only allow appending valid channels, don't allow erasing them
                                
                                try:
                                    self.chanlist.setupChannel(i + 1, True, False, True)
                                except Exception,e:
                                    self.log("Unknown Channel Appending Exception", xbmc.LOGERROR)
                                    self.log(traceback.format_exc(), xbmc.LOGERROR)
                                    return

                                self.chanlist.channels[i].playlistPosition = self.myOverlay.channels[i].playlistPosition
                                self.chanlist.channels[i].showTimeOffset = self.myOverlay.channels[i].showTimeOffset
                                self.chanlist.channels[i].lastAccessTime = self.myOverlay.channels[i].lastAccessTime
                                self.chanlist.channels[i].totalTimePlayed = self.myOverlay.channels[i].totalTimePlayed
                                self.chanlist.channels[i].isPaused = self.myOverlay.channels[i].isPaused
                                self.chanlist.channels[i].mode = self.myOverlay.channels[i].mode
                            else:
                                try:
                                    self.chanlist.setupChannel(i + 1, True, True, False)
                                except Exception,e:
                                    self.log("Unknown Channel Modification Exception", xbmc.LOGERROR)
                                    self.log(traceback.format_exc(), xbmc.LOGERROR)
                                    return
                        else:
                            try:
                                # We're not master, so no modifications...just try and load the channel
                                self.chanlist.setupChannel(i + 1, True, False, False)
                            except Exception,e:
                                self.log("Unknown Channel Loading Exception", xbmc.LOGERROR)
                                self.log(traceback.format_exc(), xbmc.LOGERROR)
                                return

                        self.myOverlay.channels[i] = self.chanlist.channels[i]

                        if self.myOverlay.isMaster:
                            ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(self.myOverlay.channels[i].totalTimePlayed))

                        if self.myOverlay.channels[i].getTotalDuration() > curtotal and self.myOverlay.isMaster:
                            modified = True

                        # A do-while loop for the paused state
                        while True:
                            if self.myOverlay.isExiting:
                                self.log("Closing thread")
                                return

                            time.sleep(2)

                            if self.paused == False:
                                break
                    except:
                        pass
                timeslept = 0

            if self.fullUpdating == False and self.myOverlay.isMaster:
                return

            # If we're master, wait 30 minutes in between checks.  If not, wait 5 minutes.
            while (timeslept < 1800 and self.myOverlay.isMaster == True) or (timeslept < 300 and self.myOverlay.isMaster == False):
                if self.myOverlay.isExiting:
                    self.log("IsExiting")
                    return

                time.sleep(2)
                timeslept += 2

        self.log("All channels up to date.  Exiting thread.")
        
        
    def pause(self):
        self.paused = True
        self.chanlist.threadPaused = True


    def unpause(self):
        self.paused = False
        self.chanlist.threadPaused = False
