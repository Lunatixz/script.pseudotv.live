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

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import subprocess, os, sys, re
import time, threading, datetime, _strptime, traceback
import urllib, urllib2

from Playlist import Playlist
from Globals import *
from Channel import Channel
from ChannelList import ChannelList
from FileAccess import FileAccess
from xml.etree import ElementTree as ET
from Artdownloader import *
from utils import *

try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo-web/submit.php'
except:
    pass
      
class EPGWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.log('__init__')
        self.focusRow = 0
        self.focusIndex = 0
        self.focusTime = 0
        self.focusEndTime = 0
        self.shownTime = 0
        self.centerChannel = 0
        self.rowCount = 6  
        self.channelButtons = [None] * self.rowCount
        self.buttonCache = []
        self.buttonCount = 0
        self.actionSemaphore = threading.BoundedSemaphore()
        self.lastActionTime = time.time()
        self.channelLogos = ''
        self.textcolor = "FFFFFFFF"
        self.focusedcolor = "FF7d7d7d"
        self.clockMode = 0
        self.textfont  = "font14"
        self.startup = time.time()
        self.showingInfo = False
        self.infoOffset = 0
        self.infoOffsetV = 0
        self.showSeasonEpisode = REAL_SETTINGS.getSetting("ShowSeEp") == "true"
        self.PVRTimeOffset = 0
        self.Artdownloader = Artdownloader()
        self.inputChannel = -1
        self.channelLabel = []    
        self.channelbugcolor = CHANBUG_COLOR
        self.chanlist = ChannelList()
        self.showingContext = False
        self.timeButtonNoFocus = MEDIA_LOC + TIME_BUTTON
        self.timeButtonBar = MEDIA_LOC + TIME_BAR
        self.ButtonContextB = MEDIA_LOC + BUTTON_GAUSS_CONTEXT
        self.ButtonContextF = MEDIA_LOC + BUTTON_FOCUS_CONTEXT
        self.ButtonContextC = MEDIA_LOC + BUTTON_NO_FOCUS_CONTEXT
        
        for i in range(self.rowCount):
            self.channelButtons[i] = []
            
        self.clockMode = ADDON_SETTINGS.getSetting("ClockMode")
        self.toRemove = []


    def onFocus(self, controlid):
        pass


    # set the time labels
    def setTimeLabels(self, thetime):
        now = datetime.datetime.fromtimestamp(thetime)
        self.getControl(104).setLabel(now.strftime('%A, %b %d'))
        delta = datetime.timedelta(minutes=30)

        for i in range(3):
            if self.clockMode == "0":
                self.getControl(101 + i).setLabel(now.strftime("%I:%M%p").lower())
            else:
                self.getControl(101 + i).setLabel(now.strftime("%H:%M"))
            now = now + delta
        self.log('setTimeLabels return')
            

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('EPGWindow: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('EPGWindow: ' + msg, level)
                
    
    def onInit(self):
        self.log('onInit')
        now = datetime.datetime.now()        
        if self.clockMode == "0":
            timeex = now.strftime("%I:%M%p").lower()
        else:
            timeex = now.strftime("%H:%M")

        timetx, timety = self.getControl(106).getPosition()
        timetw = self.getControl(106).getWidth()
        timeth = self.getControl(106).getHeight()
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
            
        self.textureButtonFocus = MEDIA_LOC + BUTTON_FOCUS
        self.textureButtonNoFocus = MEDIA_LOC + BUTTON_NO_FOCUS
        self.textureButtonFocusAlt = MEDIA_LOC + BUTTON_FOCUS_ALT
        self.textureButtonNoFocusAlt = MEDIA_LOC + BUTTON_NO_FOCUS_ALT
        self.currentTime = xbmcgui.ControlButton(timetx, timety, timetw, timeth, timeex, font='font12', noFocusTexture=self.timeButtonNoFocus)
        self.currentTimeBar = xbmcgui.ControlImage(timex, timey, timew, timeh, self.timeButtonBar) 
        self.addControl(self.currentTime)
        self.addControl(self.currentTimeBar)
        self.curchannelIndex = []
        
        try:
            textcolor = int(self.getControl(100).getLabel(), 16)            
            if textcolor > 0:
                self.textcolor = hex(textcolor)[2:]
            
            focusedcolor = int(self.getControl(99).getLabel(), 16)
            if focusedcolor > 0:
                self.focusedcolor = hex(focusedcolor)[2:]
            
            self.textfont = self.getControl(105).getLabel()
        except:
            pass

        try:
            self.getControl(508).setImage(THUMB)
            self.getControl(510).setImage(THUMB)
        except:
            pass
            
        try:
            if self.setChannelButtons(time.time(), self.MyOverlayWindow.currentChannel) == False:
                self.log('Unable to add channel buttons')
                return

            curtime = time.time()
            self.focusIndex = -1
            basex, basey = self.getControl(113).getPosition()
            baseh = self.getControl(113).getHeight()
            basew = self.getControl(113).getWidth()

            # set the button that corresponds to the currently playing show
            for i in range(len(self.channelButtons[2])):
                left, top = self.channelButtons[2][i].getPosition()
                width = self.channelButtons[2][i].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))

                if curtime >= starttime and curtime <= endtime:
                    self.focusIndex = i
                    self.setFocus(self.channelButtons[2][i])
                    self.focusTime = int(time.time())
                    self.focusEndTime = endtime
                    break

            # If nothing was highlighted, just select the first button
            if self.focusIndex == -1:
                self.focusIndex = 0
                self.setFocus(self.channelButtons[2][0])
                left, top = self.channelButtons[2][0].getPosition()
                width = self.channelButtons[2][0].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                endtime = starttime + (width / (basew / 5400.0))
                self.focusTime = int(starttime + 30)
                self.focusEndTime = endtime
            self.focusRow = 2
            self.setShowInfo()
        except Exception,e:
            self.log("Unknown EPG Initialization Exception " + str(e), xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)          
            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)
            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return
        
        # Artwork types
        try:
            self.Arttype1 = str(self.getControl(507).getLabel())
            self.type1EXT = EXTtype(self.Arttype1)
            REAL_SETTINGS.setSetting("type1EXT_EPG",self.type1EXT)
        except:
            pass
        try:
            self.Arttype2 = str(self.getControl(509).getLabel())
            self.type2EXT = EXTtype(self.Arttype2)
            REAL_SETTINGS.setSetting("type2EXT_EPG",self.type2EXT)
        except:
            pass
            
        #Check if VideoWindow Patch found, Toggle Visible.
        try:
            if self.MyOverlayWindow.VideoWindow == True:
                self.log('VideoWindow = True')
                self.getControl(523).setVisible(True)
            else:
                self.log('VideoWindow = False')
                self.getControl(523).setVisible(False)
        except:
            self.log('VideoWindow Failed!')
            self.getControl(523).setVisible(False)
            pass
            
        try:
            for i in range(3):
                self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse = self.channelbugcolor))
                self.addControl(self.channelLabel[i])
                self.channelLabel[i].setVisible(False)
            self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
        except:
            pass
            
        if getProperty("PTVL.FEEDtoggle") == "true":
            self.getControl(131).setVisible(True)
        else:
            self.getControl(131).setVisible(False)
        self.log('onInit return')

        
    # setup all channel buttons for a given time
    def setChannelButtons(self, starttime, curchannel, singlerow = -1):
        self.log('setChannelButtons ' + str(starttime) + ', ' + str(curchannel))
        self.centerChannel = self.MyOverlayWindow.fixChannel(curchannel)
        
        # This is done twice to guarantee we go back 2 channels.  If the previous 2 channels
        # aren't valid, then doing a fix on curchannel - 2 may result in going back only
        # a single valid channel.
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        curchannel = self.MyOverlayWindow.fixChannel(curchannel - 1, False)
        starttime = self.roundToHalfHour(int(starttime))
        self.setTimeLabels(starttime)
        self.shownTime = starttime
        basex, basey = self.getControl(111).getPosition()
        basew = self.getControl(111).getWidth()
        tmpx, tmpy =  self.getControl(110 + self.rowCount).getPosition()
        
        timetx, timety = self.getControl(106).getPosition()
        timetw = self.getControl(106).getWidth()
        timeth = self.getControl(106).getHeight()
        timex, timey = self.getControl(120).getPosition()
        timew = self.getControl(120).getWidth()
        timeh = self.getControl(120).getHeight()
        
        basecur = curchannel
        self.toRemove.append(self.currentTime)
        self.toRemove.append(self.currentTimeBar)
        myadds = []
        
        for i in range(self.rowCount):
            if singlerow == -1 or singlerow == i:
                self.setButtons(starttime, basecur, i)
                myadds.extend(self.channelButtons[i])
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        basecur = curchannel

        for i in range(self.rowCount):
            self.getControl(301 + i).setLabel(self.MyOverlayWindow.channels[basecur - 1].name)
            basecur = self.MyOverlayWindow.fixChannel(basecur + 1)

        for i in range(self.rowCount): 
            try:
                self.getControl(311 + i).setLabel(str(curchannel))
            except:
                pass

            try:        
                if REAL_SETTINGS.getSetting("EPGTextEnable") == "0":
                    try:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
                    except:
                        self.log("Unknown EPG Chtype Exception", xbmc.LOGERROR)
                        chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
                        pass  
                    # chname = (self.MyOverlayWindow.channels[curchannel - 1].name)
                    # plpos = self.determinePlaylistPosAtTime(starttime, (curchannel - 1))
                    # mediapath = ascii(self.MyOverlayWindow.channels[curchannel - 1].getItemFilename(plpos))
                    # mpath = self.MyOverlayWindow.GetMpath(mediapath)
                    # setImage = self.Artdownloader.FindLogo_NEW(chtype, chname, mpath)
                    # self.getControl(321 + i).setImage(setImage)
                    self.getControl(321 + i).setImage(self.channelLogos + ascii(self.MyOverlayWindow.channels[curchannel - 1].name) + ".png")
                    if not FileAccess.exists(self.channelLogos + ascii(self.MyOverlayWindow.channels[curchannel - 1].name) + ".png"):
                        self.getControl(321 + i).setImage('NA.png')
                else:
                    self.getControl(321 + i).setImage('NA.png')
            except:
                pass

            curchannel = self.MyOverlayWindow.fixChannel(curchannel + 1)
   
        if time.time() >= starttime and time.time() < starttime + 5400:
            dif = int((starttime + 5400 - time.time())) 
            self.currentTime.setPosition(int((basex + basew - 2) - (dif * (basew / 5400.0))), timety)
            self.currentTimeBar.setPosition(int((basex + basew - 2) - (dif * (basew / 5400.0))), timey)
        else:
            if time.time() < starttime:
                self.currentTime.setPosition(-1800, timety)
                self.currentTimeBar.setPosition(basex + 2, timey)
            else:
                self.currentTime.setPosition(-1800, timety)
                self.currentTimeBar.setPosition(basex + basew - 2 - timew, timey)

        myadds.append(self.currentTime)
        myadds.append(self.currentTimeBar)
        
        # Update timebutton
        now = datetime.datetime.now()        
        if self.clockMode == "0":
            timeex = now.strftime("%I:%M%p").lower()
        else:
            timeex = now.strftime("%H:%M")
        self.currentTime.setLabel(timeex)
        
        # Set backtime focus width
        TimeBX, TimeBY = self.currentTimeBar.getPosition()
        PFadeX, PFadeY = self.getControl(119).getPosition()
        self.getControl(119).setWidth(TimeBX-PFadeX)
        self.getControl(118).setPosition(TimeBX, PFadeY)
        self.getControl(118).setWidth(1920-TimeBX)

        Time1X, Time1Y = self.getControl(101).getPosition()
        Time2X, Time2Y = self.getControl(102).getPosition()
        Time3X, Time3Y = self.getControl(103).getPosition()
        TimeBW = int(self.currentTime.getWidth())
        Time1W = int(self.getControl(101).getWidth())
        Time2W = int(self.getControl(102).getWidth())
        Time3W = int(self.getControl(103).getWidth())
        
        # Arrow color
        if TimeBX > Time3X:
            self.getControl(109).setColorDiffuse('0x'+self.focusedcolor)
        else:
            self.getControl(109).setColorDiffuse('0x'+self.textcolor)
        if TimeBX < Time1X:
            self.getControl(110).setColorDiffuse('0x'+self.focusedcolor)
        else:
            self.getControl(110).setColorDiffuse('0x'+self.textcolor)
         
        # Hide timebutton when near timebar
        self.getControl(101).setVisible(True)
        if TimeBX < Time1X or TimeBX > Time1X + Time1W:
            self.getControl(101).setVisible(True)
        else:
            self.getControl(101).setVisible(False)
            
        self.getControl(102).setVisible(True)
        if TimeBX + TimeBW < Time2X or TimeBX > Time2X + Time2W:
            self.getControl(102).setVisible(True)
        else:
            self.getControl(102).setVisible(False)
            
        self.getControl(103).setVisible(True)            
        if TimeBX + TimeBW < Time3X or TimeBX > Time3X + Time3W:
            self.getControl(103).setVisible(True)
        else:
            self.getControl(103).setVisible(False)
            
        try:
            self.removeControls(self.toRemove)
        except:
            for cntrl in self.toRemove:
                try:
                    self.removeControl(cntrl)
                except:
                    pass
        try:
            self.addControls(myadds)
            self.toRemove = []
            self.log('setChannelButtons return')
        except:
            xbmc.log('self.addControls(myadds) in use')
            pass
        
        print 'self.curchannelIndex', str(self.curchannelIndex)

    # round the given time down to the nearest half hour
    def roundToHalfHour(self, thetime):
        n = datetime.datetime.fromtimestamp(thetime)
        delta = datetime.timedelta(minutes=30)

        if n.minute > 29:
            n = n.replace(minute=30, second=0, microsecond=0)
        else:
            n = n.replace(minute=0, second=0, microsecond=0)

        return time.mktime(n.timetuple())

        
    def GetEPGtype(self, genre):
        #rewrite as option switch, dict? faster? time function todo?
        if genre in COLOR_RED_TYPE:
            return (EPGGENRE_LOC + 'COLOR_RED.png')
        elif genre in COLOR_GREEN_TYPE:
            return (EPGGENRE_LOC + 'COLOR_GREEN.png')
        elif genre in COLOR_mdGREEN_TYPE:
            return (EPGGENRE_LOC + 'COLOR_mdGREEN.png')
        elif genre in COLOR_BLUE_TYPE:
            return (EPGGENRE_LOC + 'COLOR_BLUE.png')
        elif genre in COLOR_ltBLUE_TYPE:
            return (EPGGENRE_LOC + 'COLOR_ltBLUE.png')
        elif genre in COLOR_CYAN_TYPE:
            return (EPGGENRE_LOC + 'COLOR_CYAN.png')
        elif genre in COLOR_ltCYAN_TYPE:
            return (EPGGENRE_LOC + 'COLOR_ltCYAN.png')
        elif genre in COLOR_PURPLE_TYPE:
            return (EPGGENRE_LOC + 'COLOR_PURPLE.png')
        elif genre in COLOR_ltPURPLE_TYPE:
            return (EPGGENRE_LOC + 'COLOR_ltPURPLE.png')
        elif genre in COLOR_ORANGE_TYPE:
            return (EPGGENRE_LOC + 'COLOR_ORANGE.png')
        elif genre in COLOR_YELLOW_TYPE:
            return (EPGGENRE_LOC + 'COLOR_YELLOW.png')
        elif genre in COLOR_GRAY_TYPE:
            return (EPGGENRE_LOC + 'COLOR_GRAY.png')
        else:#Unknown or COLOR_ltGRAY_TYPE
            return (EPGGENRE_LOC + 'COLOR_ltGRAY.png') 
        

    # create the buttons for the specified channel in the given row
    def setButtons(self, starttime, curchannel, row):
        self.logDebug('setButtons ' + str(starttime) + ", " + str(curchannel) + ", " + str(row))
        Filtered = False
        try:
            curchannel = self.MyOverlayWindow.fixChannel(curchannel)
            basex, basey = self.getControl(111 + row).getPosition()
            baseh = self.getControl(111 + row).getHeight()
            basew = self.getControl(111 + row).getWidth()
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
            except:
                self.log("Unknown EPG Chtype Exception", xbmc.LOGERROR)
                chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(curchannel) + '_type'))
                pass

            chname = ascii(self.MyOverlayWindow.channels[curchannel - 1].name)
            
            if xbmc.Player().isPlaying() == False:
                self.log('No video is playing, not adding buttons')
                self.closeEPG()
                return False

            # Backup all of the buttons to an array
            self.toRemove.extend(self.channelButtons[row])
            del self.channelButtons[row][:]

            # if the channel is paused, then only 1 button needed
            nowDate = datetime.datetime.now()
            playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                        


            if self.MyOverlayWindow.channels[curchannel - 1].isPaused:
                self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].getCurrentTitle() + " (paused)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
            elif chname in BYPASS_EPG:
                self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].name, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
            elif chtype >= 10 and self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < 900: #Under 15mins "Stacked"
                self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].name + " (stacked)", focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
            else:
                # Find the show that was running at the given time
                # Use the current time and show offset to calculate it
                # At timedif time, channelShowPosition was playing at channelTimes
                # The only way this isn't true is if the current channel is curchannel since
                # it could have been fast forwarded or rewinded (rewound)?
                if curchannel == self.MyOverlayWindow.currentChannel:
                    #Live TV pull date from the playlist entry
                    if chtype == 8 and len(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)) > 0:
                        #episodetitle is actually the start time of each show that the playlist gets from channellist.py
                        tmpDate = self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)
                        
                        try:#sloppy fix, for threading issue with strptime.
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        except:
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            pass
                            
                        epochBeginDate = time.mktime(t)
                        videotime = time.time() - epochBeginDate
                        reftime = time.time()
                    else:
                        playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                        videotime = xbmc.Player().getTime()
                        reftime = time.time()        

                else:
                    #Live TV pull date from the playlist entry
                    if chtype == 8 and len(self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)) > 0:
                        playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition
                        #episodetitle is actually the start time of each show that the playlist gets from channellist.py
                        tmpDate = self.MyOverlayWindow.channels[curchannel - 1].getItemtimestamp(playlistpos)

                        try:#sloppy fix, for threading issue with strptime.
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        except:
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            pass
                            
                        epochBeginDate = time.mktime(t)
                        #loop to ensure we get the current show in the playlist
                        while epochBeginDate + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) <  time.time():
                            epochBeginDate += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                            playlistpos = self.MyOverlayWindow.channels[curchannel - 1].fixPlaylistIndex(playlistpos + 1)
                        videotime = time.time() - epochBeginDate
                        reftime = time.time()
                    else:
                         #everyotherchannel epg
                        playlistpos = self.MyOverlayWindow.channels[curchannel - 1].playlistPosition
                        videotime = self.MyOverlayWindow.channels[curchannel - 1].showTimeOffset
                        reftime = self.MyOverlayWindow.channels[curchannel - 1].lastAccessTime

                    self.logDebug('videotime  & reftime  + starttime + channel === ' + str(videotime) + ', ' + str(reftime) + ', ' + str(starttime) + ', ' + str(curchannel))

                # normalize reftime to the beginning of the video
                reftime -= videotime

                while reftime > starttime:
                    playlistpos -= 1
                    # No need to check bounds on the playlistpos, the duration function makes sure it is correct
                    reftime -= self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)

                while reftime + self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < starttime:
                    reftime += self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    playlistpos += 1

                # create a button for each show that runs in the next hour and a half
                endtime = starttime + 5400
                totaltime = 0
                totalloops = 0
                
                while reftime < endtime and totalloops < 1000:
                    xpos = int(basex + (totaltime * (basew / 5400.0)))
                    tmpdur = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos)
                    shouldskip = False

                    # this should only happen the first time through this loop
                    # it shows the small portion of the show before the current one
                    if reftime < starttime:
                        tmpdur -= starttime - reftime
                        reftime = starttime

                        if tmpdur < 60 * 3:
                            shouldskip = True
                    
                    # Don't show very short videos
                    if self.MyOverlayWindow.hideShortItems and shouldskip == False:
                        if chtype <= 7 and self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos) < self.MyOverlayWindow.shortItemLength:
                            shouldskip = True
                            tmpdur = 0
                        else:
                            nextlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos + 1)
                            prevlen = self.MyOverlayWindow.channels[curchannel - 1].getItemDuration(playlistpos - 1)

                            if nextlen < 60:
                                tmpdur += nextlen / 2

                            if prevlen < 60:
                                tmpdur += prevlen / 2

                    width = int((basew / 5400.0) * tmpdur)

                    if width < 30 and shouldskip == False:
                        width = 30
                        tmpdur = int(30.0 / (basew / 5400.0))

                    if width + xpos > basex + basew:
                        width = basex + basew - xpos

                    if shouldskip == False and width >= 30:
                        chname = (self.MyOverlayWindow.channels[curchannel - 1].name)
                        mediapath = ascii(self.MyOverlayWindow.channels[curchannel - 1].getItemFilename(playlistpos))
                        mylabel = self.MyOverlayWindow.channels[curchannel - 1].getItemTitle(playlistpos)
                        myLiveID = self.MyOverlayWindow.channels[curchannel - 1].getItemLiveID(playlistpos)
                        LiveID = self.chanlist.unpackLiveID(myLiveID)
                        type = LiveID[0]
                        id = LiveID[1]
                        playcount = int(LiveID[4])  
                        rating = LiveID[5]
                        
                        if REAL_SETTINGS.getSetting("EPG.xInfo") == "true":                  
                            if playcount == 0:
                                New = '(NEW)'
                            else:
                                New = ''
                            if rating != 'NR':
                                Rat = '[' + rating + ']'
                            else:
                                Rat = ''  
                                
                            mylabel = (mylabel + ' ' + New + ' ' + Rat).replace('()','').replace('[]','')
                            
                        if REAL_SETTINGS.getSetting('EPGcolor_enabled') == '1':
                            if type == 'movie' and REAL_SETTINGS.getSetting('EPGcolor_MovieGenre') == "false":
                                self.textureButtonNoFocus = self.GetEPGtype('Movie')
                            else:
                                mygenre = self.MyOverlayWindow.channels[curchannel - 1].getItemgenre(playlistpos)
                                self.textureButtonNoFocus = self.GetEPGtype(mygenre)
                                
                        elif REAL_SETTINGS.getSetting('EPGcolor_enabled') == '2':
                            self.textureButtonNoFocus = self.GetEPGtype(str(chtype))
                           
                        elif REAL_SETTINGS.getSetting('EPGcolor_enabled') == '3':
                            self.textureButtonNoFocus = self.GetEPGtype(rating)
                        else:   
                            self.textureButtonNoFocus = MEDIA_LOC + BUTTON_NO_FOCUS
                            
                        # if self.MyOverlayWindow.channels[self.centerChannel - 1].getItemEpisodeTitle(-999) == ('[COLOR=%s][B]OnDemand[/B][/COLOR]' % ((self.MyOverlayWindow.channelbugcolor).replace('0x',''))):
                            # self.textureButtonFocus = IMAGES_LOC + 'label_ondemand.png'
                            # self.textureButtonNoFocus = MEDIA_LOC + 'label_ondemand.png'
                        # Filtered = True
                        #Create Control array
                        self.channelButtons[row].append(xbmcgui.ControlButton(xpos, basey, width, baseh, mylabel, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, font=self.textfont, textColor=self.textcolor, focusedColor=self.focusedcolor))

                    totaltime += tmpdur
                    reftime += tmpdur
                    playlistpos += 1
                    totalloops += 1

                if totalloops >= 1000:
                    self.log("Broken big loop, too many loops, reftime is " + str(reftime) + ", endtime is " + str(endtime))

                # If there were no buttons added, show some default button
                if len(self.channelButtons[row]) == 0:
                    self.channelButtons[row].append(xbmcgui.ControlButton(basex, basey, basew, baseh, self.MyOverlayWindow.channels[curchannel - 1].name, focusTexture=self.textureButtonFocus, noFocusTexture=self.textureButtonNoFocus, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor))
        except:
            self.log("Exception in setButtons", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)
            
        self.logDebug('setButtons return')
        return True


    def onAction(self, act):
        self.logDebug('onAction ' + str(act.getId()))
        
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        action = act.getId()
        
        try:
            if action in ACTION_PREVIOUS_MENU:
                if self.showingContext:    
                    self.closeContext()
                else:
                    self.closeEPG()   
                    
                if self.showingInfo:
                    self.infoOffset = 0
                    self.infoOffsetV = 0
            
            elif action == ACTION_MOVE_DOWN: 
                if not self.showingContext:
                    self.GoDown()    
                if self.showingInfo:  
                    self.infoOffsetV -= 1
                    
            elif action == ACTION_MOVE_UP:
                if not self.showingContext:
                    self.GoUp()         
                if self.showingInfo: 
                    self.infoOffsetV += 1

            elif action == ACTION_MOVE_LEFT: 
                if not self.showingContext:
                    self.GoLeft()           
                if self.showingInfo:
                    self.infoOffset -= 1
            
            elif action == ACTION_MOVE_RIGHT: 
                if not self.showingContext:
                    self.GoRight()           
                if self.showingInfo:
                    self.infoOffset += 1
            
            elif action == ACTION_STOP:
                self.closeEPG()           
                if self.showingInfo:
                    self.infoOffset = 0
                    self.infoOffsetV = 0
            
            elif action == ACTION_SELECT_ITEM:
                print 'showingContext = ' + str(self.showingContext)
                if self.showingContext:
                    pos = self.contextButton.getSelectedPosition()  
                    
                    if getProperty("PVR.Type") == 'tvshow':
                        print getProperty("PVR.Season"), getProperty("PVR.Episode")
                        if getProperty("PVR.Season") != '0' and getProperty("PVR.Episode") != '0':
                            info = 'seasoninfo'
                            # traktinfo = 'similar'
                            traktinfo = 'similartvshowstrakt'
                            dbtype = 'tvdb_id'
                            title = 'tvshow'
                        else:
                            info = 'extendedtvinfo'
                            # traktinfo = 'similar'
                            traktinfo = 'similartvshowstrakt'
                            dbtype = 'tvdb_id'
                            title = 'name'                    
                    else:
                        info = 'extendedinfo'
                        # traktinfo = 'similarmovies'
                        traktinfo = 'similarmoviestrakt'
                        dbtype = 'imdb_id'
                        title = 'name'  
                                            
                    if pos == 0:
                        print 'Context, MoreInfo'
                        if info == 'seasoninfo':
                            xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,%s=%s,%s=%s,season=%s)" % (info, getProperty("PVR.DBID"), title, getProperty("PVR.Title"), dbtype, getProperty("PVR.ID"), getProperty("PVR.Season")))
                        else:
                            xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,%s=%s,%s=%s)" % (info, getProperty("PVR.DBID"), title, getProperty("PVR.Title"), dbtype, getProperty("PVR.ID")))
                    elif pos == 1:
                        print 'Context, Similar'
                        print getProperty("PVR.DBID")
                        if getProperty("PVR.DBID") != '0':
                            print GetSimilarFromOwnLibrary(getProperty("PVR.DBID"))
                        # if getProperty("PVR.DBID") == '0' and getProperty("PVR.ID") != '0':
                            # xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,id=%s)" % (traktinfo, getProperty("PVR.ID")))#NONLOCAL
                        # elif getProperty("PVR.ID") == '0' and getProperty("PVR.DBID") != '0':
                            # xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s)" % (traktinfo, getProperty("PVR.DBID")))#LOCAL
                        # else:
                            # xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,id=%s)" % (traktinfo, getProperty("PVR.DBID"), getProperty("PVR.ID")))#OTHER
                        Comingsoon()
                    elif pos == 2:
                        Comingsoon()
                    elif pos == 3:
                        Comingsoon()
                else:
                    lastaction = time.time() - self.lastActionTime           
                    if self.showingInfo:
                        self.infoOffset = 0
                        self.infoOffsetV = 0

                    if lastaction >= 2:
                        self.selectShow()
                        self.closeEPG()
                        self.infoOffset = 0
                        self.infoOffsetV = 0
                        self.lastActionTime = time.time()
                
                    
            elif action == ACTION_PAGEDOWN: 
                if not self.showingContext:
                    self.GoPgDown()  
                if self.showingInfo:  
                    self.infoOffsetV -= 6       

            elif action == ACTION_PAGEUP: 
                if not self.showingContext:
                    self.GoPgUp()           
                if self.showingInfo:
                    self.infoOffsetV += 6
                    
            elif action == ACTION_RECORD:
                self.log('ACTION_RECORD')
                # PVRrecord(self.PVRchtype, self.PVRmediapath, self.PVRchname, getProperty("PVR.Title"))
                    
            elif action == ACTION_TELETEXT_RED:
                self.log('ACTION_TELETEXT_RED')
                self.MyOverlayWindow.myOndemand.close()
                self.MyOverlayWindow.myDVR.close()
                self.MyOverlayWindow.myApps.close()
                    
                if getProperty("PTVL.EPG_Opened") != "true":
                    self.MyOverlayWindow.myepg.doModal()
            
            elif action == ACTION_TELETEXT_GREEN:
                self.log('ACTION_TELETEXT_GREEN')
                self.MyOverlayWindow.myOndemand.close()
                self.MyOverlayWindow.myApps.close()

                if getProperty("PTVL.PVR_Opened") != "true":
                    self.MyOverlayWindow.myDVR.doModal()
            
            elif action == ACTION_TELETEXT_YELLOW:
                self.log('ACTION_TELETEXT_YELLOW')
                self.MyOverlayWindow.myDVR.close()
                self.MyOverlayWindow.myApps.close()
                
                if getProperty("PTVL.ONDEMAND__Opened") != "true":
                    self.MyOverlayWindow.myOndemand.doModal()
            
            elif action == ACTION_TELETEXT_BLUE:
                self.log('ACTION_TELETEXT_BLUE')
                self.MyOverlayWindow.myOndemand.close()
                self.MyOverlayWindow.myDVR.close()
                
                if getProperty("PTVL.APPS_Opened") != "true":
                    self.MyOverlayWindow.myApps.doModal()
                
            elif action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
                if self.inputChannel < 0:
                    self.inputChannel = action - ACTION_NUMBER_0
                else:
                    if self.inputChannel < 100:
                        self.inputChannel = self.inputChannel * 10 + action - ACTION_NUMBER_0
                
                self.showChannelLabel(self.inputChannel)  

            elif action == ACTION_SYMBOLS: #Toggle thru favourite channels
                self.log('ACTION_SYMBOLS')
                self.showChannelLabel(self.MyOverlayWindow.Jump2Favorite())  

            elif action == ACTION_CONTEXT_MENU:
                if not self.showingContext:
                    self.showContextMenu()

        except:
            self.log("Unknown EPG Exception", xbmc.LOGERROR)
            self.log(traceback.format_exc(), xbmc.LOGERROR)

            try:
                self.close()
            except:
                self.log("Error closing", xbmc.LOGERROR)

            self.MyOverlayWindow.sleepTimeValue = 1
            self.MyOverlayWindow.startSleepTimer()
            return

        self.actionSemaphore.release()
        self.logDebug('onAction return')


    def closeContext(self):
        self.showingContext = False
        try:
            self.removeControl(self.contextButtonB)
            self.removeControl(self.contextButtonC)
            self.removeControl(self.contextButtonF)
            self.removeControl(self.contextButton)
        except:
            pass     
        

    def closeEPG(self):
        self.log('closeEPG')
        self.closeContext()
        setProperty("PTVL.EPG_Opened","false")
        
        try:
            if self.channelLabelTimer.isAlive():
                self.channelLabelTimer.cancel()
        except:
            pass
        try:
            if self.GotoChannelTimer.isAlive():
                self.GotoChannelTimer.cancel()
        except:
            pass
        try:
            if self.ArtThread1.isAlive():
                self.ArtThread1.cancel()
        except:
            pass
        try:
            if self.ArtThread2.isAlive():
                self.ArtThread2.cancel()
        except:
            pass    
        try:
            self.removeControl(self.currentTime)
            self.removeControl(self.currentTimeBar)
            self.MyOverlayWindow.startSleepTimer()
        except:
            pass
            
        self.close()


    def onControl(self, control):
        self.log('onControl')


    # Run when a show is selected, so close the epg and run the show
    def onClick(self, controlid):
        self.log('onClick')
        if not self.showingContext:
            try:
                if self.actionSemaphore.acquire(False) == False:
                    self.log('Unable to get semaphore')
                    return

                lastaction = time.time() - self.lastActionTime

                if lastaction >= 2:
                    try:
                        selectedbutton = self.getControl(controlid)
                    except:
                        self.actionSemaphore.release()
                        self.log('onClick unknown controlid ' + str(controlid))
                        return

                    for i in range(self.rowCount):
                        for x in range(len(self.channelButtons[i])):
                            mycontrol = 0
                            mycontrol = self.channelButtons[i][x]

                            if selectedbutton == mycontrol:
                                self.focusRow = i
                                self.focusIndex = x
                                self.selectShow()
                                self.closeEPG()
                                self.lastActionTime = time.time()
                                self.actionSemaphore.release()
                                self.log('onClick found button return')
                                return

                    self.lastActionTime = time.time()
                    self.closeEPG()

                self.actionSemaphore.release()
                self.log('onClick return')
            except:
                pass
    
    
    # Called from the timer to hide the channel label.
    def hideChannelLabel(self):
        self.log('hideChannelLabel')
        self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
        try:
            if self.GotoChannelTimer.isAlive():
                self.GotoChannelTimer.cancel()
        except:
            pass     
        try:
            for i in range(3):
                self.channelLabel[i].setVisible(False)
        except:
            pass
        inputChannel = self.inputChannel
        self.GotoChannelTimer = threading.Timer(2.1, self.GotoChannel, [inputChannel])
        self.GotoChannelTimer.start()
        self.inputChannel = -1
        
          
    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))
        
        try:
            if self.channelLabelTimer.isAlive():
                self.channelLabelTimer.cancel()
        except:
            pass            
            
        tmp = self.inputChannel
        self.hideChannelLabel()
        self.inputChannel = tmp
        curlabel = 0

        if channel > 99:
            if FileAccess.exists(IMAGES_LOC):
                self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str(channel // 100) + '.png')
            self.channelLabel[curlabel].setVisible(True)
            curlabel += 1

        if channel > 9:
            if FileAccess.exists(IMAGES_LOC):
                self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str((channel % 100) // 10) + '.png')
            self.channelLabel[curlabel].setVisible(True)
            curlabel += 1
        
        if FileAccess.exists(IMAGES_LOC):
            self.channelLabel[curlabel].setImage(IMAGES_LOC + 'label_' + str(channel % 10) + '.png')
        self.channelLabel[curlabel].setVisible(True)

        self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
        self.channelLabelTimer.name = "ChannelLabel"
        self.channelLabelTimer.start()
        self.log('showChannelLabel return')
        
            
    def GotoChannel(self,inchannel):
        print 'GotoChannel'
        try:
            if self.GotoChannelTimer.isAlive():
                self.GotoChannelTimer.cancel()
        except:
            pass
        try:
            if inchannel > self.centerChannel:
                newchannel = self.MyOverlayWindow.fixChannel(inchannel+2)
            else:
                newchannel = self.MyOverlayWindow.fixChannel(inchannel+2,False)
            
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
            self.setProperButton(0)
            self.inputChannel = -1
            self.log('GotoChannel return')
        except Exception,e:
            print str(e)
            pass
            
           
    def GoPgDown(self):
        self.log('GoPgDown')
        try:
            newchannel = self.centerChannel
            for x in range(0, 6):
                newchannel = self.MyOverlayWindow.fixChannel(newchannel + 1)
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
            self.setProperButton(0)
            self.log('GoPgDown return') 
        except:
            pass

    
    def GoPgUp(self):
        self.log('GoPgUp')
        try:
            newchannel = self.centerChannel
            for x in range(0, 6):
                newchannel = self.MyOverlayWindow.fixChannel(newchannel - 1, False)
            self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(newchannel))
            self.setProperButton(0)
            self.log('GoPgUp return')
        except:
            pass
            

    def GoDown(self):
        self.log('goDown')
        try:
            # change controls to display the proper junks
            if self.focusRow == self.rowCount - 1:
                self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel + 1))
                self.focusRow = self.rowCount - 2

            self.setProperButton(self.focusRow + 1)
            self.log('goDown return')
        except:
            pass

    
    def GoUp(self):
        self.log('goUp')
        try:

            # same as godown
            # change controls to display the proper junks
            if self.focusRow == 0:
                self.setChannelButtons(self.shownTime, self.MyOverlayWindow.fixChannel(self.centerChannel - 1, False))
                self.focusRow = 1

            self.setProperButton(self.focusRow - 1)
            self.log('goUp return')
        except:
            pass

    
    def GoLeft(self):
        self.log('goLeft')
        try:
            basex, basey = self.getControl(111 + self.focusRow).getPosition()
            basew = self.getControl(111 + self.focusRow).getWidth()

            # change controls to display the proper junks
            if self.focusIndex == 0:
                left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
                width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                self.setChannelButtons(self.shownTime - 1800, self.centerChannel)
                curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

                if(curbutidx - 1) >= 0:
                    self.focusIndex = curbutidx - 1
                else:
                    self.focusIndex = 0
            else:
                self.focusIndex -= 1

            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))
            self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
            self.setShowInfo()
            self.focusEndTime = endtime
            self.focusTime = starttime + 30
            self.log('goLeft return')
        except:
            pass

    
    def GoRight(self):
        self.log('goRight')
        try:
            basex, basey = self.getControl(111 + self.focusRow).getPosition()
            basew = self.getControl(111 + self.focusRow).getWidth()

            # change controls to display the proper junks
            if self.focusIndex == len(self.channelButtons[self.focusRow]) - 1:
                left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
                width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
                left = left - basex
                starttime = self.shownTime + (left / (basew / 5400.0))
                self.setChannelButtons(self.shownTime + 1800, self.centerChannel)
                curbutidx = self.findButtonAtTime(self.focusRow, starttime + 30)

                if(curbutidx + 1) < len(self.channelButtons[self.focusRow]):
                    self.focusIndex = curbutidx + 1
                else:
                    self.focusIndex = len(self.channelButtons[self.focusRow]) - 1
            else:
                self.focusIndex += 1

            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))
            self.setFocus(self.channelButtons[self.focusRow][self.focusIndex])
            self.setShowInfo()
            self.focusEndTime = endtime
            self.focusTime = starttime + 30
            self.log('goRight return')
        except:
            pass

    
    def findButtonAtTime(self, row, selectedtime):
        self.log('findButtonAtTime ' + str(row))
        basex, basey = self.getControl(111 + row).getPosition()
        baseh = self.getControl(111 + row).getHeight()
        basew = self.getControl(111 + row).getWidth()

        for i in range(len(self.channelButtons[row])):
            left, top = self.channelButtons[row][i].getPosition()
            width = self.channelButtons[row][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if selectedtime >= starttime and selectedtime <= endtime:
                return i

        return -1


    # based on the current focus row and index, find the appropriate button in
    # the new row to set focus to
    def setProperButton(self, newrow, resetfocustime = False):
        self.log('setProperButton ' + str(newrow))
        self.focusRow = newrow
        basex, basey = self.getControl(111 + newrow).getPosition()
        baseh = self.getControl(111 + newrow).getHeight()
        basew = self.getControl(111 + newrow).getWidth()

        for i in range(len(self.channelButtons[newrow])):
            left, top = self.channelButtons[newrow][i].getPosition()
            width = self.channelButtons[newrow][i].getWidth()
            left = left - basex
            starttime = self.shownTime + (left / (basew / 5400.0))
            endtime = starttime + (width / (basew / 5400.0))

            if self.focusTime >= starttime and self.focusTime <= endtime:
                self.focusIndex = i
                self.setFocus(self.channelButtons[newrow][i])
                self.setShowInfo()
                self.focusEndTime = endtime

                if resetfocustime:
                    self.focusTime = starttime + 30

                self.log('setProperButton found button return')
                return

        self.focusIndex = 0
        self.setFocus(self.channelButtons[newrow][0])
        left, top = self.channelButtons[newrow][0].getPosition()
        width = self.channelButtons[newrow][0].getWidth()
        left = left - basex
        starttime = self.shownTime + (left / (basew / 5400.0))
        endtime = starttime + (width / (basew / 5400.0))
        self.focusEndTime = endtime

        if resetfocustime:
            self.focusTime = starttime + 30

        self.setShowInfo()
        self.log('setProperButton return')

            
    def setShowInfo(self):
        self.log('setShowInfo')        
        self.showingInfo = True
        basex, basey = self.getControl(111 + self.focusRow).getPosition()
        baseh = self.getControl(111 + self.focusRow).getHeight()
        basew = self.getControl(111 + self.focusRow).getWidth()
        # use the selected time to set the video
        left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        left = left - basex + (width / 2)
        starttime = self.shownTime + (left / (basew / 5400.0))
        chnoffset = self.focusRow - 2
        newchan = self.centerChannel
        
        if self.MyOverlayWindow.OnDemand and chnoffset == 0:
            print 'setShowInfo, OnDemand'
            plpos = -999
            mediapath = xbmc.Player().getPlayingFile()
        else:
            while chnoffset != 0:
                if chnoffset > 0:
                    newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                    chnoffset -= 1
                else:
                    newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                    chnoffset += 1

            plpos = self.determinePlaylistPosAtTime(starttime, newchan)
            
            if plpos == -1:
                self.log('Unable to find the proper playlist to set from EPG')
                return  
            try:
                mediapath = self.MyOverlayWindow.channels[newchan - 1].getItemFilename(plpos)
            except:
                mediapath = self.MyOverlayWindow.channels[newchan - 1].getItemFilename(plpos)

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
        except:
            self.log("Unknown EPG Chtype Exception", xbmc.LOGERROR)
            chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
            pass
                            
        #Change Label when Dynamic artwork enabled
        try:
            if self.infoOffset > 0:
                self.getControl(515).setVisible(False)
                self.getControl(516).setLabel('COMING UP:') 
            elif self.infoOffset < 0:
                self.getControl(515).setVisible(False)
                self.getControl(516).setLabel('ALREADY SEEN:')
            elif self.infoOffset == 0 and self.infoOffsetV == 0:
                self.getControl(515).setVisible(True) 
                self.getControl(516).setLabel('NOW WATCHING:')
            # elif self.infoOffsetV != 0 and self.infoOffset == 0: 
            else:
                self.getControl(515).setVisible(False)
                self.getControl(516).setLabel('ON NOW:')
        except:
            pass
            
        chname = self.MyOverlayWindow.channels[newchan - 1].name
        self.SetMediaInfo(chtype, chname, mediapath, newchan, plpos)
        
        
    def SetMediaInfo(self, chtype, chname, mediapath, newchan, plpos):
        self.log('SetMediaInfo') 
        mpath = self.MyOverlayWindow.GetMpath(mediapath)
        
        if plpos == -999:
            if len(getProperty("Playing.OnDemand_tmpstr")) > 0:
                tmpstr = (getProperty("Playing.OnDemand_tmpstr")).split('//')
                title = tmpstr[0]
                SEtitle = ('[COLOR=%s][B]OnDemand[/B][/COLOR]' % ((self.channelbugcolor).replace('0x','')))
                Description = tmpstr[2]
                genre = tmpstr[3]
                timestamp = tmpstr[4]
                LiveID = self.chanlist.unpackLiveID(tmpstr[5])
                self.getControl(503).setImage(IMAGES_LOC + 'ondemand.png')
                try:
                    self.getControl(508).setImage(IMAGES_LOC + 'ondemand.png')
                    self.getControl(510).setImage(IMAGES_LOC + 'ondemand.png')
                except:
                    pass
            else:
                try:
                    if self.MyOverlayWindow.GetPlayingTmpstrTimer.isAlive():
                        self.MyOverlayWindow.GetPlayingTmpstrTimer.cancel()
                except:
                    pass
                data = [chtype, chname, mediapath, plpos]
                self.MyOverlayWindow.GetPlayingTmpstrTimer = threading.Timer(1.0, self.MyOverlayWindow.GetPlayingTmpstrThread, [data])
                self.MyOverlayWindow.GetPlayingTmpstrTimer.name = "GetPlayingTmpstrTimer"  
                self.MyOverlayWindow.GetPlayingTmpstrTimer.start()  
                return
        else:
            title = (self.MyOverlayWindow.channels[newchan - 1].getItemTitle(plpos))   
            SEtitle = self.MyOverlayWindow.channels[newchan - 1].getItemEpisodeTitle(plpos) 
            Description = self.MyOverlayWindow.channels[newchan - 1].getItemDescription(plpos)
            timestamp = (self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(plpos))
            myLiveID = (self.MyOverlayWindow.channels[newchan - 1].getItemLiveID(plpos))      
            LiveID = self.chanlist.unpackLiveID(myLiveID)
            try:
                self.getControl(503).setImage(ascii(self.channelLogos + (self.MyOverlayWindow.channels[newchan - 1].name + '.png')))
            except:
                pass
                
        try:
            SEinfo = SEtitle.split(' -')[0]
            season = int(SEinfo.split('x')[0])
            episode = int(SEinfo.split('x')[1])
        except:
            season = 0
            episode = 0  
            
        setProperty("PVR.Season",str(season))
        setProperty("PVR.Episode",str(episode))
        
        try:
            if self.showSeasonEpisode:
                eptitles = SEtitle.split('- ')
                eptitle = (eptitles[1] + (' - ' + eptitles[2] if len(eptitles) > 2 else ''))
                swtitle = ('S' + ('0' if season < 10 else '') + str(season) + 'E' + ('0' if episode < 10 else '') + str(episode) + ' - ' + (eptitle)).replace('  ',' ')
            else:
                swtitle = SEtitle      
        except:
            swtitle = SEtitle
            pass

        self.getControl(500).setLabel((title).replace("*NEW*",""))
        self.getControl(501).setLabel(swtitle)
        self.getControl(502).setLabel(Description)

        ##LIVEID##
        type = LiveID[0]
        id = LiveID[1]
        dbid = LiveID[2]
        Managed = LiveID[3]
        playcount = int(LiveID[4])
        
        #PVR Globals
        setProperty("PVR.Chtype",str(chtype))
        setProperty("PVR.Title",((title).replace("*NEW*","")))
        setProperty("PVR.Mpath",mpath)
        setProperty("PVR.Chname",chname)
        setProperty("PVR.SEtitle",SEtitle)
        setProperty("PVR.Type",type)
        setProperty("PVR.DBID",dbid)
        setProperty("PVR.ID",id)
        setProperty("PVR.Type",type)
            
        #Notification Globals
        setProperty("PVR.ChanNum",str(newchan))
        setProperty("PVR.TimeStamp",str(timestamp))
        
        #Sickbeard/Couchpotato
        try:
            if Managed == 'True':
                self.getControl(511).setVisible(True)  
                if type == 'tvshow':
                    self.getControl(511).setImage(IMAGES_LOC + 'SB.png')
                elif type == 'movie':
                    self.getControl(511).setImage(IMAGES_LOC + 'CP.png')                          
            else:
                self.getControl(511).setVisible(False)  
                self.getControl(511).setImage(IMAGES_LOC + 'NA.png') 
        except:
            self.log('setShowInfo, Label 511 not found')
            pass    
            
        #Unaired/aired
        try:
            self.getControl(512).setVisible(True)
            if playcount == 0:
                self.getControl(512).setImage(MEDIA_LOC + 'NEW.png')
            elif playcount >= 1:
                self.getControl(512).setImage(MEDIA_LOC + 'OLD.png')      
            else:
                self.getControl(512).setVisible(False) 
                self.getControl(512).setImage(MEDIA_LOC + 'NA.png')     
        except:
            self.log('setShowInfo, Label 512 not found')
            pass  
            
        #Dynamic Art1
        try:
            self.setArtwork1(type, chtype, chname, id, dbid, mpath, self.type1EXT)
        except Exception,e:
            self.log('setShowInfo, Label 508 not found', str(e))
            pass
           
        #Dynamic Art2
        try:
            self.setArtwork2(type, chtype, chname, id, dbid, mpath, self.type2EXT)
        except Exception,e:
            self.log('setShowInfo, Label 510 not found', str(e))
            pass

            
    def FindArtwork_Thread(self, data):
        try:
            self.getControl(data[7]).setVisible(True)
            if getProperty("EnableArtwork") == "false":
                setImage = self.Artdownloader.SetDefaultArt_NEW(data[2], data[5], data[6])
            else:
                setImage = self.Artdownloader.FindArtwork_NEW(data[0], data[1], data[2], data[3], data[4], data[5], data[6])
                if FileAccess.exists(setImage) == False:
                    setImage = self.Artdownloader.SetDefaultArt_NEW(data[2], data[5], data[6])
            self.getControl(data[7]).setImage(setImage)
        except Exception,e:
            self.log('FindArtwork_Thread, Failed!', str(e))
            pass  
        
        
    def setArtwork1(self, type, chtype, chname, id, dbid, mpath, type1EXT):
        self.log('setArtwork1')
        try:
            try:
                if self.ArtThread1.isAlive():
                    self.ArtThread1.cancel()
            except:
                pass
                
            data = [type, chtype, chname, id, dbid, mpath, type1EXT, 508]
            self.ArtThread1 = threading.Timer(0.5, self.FindArtwork_Thread, [data])
            self.ArtThread1.name = "ArtThread1"
            self.ArtThread1.start()
        except Exception,e:
            self.log('setArtwork1, Failed!', str(e))
            pass  
    
    
    def setArtwork2(self, type, chtype, chname, id, dbid, mpath, type2EXT):
        self.log('setArtwork2')
        try:
            try:
                if self.ArtThread2.isAlive():
                    self.ArtThread2.cancel()
            except:
                pass
                
            data = [type, chtype, chname, id, dbid, mpath, type2EXT, 510]
            self.ArtThread2 = threading.Timer(0.5, self.FindArtwork_Thread, [data])
            self.ArtThread2.name = "ArtThread2"
            self.ArtThread2.start()
        except Exception,e:
            self.log('setArtwork2, Failed!', str(e))
            pass
    
    
    # using the currently selected button, play the proper shows
    def selectShow(self):
        self.log('selectShow')    
        CurChannel = self.MyOverlayWindow.currentChannel
        REAL_SETTINGS.setSetting('LastChannel', str(CurChannel))
        
        try:
            basex, basey = self.getControl(111 + self.focusRow).getPosition()
            baseh = self.getControl(111 + self.focusRow).getHeight()
            basew = self.getControl(111 + self.focusRow).getWidth()
            # use the selected time to set the video
            left, top = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
            width = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
            left = left - basex + (width / 2)
            starttime = self.shownTime + (left / (basew / 5400.0))
            chnoffset = self.focusRow - 2
            newchan = self.centerChannel
            nowDate = datetime.datetime.now()
            
            while chnoffset != 0:
                if chnoffset > 0:
                    newchan = self.MyOverlayWindow.fixChannel(newchan + 1, True)
                    chnoffset -= 1
                else:
                    newchan = self.MyOverlayWindow.fixChannel(newchan - 1, False)
                    chnoffset += 1

            plpos = self.determinePlaylistPosAtTime(starttime, newchan)
            
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
            except:
                self.log("Unknown EPG Chtype Exception", xbmc.LOGERROR)
                chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(newchan) + '_type'))
                pass
                
            if plpos == -1:
                self.log('Unable to find the proper playlist to set from EPG', xbmc.LOGERROR)
                return
           
            timedif = (time.time() - self.MyOverlayWindow.channels[newchan - 1].lastAccessTime)
            pos = self.MyOverlayWindow.channels[newchan - 1].playlistPosition
            showoffset = self.MyOverlayWindow.channels[newchan - 1].showTimeOffset
            #Start at the beginning of the playlist get the first epoch date
            #position pos of the playlist convert the string add until we get to the current item in the playlist

            if chtype == 8 and len(self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(pos)) > 0:
                tmpDate = self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(pos)
                self.log("selectshow tmpdate " + str(tmpDate))
                
                try:#sloppy fix, for threading issue with strptime.
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                except:
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    pass
                    
                epochBeginDate = time.mktime(t)
                #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                #loop till we get to the current show  
                while epochBeginDate + self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos) <  time.time():
                    epochBeginDate += self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos)
                    pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
                    self.log('live tv while loop')

            # adjust the show and time offsets to properly position inside the playlist
            else:
                while showoffset + timedif > self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos):
                    self.log('duration ' + str(self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos)))
                    timedif -= self.MyOverlayWindow.channels[newchan - 1].getItemDuration(pos) - showoffset
                    pos = self.MyOverlayWindow.channels[newchan - 1].fixPlaylistIndex(pos + 1)
                    showoffset = 0
                self.log('pos + plpos ' + str(pos) +', ' + str(plpos))
            
            if self.MyOverlayWindow.currentChannel == newchan:
                if plpos == xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition():
                    self.log('selectShow return current show')
                    return

                if chtype == 8 and len(self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(pos)) > 0:
                    tmpDate = int(getProperty("PVR.TimeStamp"))
                    try:#sloppy fix, for threading issue with strptime.
                        t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    except:
                        t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        pass
                    Notify_Time = time.strftime('%I:%M%p, %A', t)
                    self.log('selectShow return current LiveTV channel')
                    return
            
            if pos != plpos:
                if chtype == 8 and len(self.MyOverlayWindow.channels[newchan - 1].getItemtimestamp(pos)) > 0:
                    tmpDate = int(getProperty("PVR.TimeStamp"))
                    try:#sloppy fix, for threading issue with strptime.
                        t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    except:
                        t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        pass
                    Notify_Time = time.strftime('%I:%M%p, %A', t)
                    self.log('selectShow return different LiveTV channel')
                    return
                else:
                    Notify_Time = self.PVRTimeOffset
                    self.MyOverlayWindow.channels[newchan - 1].setShowPosition(plpos)
                    self.MyOverlayWindow.channels[newchan - 1].setShowTime(0)
                    self.MyOverlayWindow.channels[newchan - 1].setAccessTime(time.time())

            self.MyOverlayWindow.newChannel = newchan
            self.log('selectShow return')
        except:
            pass
        
        
    def determinePlaylistPosAtTime(self, starttime, channel):
        self.logDebug('determinePlaylistPosAtTime ' + str(starttime) + ', ' + str(channel))
        channel = self.MyOverlayWindow.fixChannel(channel)
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
        except:
            self.log("Unknown EPG Chtype Exception", xbmc.LOGERROR)
            chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            pass

        self.lastExitTime = ADDON_SETTINGS.getSetting("LastExitTime")     
        
        try:
            # if the channel is paused, then it's just the current item
            if self.MyOverlayWindow.channels[channel - 1].isPaused:
                self.logDebug('determinePlaylistPosAtTime paused return')
                return self.MyOverlayWindow.channels[channel - 1].playlistPosition
            else:
                # Find the show that was running at the given time
                # Use the current time and show offset to calculate it
                # At timedif time, channelShowPosition was playing at channelTimes
                # The only way this isn't true is if the current channel is curchannel since
                # it could have been fast forwarded or rewinded (rewound)?
                if channel == self.MyOverlayWindow.currentChannel: #currentchannel epg
                    playlistpos = int(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition())
                    #Live TV pull date from the playlist entry
                    if chtype == 8 and len(self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)) > 0:
                        tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                        self.logDebug("setbuttonnowtime2 " + str(tmpDate))
                       
                        try:#sloppy fix, for threading issue with strptime.
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        except:
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            pass
                                
                        epochBeginDate = time.mktime(t)
                        videotime = time.time() - epochBeginDate
                        reftime = time.time()
                    else:
                        try:
                            videotime = xbmc.Player().getTime()
                        except:
                            videotime = xbmc.Player().getTime()
                            pass
                        reftime = time.time() 
                else:
                    playlistpos = self.MyOverlayWindow.channels[channel - 1].playlistPosition
                    #Live TV pull date from the playlist entry
                    if chtype == 8 and len(self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)) > 0:
                        tmpDate = self.MyOverlayWindow.channels[channel - 1].getItemtimestamp(playlistpos)
                        self.logDebug("setbuttonnowtime2 " + str(tmpDate))
                           
                        try:#sloppy fix, for threading issue with strptime.
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        except:
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            pass
                            
                        epochBeginDate = time.mktime(t)
                        while epochBeginDate + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) <  time.time():
                            epochBeginDate += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                            playlistpos = self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos + 1)
                           
                        videotime = time.time() - epochBeginDate
                        self.logDebug('videotime ' + str(videotime))
                        reftime = time.time()
                          
                    else:
                        videotime = self.MyOverlayWindow.channels[channel - 1].showTimeOffset
                        reftime = self.MyOverlayWindow.channels[channel - 1].lastAccessTime

                # normalize reftime to the beginning of the video
                reftime -= videotime

                while reftime > starttime:
                    playlistpos -= 1
                    reftime -= self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)

                while reftime + self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos) < starttime:
                    reftime += self.MyOverlayWindow.channels[channel - 1].getItemDuration(playlistpos)
                    playlistpos += 1

                self.logDebug('determinePlaylistPosAtTime return' + str(self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)))
                return self.MyOverlayWindow.channels[channel - 1].fixPlaylistIndex(playlistpos)
        except:
            pass

            
    def showContextMenu(self):
        self.log('showContextMenu')
        self.showingContext = True
        ChanButtonx, ChanButtony = self.channelButtons[self.focusRow][self.focusIndex].getPosition()
        ChanButtonw = self.channelButtons[self.focusRow][self.focusIndex].getWidth()
        ChanButtonh = self.channelButtons[self.focusRow][self.focusIndex].getHeight()
        
        self.contextButtonB = xbmcgui.ControlImage(0, 0, 1920, 1080, self.ButtonContextB)
        self.addControl(self.contextButtonB)
        self.contextButtonC = xbmcgui.ControlImage(ChanButtonx-4, ChanButtony+71, 258, 308, self.ButtonContextC)
        self.addControl(self.contextButtonC)
        self.contextButtonF = xbmcgui.ControlButton(ChanButtonx-4, ChanButtony, ChanButtonw+8, ChanButtonh, '[ '+getProperty("PVR.Title")+' ]', focusTexture=self.ButtonContextF, noFocusTexture=self.ButtonContextF, alignment=4, textColor=self.textcolor, focusedColor=self.focusedcolor)
        self.addControl(self.contextButtonF)
        
        self.contextButton = xbmcgui.ControlList(ChanButtonx, ChanButtony+75, 250, 1000, self.textfont, self.textcolor, self.textureButtonNoFocusAlt, self.textureButtonFocus, self.focusedcolor, 0, 0, 0, 0, 75, 0, 4)
        self.addControl(self.contextButton)
        self.ContextList = ['More Info','Find Similar','Record Show','Set Reminder']
        self.contextButton.addItems(items=self.ContextList)
        self.setFocus(self.contextButton)
           
    def setReminder(self, tmpDate, cleanDate, title, channel):
        self.log('setReminder')
        jump = REAL_SETTINGS.getSetting("AutoJump") == "true"
        
        try:#sloppy fix, for threading issue with strptime.
            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
        except:
            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
            pass
            
        epochBeginDate = time.mktime(t)
        now = time.time()
        reminder_time = round(((epochBeginDate - now) / 60) - 1)
        reminder_threadtime = round(((epochBeginDate - now) / 60) - 1) * 60
        msg = title + 'on Channel ' + str(channel) +' starts in 1m'
        
        if jump == False:
            xbmc.executebuiltin('XBMC.AlarmClock(PseudoTV Live, XBMC.Notification("PseudoTV Live",'+ msg +',4000,'+ THUMB +'),'+ str(reminder_time) + ',false)')
        else:
            self.MyOverlayWindow.SetAutoJump(reminder_threadtime, cleanDate, title, channel)