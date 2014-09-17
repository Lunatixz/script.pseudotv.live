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

import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import subprocess, os, sys, re
import datetime, time, threading, _strptime
import random, traceback
import urllib, urllib2, json

from fanarttv import *
from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow
from ChannelList import ChannelList
from ChannelListThread import ChannelListThread
from FileAccess import FileLock, FileAccess
from Migrate import Migrate
from Artdownloader import *
from upnp import *
from PVRdownload import *

try:
    from PIL import Image
    from PIL import ImageEnhance
except:
    REAL_SETTINGS.setSetting("COLOR_CHANBUG","true")
    pass
   
    
class MyPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)
        self.stopped = False
        self.ignoreNextStop = False
    
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Player: ' + msg, level)
    
    
    def is_playback_paused(self):
        self.log('is_playback_paused')
        return bool(xbmc.getCondVisibility("Player.Paused"))

    
    def resume_playback(self):
        self.log('resume_playback')
        xbmc.sleep(100)
        if self.is_playback_paused():
            xbmc.Player().pause()
            if DEBUG == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "resume_playback", 1000, THUMB) )
    
    
    def onPlayBackPaused(self):
        self.log('onPlayBackPaused')
        
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                UPNP1 = PauseUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                UPNP2 = PauseUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                UPNP3 = PauseUPNP(IPP3)
        except:
            pass
        
        
    def onPlayBackResumed(self):
        self.log('onPlayBackResumed')
        
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                UPNP1 = ResumeUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                UPNP2 = ResumeUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                UPNP3 = ResumeUPNP(IPP3)
        except:
            pass
    
    
    def onPlayBackStarted(self):
        self.log('onPlayBackStarted')
        self.resume_playback()
        
        try:
            file = xbmc.Player().getPlayingFile()
            file = file.replace("\\\\","\\")
            
            global seektime
            seektime = 0
            
            if seektime == 0:
                seektime = xbmc.Player().getTime()
           
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                self.log('UPNP1 Sharing')
                UPNP1 = SendUPNP(IPP1, file, seektime)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                self.log('UPNP2 Sharing')
                UPNP2 = SendUPNP(IPP2, file, seektime)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                self.log('UPNP3 Sharing')
                UPNP3 = SendUPNP(IPP3, file, seektime)
        except:
            pass
    
    
    def onPlayBackEnded(self):
        self.log('onPlayBackEnded')   
        
    
    def onPlayBackStopped(self):
        if self.stopped == False:
            self.log('Playback stopped')

            if self.ignoreNextStop == False:
                if self.overlay.sleepTimeValue == 0:
                    self.overlay.sleepTimer = threading.Timer(2.0, self.overlay.sleepAction)

                self.overlay.background.setVisible(True)#Visible channel number?
                self.overlay.sleepTimeValue = 1
                self.overlay.startSleepTimer()
                self.stopped = True
            else:
                self.ignoreNextStop = False

                
# overlay window to catch events and change channels
class TVOverlay(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log('__init__')
        # initialize all variables
        self.channels = []
        self.Player = MyPlayer()
        self.Player.overlay = self
        self.inputChannel = -1
        self.channelLabel = []
        self.lastActionTime = 0
        self.actionSemaphore = threading.BoundedSemaphore()
        self.channelThread = ChannelListThread()
        self.channelThread.myOverlay = self
        self.timeStarted = 0
        self.infoOnChange = True
        self.infoOffset = 0
        self.invalidatedChannelCount = 0
        self.showingInfo = False
        self.showingPop = False
        self.showChannelBug = False
        self.showNextItem = False
        self.notificationLastChannel = 0
        self.notificationLastShow = 0
        self.notificationShowedNotif = False
        self.isExiting = False
        self.maxChannels = 0
        self.notPlayingCount = 0
        self.ignoreInfoAction = False
        self.shortItemLength = 60
        self.runningActionChannel = 0
        self.channelDelay = 0
        self.channelbugcolor = CHANBUG_COLOR
        self.showSeasonEpisode = REAL_SETTINGS.getSetting("ShowSeEp") == "true"
        self.PVRchtype = 0
        self.PVRmediapath = ''
        self.PVRchname = ''
        self.PVRtitle = ''
        self.LastChannel = 0
        self.InfTimer = INFOBAR_TIMER[int(REAL_SETTINGS.getSetting('InfoTimer'))]
        self.Artdownloader = Artdownloader()
        self.VideoWindow = False
        
        if FileAccess.exists(os.path.join(skinPath, 'custom_script.pseudotv.live_9506.xml')):
            self.VideoWindow = True
            
        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse = self.channelbugcolor))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)
        self.doModal()
        self.log('__init__ return')
        
        try:
            self.getControl(101).setLabel('Loading...')
        except:
            pass
     
     
    def resetChannelTimes(self):
        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(self.timeStarted - self.channels[i].totalTimePlayed)

            
    def onFocus(self, controlId):
        pass

        
    def Backup(self, org, bak):
        self.log('Backup ' + str(org) + ' - ' + str(bak))
        if FileAccess.exists(org):
            if FileAccess.exists(bak):
                try:
                    os.remove(bak)
                except:
                    pass
            FileAccess.copy(org, bak)
        
        if NOTIFY == 'true':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Backup Complete", 1000, THUMB) )
            
            
    def Restore(self, bak, org):
        self.log('Restore ' + str(bak) + ' - ' + str(org))
        if FileAccess.exists(bak):
            if FileAccess.exists(org):
                try:
                    os.remove(org)
                except:
                    pass
            FileAccess.copy(bak, org)
        
        if NOTIFY == 'true':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Restore Complete, Restarting...", 1000, THUMB) )
        
        xbmc.executebuiltin('XBMC.AlarmClock( RestartPTVL, XBMC.RunScript(' + ADDON_PATH + '/default.py),1.0,false)')
        self.end()
        
    
    def getSize(self, fileobject):
        fileobject.seek(0,2) # move the cursor to the end of the file
        size = fileobject.tell()
        return size
        
        
    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('onInit')
        self.log('PTVL Version = ' + ADDON_VERSION)
        self.channelList = ChannelList()
        settingsFile_flesize = 0
        nsettingsFile_flesize = 0
        atsettingsFile_flesize = 0
        settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
        nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.bak.xml'))
        atsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.pretune.xml'))
        self.Refresh = REFRESH_INT[int(REAL_SETTINGS.getSetting('REFRESH_INT'))]   
        dlg = xbmcgui.Dialog()

        try:
            NormalShutdown = REAL_SETTINGS.getSetting('Normal_Shutdown')
        except:
            NormalShutdown = "true"
            REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
            pass
            
        if FileAccess.exists(settingsFile):
            file1 = FileAccess.open(settingsFile, "rb")
            settingsFile_flesize = self.getSize(file1)
            file1.close()
            
        if FileAccess.exists(nsettingsFile):
            file2 = FileAccess.open(nsettingsFile, "rb")
            nsettingsFile_flesize = self.getSize(file2)
            file2.close()
                
        if FileAccess.exists(atsettingsFile):
            file3 = FileAccess.open(atsettingsFile, "rb")
            atsettingsFile_flesize = self.getSize(file3)
            file3.close()

        # Clear Setting2 for fresh autotune
        if REAL_SETTINGS.getSetting("Autotune") == "true" and REAL_SETTINGS.getSetting("Warning1") == "true":
            self.log('Autotune onInit') 
            
            #Reserve channel check            
            if REAL_SETTINGS.getSetting("reserveChannels") == "false":
                self.log('Autotune not reserved') 
                if settingsFile_flesize != 0:
                    self.Backup(settingsFile, atsettingsFile)

                if FileAccess.exists(atsettingsFile):
                    xbmc.log('Autotune, Back Complete!')
                    f = FileAccess.open(settingsFile, "w")
                    f.write('\n')
                    self.log('Autotune, Setting2 Deleted...')
                    f.close()
                
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Initializing Autotuning...", 4000, THUMB) )

        if FileAccess.exists(GEN_CHAN_LOC) == False:
            try:
                FileAccess.makedirs(GEN_CHAN_LOC)
            except:
                self.Error('Unable to create the cache directory')
                return

        if FileAccess.exists(MADE_CHAN_LOC) == False:
            try:
                FileAccess.makedirs(MADE_CHAN_LOC)
            except:
                self.Error('Unable to create the storage directory')
                return

        self.background = self.getControl(101)
        self.getControl(102).setVisible(False)

        try:
            self.getControl(101).setLabel('Loading...')
        except:
            pass
            
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        self.background.setVisible(True)
        updateDialog = xbmcgui.DialogProgress()
        updateDialog.create("PseudoTV Live", "Initializing")
        self.backupFiles(updateDialog)
        ADDON_SETTINGS.loadSettings()
        
        if CHANNEL_SHARING:
            FileAccess.makedirs(LOCK_LOC)
            updateDialog.update(70, "Initializing", "Checking Other Instances")
            self.isMaster = GlobalFileLock.lockFile("MasterLock", False)
        else:
            self.isMaster = True

        updateDialog.update(95, "Initializing", "Migrating")

        if self.isMaster:
            migratemaster = Migrate()
            migratemaster.migrate()

        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)
        self.playerTimer.name = "PlayerTimer"
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.popTimer = threading.Timer(5.0, self.hidePOP)
        
        try:
            self.myEPG = EPGWindow("script.pseudotv.live.EPG.xml", ADDON_PATH, Skin_Select)
        except:
            self.myEPG = EPGWindow("script.pseudotv.EPG.xml", ADDON_PATH, Skin_Select)
            pass
            
        self.myEPG.MyOverlayWindow = self
        
        # Don't allow any actions during initialization
        self.actionSemaphore.acquire()
        updateDialog.close()
        self.timeStarted = time.time()
              
        if REAL_SETTINGS.getSetting("ATRestore") == "true" and REAL_SETTINGS.getSetting("Warning2") == "true":
            self.log('Setting2 Restore onInit') 
            if atsettingsFile_flesize != 0:
                REAL_SETTINGS.setSetting("ATRestore","false")
                REAL_SETTINGS.setSetting("Warning2","false")
                REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
                self.Restore(atsettingsFile, settingsFile)       
                return
                
        elif NormalShutdown == "false":
            xbmc.executebuiltin("Mute()");
            if settingsFile_flesize == 0 and nsettingsFile_flesize != 0:
                self.log('Setting2 Restore onInit') 
                self.Restore(nsettingsFile, settingsFile)
                return
        else:
            if settingsFile_flesize != 0:
                self.Backup(settingsFile, nsettingsFile)
        
        REAL_SETTINGS.setSetting('Normal_Shutdown', "false")
        
        if self.readConfig() == False:
            return
        
        self.myEPG.channelLogos = self.channelLogos
        self.maxChannels = len(self.channels)

        if self.maxChannels == 0 and REAL_SETTINGS.getSetting("Autotune") != "true":
            autoTune = False
            dlg = xbmcgui.Dialog()     
                
            if dlg.yesno("No Channels Configured", "Would you like PseudoTV Live to Auto Tune Channels?"):
                REAL_SETTINGS.setSetting("Autotune","true")
                REAL_SETTINGS.setSetting("Warning1","true")
                REAL_SETTINGS.setSetting("autoFindCustom","true")
                REAL_SETTINGS.setSetting("autoFindNetworks","true")
                REAL_SETTINGS.setSetting("autoFindMovieGenres","true")
                REAL_SETTINGS.setSetting("autoFindMixGenres","true")
                REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_RSS","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Plugins","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Networks","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Channels","true")
                autoTune = True
                
                if autoTune:
                    xbmc.executebuiltin('XBMC.AlarmClock( RestartPTVL, XBMC.RunScript(' + ADDON_PATH + '/default.py),0.5,false)')
                    self.end()
                    return 

            else:
                REAL_SETTINGS.setSetting("Autotune","false")
                REAL_SETTINGS.setSetting("Warning1","false")
                self.Error('Unable to find any channels. \nPlease go to the Addon Settings to configure PseudoTV Live.')
                REAL_SETTINGS.openSettings()
                self.end()
                return 
                
            del dlg
        
        else:
            if self.maxChannels == 0:
                self.Error('Unable to find any channels. Please configure the addon.')
                REAL_SETTINGS.openSettings()
                self.end()
                return

        found = False

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                found = True
                break

        if found == False:
            self.Error("Unable to populate channels. Please verify that you", "have scraped media in your library and that you have", "properly configured channels.")
            return

        if self.sleepTimeValue > 0:
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        self.notificationTimer = threading.Timer(NOTIFICATION_CHECK_TIME, self.notificationAction)

        try:
            if self.forceReset == False:
                self.currentChannel = self.fixChannel(int(REAL_SETTINGS.getSetting("CurrentChannel")))
            else:
                self.currentChannel = self.fixChannel(1)
        except:
            self.currentChannel = self.fixChannel(1)

        if REAL_SETTINGS.getSetting('INTRO_PLAYED') != 'true':
            self.background.setVisible(False)
            self.Player.play(INTRO)
            time.sleep(17) 
            self.background.setVisible(True)
            REAL_SETTINGS.setSetting("INTRO_PLAYED","true")
        
        self.resetChannelTimes()
        self.setChannel(self.currentChannel)
        self.background.setVisible(False)
        self.startSleepTimer()
        self.startNotificationTimer()
        self.playerTimer.start()

        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()
        else:
            self.ArtServiceThread = threading.Timer(float(self.InfTimer), self.Artdownloader.ArtService)
            self.ArtServiceThread.name = "ArtServiceThread"
            self.ArtServiceThread.start()

        self.actionSemaphore.release()
        self.log('onInit return')
    
    
    #SETTOP BOX
    def Settop(self):
        print 'SETTOP BOX Enabled'   
        self.channelList.setupList() 
        self.channelThread_Timer = threading.Timer(float(self.Refresh), self.Settop)
        self.channelThread_Timer.name = "ChannelThread_Timer"
        self.channelThread_Timer.start()
            

    def PlaybackValid(self):
        print 'PlaybackValid'   
        PlaybackStatus = 'False'
        if self.Player.isPlaying():
            print 'isPlaying'
            PlaybackStatus = 'True'
            
        print 'PlaybackStatus ' + str(PlaybackStatus)
        return PlaybackStatus
    

    # setup all basic configuration parameters, including creating the playlists that
    # will be used to actually run this thing
    def readConfig(self):
        self.log('readConfig')
        # Sleep setting is in 30 minute increments...so multiply by 30, and then 60 (min to sec)
        self.sleepTimeValue = int(REAL_SETTINGS.getSetting('AutoOff')) * 1800
        self.log('Auto off is ' + str(self.sleepTimeValue))
        self.infoOnChange = REAL_SETTINGS.getSetting("InfoOnChange") == "true"
        self.log('Show info label on channel change is ' + str(self.infoOnChange))
        self.showChannelBug = REAL_SETTINGS.getSetting("ShowChannelBug") == "true"
        self.log('Show channel bug - ' + str(self.showChannelBug))
        self.forceReset = REAL_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.channelResetSetting = REAL_SETTINGS.getSetting('ChannelResetSetting')
        self.log("Channel reset setting - " + str(self.channelResetSetting))
        self.channelLogos = xbmc.translatePath(REAL_SETTINGS.getSetting('ChannelLogoFolder'))
        self.backgroundUpdating = int(REAL_SETTINGS.getSetting("ThreadMode"))
        self.log("Background updating - " + str(self.backgroundUpdating))
        self.hideShortItems = REAL_SETTINGS.getSetting("HideClips") == "true"
        self.log("Hide Short Items - " + str(self.hideShortItems))
        self.shortItemLength = SHORT_CLIP_ENUM[int(REAL_SETTINGS.getSetting("ClipLength"))]
        self.log("Short item length - " + str(self.shortItemLength))
        self.channelDelay = int(REAL_SETTINGS.getSetting("ChannelDelay")) * 250


        if REAL_SETTINGS.getSetting("EnableComingUp") != "0":
            self.showNextItem = True
            
        if FileAccess.exists(self.channelLogos) == False:
            self.channelLogos = DEFAULT_LOGO_LOC
        self.log('Channel logo folder - ' + self.channelLogos)
        
        if SETTOP == 'true':
            self.channelThread_Timer = threading.Timer(float(self.Refresh), self.Settop)
            self.channelThread_Timer.name = "channelThread_Timer"
            self.channelThread_Timer.start()
           
        self.channelList = ChannelList()
        self.channelList.myOverlay = self
        self.channels = self.channelList.setupList()

        if self.channels is None:
            self.log('readConfig No channel list returned')
            self.end()
            return False

        self.Player.stop()
        self.log('readConfig return')
        return True

        
    # handle fatal errors: log it, show the dialog, and exit
    def Error(self, line1, line2 = '', line3 = ''):
        self.log('FATAL ERROR: ' + line1 + " " + line2 + " " + line3, xbmc.LOGFATAL)
        dlg = xbmcgui.Dialog()
        dlg.ok('Error', line1, line2, line3)
        del dlg
        self.end()

        
    def channelDown(self):
        self.log('channelDown')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel - 1, False)
        self.setChannel(channel)
        self.background.setVisible(False)         
        self.log('channelDown return')      
        
        
    def backupFiles(self, updatedlg):
        self.log('backupFiles')

        if CHANNEL_SHARING == False:
            return

        updatedlg.update(1, "Initializing", "Copying Channels...")
        realloc = REAL_SETTINGS.getSetting('SettingsFolder')
        FileAccess.copy(realloc + '/settings2.xml', SETTINGS_LOC + '/settings2.xml')
        realloc = xbmc.translatePath(os.path.join(realloc, 'cache')) + '/'

        for i in range(999):
            FileAccess.copy(realloc + 'channel_' + str(i) + '.m3u', CHANNELS_LOC + 'channel_' + str(i) + '.m3u')
            updatedlg.update(int(i * .07) + 1, "Initializing", "Copying Channels...")
        
        if FileAccess.exists(BCT_LOC) == True:
            try:
                self.copyanything(realloc + 'bct', CHANNELS_LOC + 'bct')
            except:
                pass

                
    def storeFiles(self):
        self.log('storeFiles')

        if CHANNEL_SHARING == False:
            return

        realloc = REAL_SETTINGS.getSetting('SettingsFolder')
        FileAccess.copy(SETTINGS_LOC + '/settings2.xml', realloc + '/settings2.xml')
        realloc = xbmc.translatePath(os.path.join(realloc, 'cache')) + '/'

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                FileAccess.copy(CHANNELS_LOC + 'channel_' + str(i) + '.m3u', realloc + 'channel_' + str(i) + '.m3u')


    def channelUp(self):
        self.log('channelUp')

        if self.maxChannels == 1:
            return

        self.background.setVisible(True)
        channel = self.fixChannel(self.currentChannel + 1)
        self.setChannel(channel)
        self.background.setVisible(False)
        self.log('channelUp return')

        
    def message(self, data):
        self.log('Dialog message: ' + data)
        dlg = xbmcgui.Dialog()
        dlg.ok('Info', data)
        del dlg


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('TVOverlay: ' + msg, level)

        
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('TVOverlay: ' + msg, level) 

            
    # set the channel, the proper show offset, and time offset
    def setChannel(self, channel):
        self.log('setChannel ' + str(channel))
        global seektime
        self.runActions(RULES_ACTION_OVERLAY_SET_CHANNEL, channel, self.channels[channel - 1])

        if self.Player.stopped:
            self.log('setChannel player already stopped', xbmc.LOGERROR);
            return

        if channel < 1 or channel > self.maxChannels:
            self.log('setChannel invalid channel ' + str(channel), xbmc.LOGERROR)
            return

        if self.channels[channel - 1].isValid == False:
            self.log('setChannel channel not valid ' + str(channel), xbmc.LOGERROR)
            return

        self.lastActionTime = 0
        timedif = 0
        self.getControl(102).setVisible(False)
        
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        self.getControl(103).setImage('')
        self.showingInfo = False
        self.showingPop = False

        # first of all, save playing state, time, and playlist offset for
        # the currently playing channel
        if self.Player.isPlaying():
            if channel != self.currentChannel:
                self.channels[self.currentChannel - 1].setPaused(xbmc.getCondVisibility('Player.Paused'))

                # Automatically pause in serial mode
                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE > 0:
                    self.channels[self.currentChannel - 1].setPaused(True)

                self.channels[self.currentChannel - 1].setShowTime(self.Player.getTime())
                self.channels[self.currentChannel - 1].setShowPosition(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition())
                self.channels[self.currentChannel - 1].setAccessTime(time.time())

        self.currentChannel = channel
        # now load the proper channel playlist
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        self.log("about to load");

        if xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(self.channels[channel - 1].fileName) == False:
            self.log("Error loading playlist", xbmc.LOGERROR)
            self.InvalidateChannel(channel)
            return

        # Disable auto playlist shuffling if it's on
        if xbmc.getInfoLabel('Playlist.Random').lower() == 'random':
            self.log('Random on.  Disabling.')
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).unshuffle()
  
        self.log("repeat all");
        xbmc.executebuiltin("PlayerControl(repeatall)")
        curtime = time.time()
        timedif = (curtime - self.channels[self.currentChannel - 1].lastAccessTime)
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
        except:
            chtype = ''
            pass
        
        if self.channels[self.currentChannel - 1].isPaused == False:
            # adjust the show and time offsets to properly position inside the playlist
            #for Live TV get the first item in playlist convert to epoch time  add duration until we get to the current item
            if chtype == 8:
                self.channels[self.currentChannel - 1].setShowPosition(0)
                tmpDate = self.channels[self.currentChannel - 1].getItemtimestamp(0)
                self.log("overlay tmpdate " + str(tmpDate))
                
                try:#sloppy fix, for threading issue with strptime.
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                except:
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    pass
                    
                epochBeginDate = time.mktime(t)
                #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                #index till we get to the current show
                while epochBeginDate + self.channels[self.currentChannel - 1].getCurrentDuration() <  curtime:
                    self.log('epoch '+ str(epochBeginDate) + ', ' + 'time ' + str(curtime))
                    epochBeginDate += self.channels[self.currentChannel - 1].getCurrentDuration()
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    self.log('live tv overlay while loop')
            else:   #loop for other channel types
                while self.channels[self.currentChannel - 1].showTimeOffset + timedif > self.channels[self.currentChannel - 1].getCurrentDuration():
                    timedif -= self.channels[self.currentChannel - 1].getCurrentDuration() - self.channels[self.currentChannel - 1].showTimeOffset
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    self.channels[self.currentChannel - 1].setShowTime(0)

        # First, check to see if the video is a strm
        if self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)[-4:].lower() == 'strm' or chtype == 8 or chtype == 9:
            self.log("Ignoring a stop because of a strm or chtype = 8 or 9")
            self.Player.ignoreNextStop = True
        
        self.log("about to mute");
        # Mute the channel before changing
        xbmc.executebuiltin("Mute()");           
        xbmc.sleep(self.channelDelay)
        # set the show offset
        self.Player.playselected(self.channels[self.currentChannel - 1].playlistPosition)
        self.log("playing selected file");
        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(curtime)
        mediapath = self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)

        try:
            plugchk = mediapath.split('/')[2]
        except:
            plugchk = mediapath
            pass
                    
        if self.channels[self.currentChannel - 1].isPaused:
            self.channels[self.currentChannel - 1].setPaused(False)
          
            if chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                self.log("Seeking")
                try:
                    self.Player.seekTime(self.channels[self.currentChannel - 1].showTimeOffset)

                    if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE == 0:
                        self.Player.pause()

                        if self.waitForVideoPaused() == False:
                            xbmc.executebuiltin("Mute()");
                            return
                except:
                    self.log('Exception during seek on paused channel', xbmc.LOGERROR)
                    pass
        else:
                
            if chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                self.log("Seeking")
                # Seek without infobar work around todo? needs testing...
                # http://forum.xbmc.org/showthread.php?pid=1547665#pid1547665
                seektime1 = self.channels[self.currentChannel - 1].showTimeOffset + timedif + int((time.time() - curtime))
                seektime2 = self.channels[self.currentChannel - 1].showTimeOffset + timedif
                overtime = float((int(self.channels[self.currentChannel - 1].getItemDuration(self.channels[self.currentChannel - 1].playlistPosition))/8)*6)
        
                if (mediapath[-4:].lower() == 'strm' or mediapath.startswith('plugin')):
                    seektime = self.SmartSeek(mediapath, seektime1, seektime2, overtime)
                    self.PlayUPNP(mediapath, seektime)
                else:
                    try:
                        self.log("Seeking");
                        self.Player.seekTime(seektime1)
                        seektime = seektime1
                    except:
                        self.log("Unable to set proper seek time, trying different value")
                        try:
                            self.Player.seekTime(seektime2)
                            seektime = seektime2
                        except:
                            self.log('Exception during seek', xbmc.LOGERROR)
                            pass     
                    
                    self.PlayUPNP(mediapath, seektime)   
        
        # Unmute
        self.log("Finished, unmuting");
        xbmc.executebuiltin("Mute()");
        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
        self.runActions(RULES_ACTION_OVERLAY_SET_CHANNEL_END, channel, self.channels[channel - 1])
        
        # if not self.PlaybackValid():
            # self.Player.playnext()

        self.log('setChannel return')
        
            
    def SmartSeek(self, mediapath, seektime1, seektime2, overtime):
        self.log("SmartSeek")
        seektime = 0
        if seektime1 < overtime:
            try:
                self.log("Seeking");
                self.Player.seekTime(seektime1)
                seektime = seektime1
            except:
                self.log("Unable to set proper seek time, trying different value")
                if seektime2 < overtime:
                    try:
                        self.Player.seekTime(seektime2)
                        seektime = seektime2
                    except:
                        self.log('Exception during seek', xbmc.LOGERROR)
                        pass
                else:
                    pass
        
        if seektime == 0 and DEBUG == 'true':
            self.log('seektime' + str(seektime))
            self.log('overtime' + str(overtime))
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Overriding Seektime", 1000, THUMB) )

        return seektime    

        
    def PlayUPNP(self, file, seektime):
        self.log("PlayUPNP")
        #UPNP
        file = file.replace("\\\\","\\")
        if REAL_SETTINGS.getSetting("UPNP1") == "true":
            self.log('UPNP1 Sharing')
            UPNP1 = SendUPNP(IPP1, file, seektime)
        if REAL_SETTINGS.getSetting("UPNP2") == "true":
            self.log('UPNP2 Sharing')
            UPNP2 = SendUPNP(IPP2, file, seektime)
        if REAL_SETTINGS.getSetting("UPNP3") == "true":
            self.log('UPNP3 Sharing')
            UPNP3 = SendUPNP(IPP3, file, seektime)

            
    def InvalidateChannel(self, channel):
        self.log("InvalidateChannel" + str(channel))

        if channel < 1 or channel > self.maxChannels:
            self.log("InvalidateChannel invalid channel " + str(channel))
            return

        self.channels[channel - 1].isValid = False
        self.invalidatedChannelCount += 1

        if self.invalidatedChannelCount > 3:
            self.Error("Exceeded 3 invalidated channels. Exiting.")
            return

        remaining = 0

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                remaining += 1

        if remaining == 0:
            self.Error("No channels available. Exiting.")
            return

        self.setChannel(self.fixChannel(channel))
    
    
    def waitForVideoPaused(self):
        self.log('waitForVideoPaused')
        sleeptime = 0

        while sleeptime < TIMEOUT:
            xbmc.sleep(100)

            if self.Player.isPlaying():
                if xbmc.getCondVisibility('Player.Paused'):
                    break

            sleeptime += 100
        else:
            self.log('Timeout waiting for pause', xbmc.LOGERROR)
            return False

        self.log('waitForVideoPaused return')
        return True

        
    def setShowInfo(self):
        self.log('setShowInfo')
        mpath = ''
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
        except:
            chtype = ''
            pass
  
        try:
            self.getControl(101).setLabel('Loading Channel...')
        except:
            pass
            
        try:
            if self.infoOffset > 0:
                self.getControl(502).setLabel('COMING UP:') 
                
                try:
                    self.getControl(515).setVisible(False)    
                except:
                    pass
                
            elif self.infoOffset < 0:
                self.getControl(502).setLabel('ALREADY SEEN:') 
                
                try:
                    self.getControl(515).setVisible(False)    
                except:
                    pass

            elif self.infoOffset == 0:
                self.getControl(502).setLabel('NOW WATCHING:')
                
                try:
                    self.getControl(515).setVisible(True)    
                except:
                    pass
        except:   
            pass
            
        if self.hideShortItems and self.infoOffset != 0:
            position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            curoffset = 0
            modifier = 1

            if self.infoOffset < 0:
                modifier = -1

            while curoffset != abs(self.infoOffset):
                position = self.channels[self.currentChannel - 1].fixPlaylistIndex(position + modifier)

                if self.channels[self.currentChannel - 1].getItemDuration(position) >= self.shortItemLength:
                    curoffset += 1
        else:
            #same logic as in setchannel; loop till we get the current show
            if chtype == 8:
                self.channels[self.currentChannel - 1].setShowPosition(0)
                tmpDate = self.channels[self.currentChannel - 1].getItemtimestamp(0)
                 
                try:#sloppy fix, for threading issue with strptime.
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                except:
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    pass
                 
                epochBeginDate = time.mktime(t)
                position = self.channels[self.currentChannel - 1].playlistPosition
                #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                #loop till we get to the current show this is done to display the correct show on the info listing for Live TV types
                while epochBeginDate + self.channels[self.currentChannel - 1].getCurrentDuration() <  time.time():
                    epochBeginDate += self.channels[self.currentChannel - 1].getCurrentDuration()
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    position = self.channels[self.currentChannel - 1].playlistPosition
            else: #original code
                position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
        
        mediapath = (self.channels[self.currentChannel - 1].getItemFilename(position))
        genre = (self.channels[self.currentChannel - 1].getItemgenre(position))
        title = (self.channels[self.currentChannel - 1].getItemTitle(position))
        LiveID = (self.channels[self.currentChannel - 1].getItemLiveID(position))
        EpisodeTitle = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(position))
        chname = (self.channels[self.currentChannel - 1].name)
        
        if mediapath[0:5] == 'stack':
            smpath = (mediapath.split(' , ')[0]).replace('stack://','')
            mpath = (os.path.split(smpath)[0])
        elif mediapath.startswith('plugin://plugin.video.bromix.youtube') or mediapath.startswith('plugin://plugin.video.youtube/?path=/root'):
            mpath = (os.path.split(mediapath)[0])
            YTid = mediapath.split('id=')[1]
            mpath = (mpath + '/' + YTid).replace('/?path=/root','')
        else:
            mpath = (os.path.split(mediapath)[0])
        
        self.PVRchtype = chtype
        self.PVRmediapath = mediapath
        self.PVRchname = chname
        self.PVRtitle = title
        
        LiveID = self.channelList.unpackLiveID(LiveID)
        type = LiveID[0]
        id = LiveID[1]
        Managed = LiveID[3]
        playcount = int(LiveID[4])

        # Unwatch Local Media if applicable    
        if REAL_SETTINGS.getSetting("Disable_Watched") == "true" and self.Player.stopped:
            if chtype <= 6 and id != '0':
                if type == 'tvshow':
                    media_type = 'episode'
                    try:
                        EPtitle = EpisodeTitle.split(' -')[0]
                        season = EPtitle.split('x')[0]
                        episode = EPtitle.split('x')[1]
                    except Exception,e:
                        EPtitle = EpisodeTitle.split(' -')[0]
                        season = (EPtitle.split('E')[0]).replace('S','')
                        episode = EPtitle.split('E')[1]
                    except Exception,e:
                        season = 0
                        episode = 0
                        pass
                else:
                    media_type = 'movie'
                    season = ''
                    episode = ''
                    self.Unwatch(media_type, title, id, season, episode, '', playcount)
                    
        SEtitle = self.channels[self.currentChannel - 1].getItemEpisodeTitle(position)

        try:
            if self.showSeasonEpisode:
                SEinfo = SEtitle.split(' -')[0]
                season = int(SEinfo.split('x')[0])
                episode = int(SEinfo.split('x')[1])
                eptitles = SEtitle.split('- ')
                eptitle = (eptitles[1] + (' - ' + eptitles[2] if len(eptitles) > 2 else ''))
                swtitle = ('S' + ('0' if season < 10 else '') + str(season) + 'E' + ('0' if episode < 10 else '') + str(episode) + ' - ' + (eptitle)).replace('  ',' ')
            else:
                swtitle = SEtitle      
        except:
            swtitle = SEtitle
            pass

        self.log('setshowposition ' + str(position))        
        self.getControl(503).setLabel((self.channels[self.currentChannel - 1].getItemTitle(position)).replace("*NEW*",""))
        self.getControl(504).setLabel(swtitle)
        self.getControl(505).setLabel(self.channels[self.currentChannel - 1].getItemDescription(position))
        self.getControl(506).setImage(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png') 
        
        if REAL_SETTINGS.getSetting("DynamicArt_Enabled") == "true" and REAL_SETTINGS.getSetting("ArtService_Enabled") == "true":  
            self.log('Dynamic artwork enabled')
            
            #hide xbmc.videoplayer art since using dynamic art
            try:
                self.getControl(513).setVisible(False)
            except:
                pass  
                
            #Sickbeard/Couchpotato == Managed
            try:
                if Managed == 'True':
                    self.getControl(511).setVisible(True)  
                    if type == 'tvshow':
                        self.getControl(511).setImage(IMAGES_LOC + 'SB.png')
                    else:
                        self.getControl(511).setImage(IMAGES_LOC + 'CP.png')                          
                else:
                    self.getControl(511).setVisible(False)  
            except:
                pass     
                
            #Unaired/aired == Playcount 0 = New
            try:
                self.getControl(512).setVisible(True)
                if playcount == 0:
                    self.getControl(512).setImage(MEDIA_LOC + 'NEW.png')
                elif playcount >= 1:
                    self.getControl(512).setImage(MEDIA_LOC + 'OLD.png')      
                else:
                    self.getControl(512).setVisible(False)      
            except:
                pass  

            try:
                type1 = str(self.getControl(507).getLabel())
                type1EXT = self.Artdownloader.EXTtype(type1)
                self.setArtwork1(type, chtype, id, mpath, type1EXT)
            except:
                print 'setShowInfo.Label 507 not found'
                pass
               
            try:
                type2 = str(self.getControl(509).getLabel())
                type2EXT = self.Artdownloader.EXTtype(type2)
                self.setArtwork2(type, chtype, id, mpath, type2EXT)
            except:
                print 'setShowInfo.Label 509 not found'
                pass
        else:
            #use xbmc.videoplayer art since not using dynamic art
            try:
                self.getControl(508).setImage('NA.png')   
            except:
                pass   
            try:
                self.getControl(510).setImage('NA.png') 
            except:
                pass   
            try:
                self.getControl(511).setImage('NA.png') 
            except:
                pass   
            try:
                self.getControl(512).setImage('NA.png') 
            except:
                pass   
            try:
                self.getControl(513).setVisible(True)
            except:
                pass  

        self.log('setShowInfo return')
        
        
    def setArtwork1(self, type, chtype, id, mpath, type1EXT):
        self.log('setArtwork1')
        try:
            self.getControl(508).setImage('NA.png')
            setImage1 = self.Artdownloader.FindArtwork_NEW(type, chtype, id, mpath, type1EXT)
            self.getControl(508).setImage(setImage1)
        except:
            pass  
    
    
    def setArtwork2(self, type, chtype, id, mpath, type2EXT):
        self.log('setArtwork2')
        try: 
            self.getControl(510).setImage('NA.png')
            setImage2 = self.Artdownloader.FindArtwork_NEW(type, chtype, id, mpath, type2EXT)
            self.getControl(510).setImage(setImage2)
        except:
            pass
    
    
    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
        except:
            chtype = ''
            pass

        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

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

        if self.inputChannel == -1 and self.infoOnChange == True:
            self.infoOffset = 0
            self.showInfo(self.InfTimer)

        if xbmc.getCondVisibility('Player.ShowInfo'):
            json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
            self.ignoreInfoAction = True
            self.channelList.sendJSON(json_query);
            
        try:
            if self.showChannelBug == True:
                if chtype != 8:
                    if REAL_SETTINGS.getSetting('COLOR_CHANBUG') == 'false':
                    
                        if not FileAccess.exists(LOGO_CACHE_LOC):
                            FileAccess.makedirs(LOGO_CACHE_LOC)
                            
                        if FileAccess.exists(LOGO_CACHE_LOC + (self.channels[self.currentChannel - 1].name) + '.png'):
                            self.getControl(103).setImage(LOGO_CACHE_LOC + (self.channels[self.currentChannel - 1].name) + '.png')
                        
                        else:
                            if FileAccess.exists(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png'):
                                original = Image.open(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png')                  
                                converted_img = original.convert('LA')
                                converted_img.save(LOGO_CACHE_LOC + (self.channels[self.currentChannel - 1].name) + '.png')
                                self.getControl(103).setImage(LOGO_CACHE_LOC + (self.channels[self.currentChannel - 1].name) + '.png')
                            else:
                                self.getControl(103).setImage(IMAGES_LOC + 'Default.png')
                    else:
                        if FileAccess.exists(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png'):
                            self.getControl(103).setImage(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png')
                        else:
                            self.getControl(103).setImage(IMAGES_LOC + 'Default.png')
            else:
                self.getControl(103).setImage('NA.png')
        except:
            pass
                
        # Channel name label #      
        try:
            self.getControl(300).setLabel(self.channels[self.currentChannel - 1].name)
        except:
            pass
            
        self.channelLabelTimer.name = "ChannelLabel"
        self.channelLabelTimer.start()
        self.startNotificationTimer(10.0)
        self.log('showChannelLabel return')


    # Called from the timer to hide the channel label.
    def hideChannelLabel(self):
        self.log('hideChannelLabel')
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)

        for i in range(3):
            self.channelLabel[i].setVisible(False)

        self.inputChannel = -1
        self.log('hideChannelLabel return')

        
    def hideInfo(self):
        self.getControl(102).setVisible(False)
        self.infoOffset = 0
        self.showingInfo = False

        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(5.0, self.hideInfo)

        
    def showInfo(self, timer):
    
        if self.hideShortItems:
            position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
            
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
            except:
                chtype = ''
                pass

            if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(position) < self.shortItemLength:
                return

        self.getControl(102).setVisible(True)
        
        if xbmc.getCondVisibility('Player.ShowInfo'):
            json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
            self.ignoreInfoAction = True
            self.channelList.sendJSON(json_query);

        if self.showingPop == False:
            self.showingInfo = True
            self.setShowInfo()

        if self.infoTimer.isAlive():
            self.infoTimer.cancel()

        self.infoTimer = threading.Timer(timer, self.hideInfo)
        self.infoTimer.name = "InfoTimer"
            
        self.infoTimer.start()
        
        
    def hidePOP(self):
        self.log("hidePOP")
        self.infoOffset = 0
        self.showingPop = False
        
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        if self.popTimer.isAlive():
            self.popTimer.cancel()

        self.popTimer = threading.Timer(5.0, self.hidePOP)
        self.getControl(103).setVisible(True)
        

    def showPOP(self, timer):
        self.log("showPOP")
        #disable channel bug
        self.getControl(103).setVisible(False)

        if self.hideShortItems:
            position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
            
            if self.channels[self.currentChannel - 1].getItemDuration(position) < self.shortItemLength:
                return
            
        if self.showingInfo == False:
            try:
                self.showingPop = True
                self.getControl(120).setVisible(True)
            except:
                pass
            
        if self.popTimer.isAlive():
            self.popTimer.cancel()

        self.popTimer = threading.Timer(timer, self.hidePOP)
        self.popTimer.name = "popTimer"
            
        self.popTimer.start()
            
            
    # return a valid channel in the proper range
    def fixChannel(self, channel, increasing = True):
        while channel < 1 or channel > self.maxChannels:
            if channel < 1: channel = self.maxChannels + channel
            if channel > self.maxChannels: channel -= self.maxChannels

        if increasing:
            direction = 1
        else:
            direction = -1

        if self.channels[channel - 1].isValid == False:
            return self.fixChannel(channel + direction, increasing)

        return channel


    # Handle all input while videos are playing
    def onAction(self, act):
        action = act.getId()
        self.log('onAction ' + str(action))
        
        try:
            chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
            mediapath = self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)
            
            try:
                plugchk = mediapath.split('/')[2]
            except:
                plugchk = mediapath
                pass
        except:
            pass
        
        if self.Player.stopped:
            return

        # Since onAction isnt always called from the same thread (weird),
        # ignore all actions if we're in the middle of processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        lastaction = time.time() - self.lastActionTime

        # during certain times we just want to discard all input
        if lastaction < 2:
            self.log('Not allowing actions')
            if chtype >= 7:
                action = ACTION_INVALID

        self.startSleepTimer()

        if action == ACTION_SELECT_ITEM:
            # If we're manually typing the channel, set it now
            if self.inputChannel > 0:
                if self.inputChannel != self.currentChannel:
                    self.setChannel(self.inputChannel)

                self.inputChannel = -1
            else:
                # Otherwise, show the EPG
                if self.channelThread.isAlive():
                    self.channelThread.pause()

                if self.notificationTimer.isAlive():
                    self.notificationTimer.cancel()
                    self.notificationTimer = threading.Timer(NOTIFICATION_CHECK_TIME, self.notificationAction)

                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

                self.hideInfo()
                self.hidePOP()
                self.newChannel = 0
                self.myEPG.doModal()

                if self.channelThread.isAlive():
                    self.channelThread.unpause()

                self.startNotificationTimer()

                if self.newChannel != 0:
                    self.background.setVisible(True)
                    self.setChannel(self.newChannel)
                    self.background.setVisible(False)
                    
        elif action == ACTION_MOVE_UP or action == ACTION_PAGEUP:
            self.channelUp()
        
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            self.channelDown()

        elif action == ACTION_MOVE_LEFT:
            if self.showingInfo:
                self.infoOffset -= 1
                self.showInfo(self.InfTimer)
            elif chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                xbmc.executebuiltin("PlayerControl(SmallSkipBackward)")
                self.log("SmallSkipBackward")
                           
                if REAL_SETTINGS.getSetting("UPNP1") == "true":
                    self.log('UPNP1 RW')
                    UPNP1 = RWUPNP(IPP1)
                if REAL_SETTINGS.getSetting("UPNP2") == "true":
                    self.log('UPNP2 RW')
                    UPNP2 = RWUPNP(IPP2)
                if REAL_SETTINGS.getSetting("UPNP3") == "true":
                    self.log('UPNP3 RW')
                    UPNP3 = RWUPNP(IPP3)

        elif action == ACTION_MOVE_RIGHT:
            if self.showingInfo:
                self.infoOffset += 1
                self.showInfo(self.InfTimer)
            elif chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                xbmc.executebuiltin("PlayerControl(SmallSkipForward)")
                self.log("SmallSkipForward")
        
                try:
                    if REAL_SETTINGS.getSetting("UPNP1") == "true":
                        self.log('UPNP1 FF')
                        UPNP1 = FFUPNP(IPP1)
                    if REAL_SETTINGS.getSetting("UPNP2") == "true":
                        self.log('UPNP2 FF')
                        UPNP2 = FFUPNP(IPP2)
                    if REAL_SETTINGS.getSetting("UPNP3") == "true":
                        self.log('UPNP3 FF')
                        UPNP3 = FFUPNP(IPP3)
                except:
                    pass
                    
        elif action in ACTION_PREVIOUS_MENU:
            if self.showingInfo:
                self.hideInfo()
                self.hidePOP()
            else:
                dlg = xbmcgui.Dialog()

                if self.sleepTimeValue > 0:
                    if self.sleepTimer.isAlive():
                        self.sleepTimer.cancel()
                        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

                if dlg.yesno("Exit?", "Are you sure you want to exit PseudoTV Live?"):
                    self.end()
                    return  # Don't release the semaphore
                else:
                    self.startSleepTimer()

                del dlg
        
        elif action == ACTION_SHOW_INFO:
            if self.ignoreInfoAction:
                self.ignoreInfoAction = False
            else:
                if self.showingInfo:
                    self.hideInfo()
                    self.hidePOP()

                    if xbmc.getCondVisibility('Player.ShowInfo'):
                        json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
                        self.ignoreInfoAction = True
                        self.channelList.sendJSON(json_query);
  
                else:
                    self.showInfo(self.InfTimer)
        
        elif action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            if self.inputChannel < 0:
                self.inputChannel = action - ACTION_NUMBER_0
            else:
                if self.inputChannel < 100:
                    self.inputChannel = self.inputChannel * 10 + action - ACTION_NUMBER_0

            CurChannel = self.fixChannel(self.currentChannel)
            REAL_SETTINGS.setSetting('LastChannel', str(CurChannel))
            self.showChannelLabel(self.inputChannel)
        
        elif action == ACTION_SHOW_SUBTITLES:
            xbmc.executebuiltin("ActivateWindow(SubtitleSearch)")
            
        elif action == ACTION_AUDIO_NEXT_LANGUAGE:
            xbmc.executebuiltin("ActivateWindow(NextSubtitle)")
            
        elif action == ACTION_SHOW_CODEC:
            xbmc.executebuiltin("ActivateWindow(CodecInfo)")
            
        elif action == ACTION_ASPECT_RATIO:
            json_query = '{"jsonrpc": "2.0", "method": "Input.ExecuteAction","params":{"action":"aspectratio"}, "id": 1}'
            self.channelList.sendJSON(json_query);

        elif action == ACTION_RECORD:
            self.log('ACTION_RECORD')
            PVRrecord(self.PVRchtype, self.PVRmediapath, self.PVRchname, self.PVRtitle)
        
        elif action == ACTION_SHIFT: #Previous channel button
            self.log('ACTION_SHIFT')
            self.LastChannel = int(REAL_SETTINGS.getSetting('LastChannel'))
            CurChannel = self.fixChannel(self.currentChannel)
            REAL_SETTINGS.setSetting('LastChannel', str(CurChannel))
            self.setChannel(self.LastChannel)
                    
        # elif action == ACTION_OSD:
            # xbmc.executebuiltin("ActivateWindow(12901)")
        
        self.actionSemaphore.release()
        self.log('onAction return')


    # Reset the sleep timer
    def startSleepTimer(self):
        if self.sleepTimeValue == 0:
            return

        # Cancel the timer if it is still running
        if self.sleepTimer.isAlive():
            self.sleepTimer.cancel()
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

        if self.Player.stopped == False:
            self.sleepTimer.name = "SleepTimer"
            self.sleepTimer.start()


    def startNotificationTimer(self, timertime = NOTIFICATION_CHECK_TIME):
        self.log("startNotificationTimer")

        if self.notificationTimer.isAlive():
            self.notificationTimer.cancel()

        self.notificationTimer = threading.Timer(timertime, self.notificationAction)

        if self.Player.stopped == False:
            self.notificationTimer.name = "NotificationTimer"
            self.notificationTimer.start()


    # This is called when the sleep timer expires
    def sleepAction(self):
        self.log("sleepAction")
        self.actionSemaphore.acquire()
#        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
        # TODO: show some dialog, allow the user to cancel the sleep
        # perhaps modify the sleep time based on the current show
        self.end()


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
                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter


    def notificationAction(self):
        self.log("notificationAction")
        ClassicPOPUP = False
        docheck = False
        # chname = (self.channels[self.currentChannel - 1].name)
        
        # if chname in BYPASS_OVERLAY: #Disable shownext for CE, move to rules todo
            # return

        if self.Player.isPlaying():
            if self.notificationLastChannel != self.currentChannel:
                docheck = True
            else:
                if self.notificationLastShow != xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition():
                    docheck = True
                else:
                    if self.notificationShowedNotif == False:
                        docheck = True

            if docheck == True:
                self.notificationLastChannel = self.currentChannel
                self.notificationLastShow = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                self.notificationShowedNotif = False

                if self.hideShortItems:
                    # Don't show any notification if the current show is < 60 seconds
                    if self.channels[self.currentChannel - 1].getItemDuration(self.notificationLastShow) < self.shortItemLength:
                        self.notificationShowedNotif = True
                        
                timedif = self.channels[self.currentChannel - 1].getItemDuration(self.notificationLastShow) - self.Player.getTime()
                if self.notificationShowedNotif == False and timedif < NOTIFICATION_TIME_BEFORE_END and timedif > NOTIFICATION_DISPLAY_TIME:
                    nextshow = self.channels[self.currentChannel - 1].fixPlaylistIndex(self.notificationLastShow + 1)
                    
                    if self.hideShortItems:
                        # Find the next show that is >= 60 seconds long
                        while nextshow != self.notificationLastShow:
                            if self.channels[self.currentChannel - 1].getItemDuration(nextshow) >= self.shortItemLength:
                                break
                                
                            nextshow = self.channels[self.currentChannel - 1].fixPlaylistIndex(nextshow + 1)
                    
                    self.log('notification.init')     
                    mediapath = (self.channels[self.currentChannel - 1].getItemFilename(nextshow))
                    THUMB = (IMAGES_LOC + 'icon.png')
                    ChannelLogo = (self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png')
                    
                    try:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel - 1) + '_type'))
                    except:
                        chtype = ''
                        pass
                        
                    title = 'Coming Up Next'   
                    ShowTitle = self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', '')
                    myLiveID = self.channels[self.currentChannel - 1].getItemLiveID(nextshow)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    youtube = ['plugin://plugin.video.bromix.youtube', 'plugin://plugin.video.youtube/?path=/root']
        
                    if mediapath[0:5] == 'stack':
                        smpath = (mediapath.split(' , ')[0]).replace('stack://','')
                        mpath = (os.path.split(smpath)[0])
                    else:
                        mpath = (os.path.split(mediapath)[0])
                    
                    if mpath in youtube:
                        YTid = mediapath.split('id=')[1]
                        mpath = (mpath + '/' + YTid).replace('/?path=/root','')
                    
                    try:
                        ShowEpisode = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(nextshow).replace(',', ''))
                        ShowEpisode = ShowEpisode.split("- ")[1]
                    except:
                        ShowEpisode = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(nextshow).replace(',', ''))
                        pass

                    ArtType = {}
                    ArtType['0'] = 'poster'
                    ArtType['1'] = 'fanart' 
                    ArtType['2'] = 'landscape'        
                    ArtType['3'] = 'logo'       
                    ArtType['4'] = 'clearart'              
                    ArtType = ArtType[REAL_SETTINGS.getSetting('ComingUpArtwork')] #notification art type for classic
                        
                    try:
                        ArtType = str(self.getControl(121).getLabel()) #notification art type for new overlay
                        self.getControl(123).setLabel(title)
                        self.getControl(124).setLabel(ShowTitle)
                        self.getControl(125).setLabel(ShowEpisode)
                    except:
                        ClassicPOPUP = True
                        pass

                    typeEXT = self.Artdownloader.EXTtype(ArtType)
                    self.log('notification.type.ext = ' + str(typeEXT))  
                    THUMB = self.Artdownloader.FindArtwork_NEW(type, chtype, id, mpath, typeEXT)
                    self.log("notification.plugin.thumb = " + THUMB)   
                    
                    if self.showingInfo == False and self.notificationShowedNotif == False:
                        if REAL_SETTINGS.getSetting("EnableComingUp") == "2" or ClassicPOPUP == True:
                            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (title, self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', ''), str(NOTIFICATION_DISPLAY_TIME * 2000), THUMB))
                        else:
                            self.getControl(122).setImage(THUMB)
                            self.showPOP(self.InfTimer + 2.5)

                    self.log("notification.THUMB = " + (THUMB))
                    self.notificationShowedNotif = True
                    
        self.startNotificationTimer()


    def playerTimerAction(self):
        self.log("playerTimerAction")
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)  
        position = self.channels[self.currentChannel - 1].playlistPosition  
        genre = (self.channels[self.currentChannel - 1].getItemgenre(position))
            
        try:
            self.getControl(101).setLabel('Loading Channel...')
        except:
            pass
        
        if genre == 'Bumper' or genre == 'Rating' or genre == 'Commercial' or genre == 'Trailer':
            BCT = True
        else:
            BCT = False
            
        if self.Player.isPlaying():
            self.lastPlayTime = int(self.Player.getTime())
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            self.notPlayingCount = 0                
        else:
            #Ignore BCT's to avoid notPlayingCount loop on a dead channel.
            if not BCT:
                self.notPlayingCount += 1
                self.log("Adding to notPlayingCount, " + str(self.notPlayingCount))  
                
                if DEBUG == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "notPlayingCount " + str(self.notPlayingCount), 1000, THUMB) )
                      
        if self.notPlayingCount > 3:
            try:
                self.getControl(101).setLabel('Error Loading: Changing Channel')
            except:
                pass
            
            self.channelUp()
            self.log("error three peat invalid channel, Changing Channel")
            return
            
        if self.Player.stopped == False:
            self.playerTimer.name = "PlayerTimer"
            self.playerTimer.start()
    
    
    def Unwatch(self, type, title, imdbid, season, episode, year, watched):
        self.log('Unwatch')
        try:        
            from metahandler import metahandlers
            self.metaget = metahandlers.MetaData(preparezip = False)
            self.metaget.change_watched(type, title, imdbid, season=season, episode=episode, year='', watched=watched)
        except:
            self.log('Unwatch Failed')
            pass
        

    def end(self):
        self.log('end')     
        
        try:
            self.getControl(101).setLabel('Exiting...')
        except:
            pass
            
        # Prevent the player from setting the sleep timer
        self.Player.stopped = True
        self.background.setVisible(True)
        
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        curtime = time.time()
        xbmc.executebuiltin("PlayerControl(repeatoff)")
        self.isExiting = True
        updateDialog = xbmcgui.DialogProgress()
        updateDialog.create("PseudoTV Live", "Exiting")
              
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                UPNP1 = StopUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                UPNP2 = StopUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                UPNP3 = StopUPNP(IPP3)
        except:
            pass
        
        if CHANNEL_SHARING and self.isMaster:
            updateDialog.update(0, "Exiting", "Removing File Locks")
            GlobalFileLock.unlockFile('MasterLock')
        
        GlobalFileLock.close()
        
        try:
            if self.playerTimer.isAlive():
                self.playerTimer.cancel()
                self.playerTimer.join()
        except:
            pass
   
        try:
            if self.channelThread_Timer.isAlive():
                self.channelThread_Timer.cancel()
                self.channelThread_Timer.join()
        except:
            pass

        try:
            if self.ArtServiceThread.isAlive():
                self.ArtServiceThread.cancel()
                self.ArtServiceThread.join()
        except:
            pass
            
        if self.Player.isPlaying():
            self.lastPlayTime = self.Player.getTime()
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
            self.Player.stop()

        updateDialog.update(1, "Exiting", "Stopping Threads")

        try:
            if self.channelLabelTimer.isAlive():
                self.channelLabelTimer.cancel()
                self.channelLabelTimer.join()
        except:
            pass

        updateDialog.update(2)

        try:
            if self.notificationTimer.isAlive():
                self.notificationTimer.cancel()
                self.notificationTimer.join()
        except:
            pass

        updateDialog.update(3)

        try:
            if self.infoTimer.isAlive():
                self.infoTimer.cancel()
                self.infoTimer.join()
        except:
            pass

        updateDialog.update(4)

        try:
            if self.sleepTimeValue > 0:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
        except:
            pass

        updateDialog.update(5)

        if self.channelThread.isAlive():
            for i in range(30):
                try:
                    self.channelThread.join(1.0)
                except:
                    pass

                if self.channelThread.isAlive() == False:
                    break

                updateDialog.update(6 + i, "Exiting", "Stopping Threads")

            if self.channelThread.isAlive():
                self.log("Problem joining channel thread", xbmc.LOGERROR)

        if self.isMaster:
        
            try:#Startup Channel
                SUPchannel = int(REAL_SETTINGS.getSetting('SUPchannel'))                
                if SUPchannel == 0:
                    REAL_SETTINGS.setSetting('CurrentChannel', str(self.currentChannel))    
            except:
                pass

            ADDON_SETTINGS.setSetting('LastExitTime', str(int(curtime)))

        if self.timeStarted > 0 and self.isMaster:
            updateDialog.update(35, "Exiting", "Saving Settings")
            validcount = 0

            for i in range(self.maxChannels):
                if self.channels[i].isValid:
                    validcount += 1
            
            if validcount > 0:
                incval = 65.0 / float(validcount)

                for i in range(self.maxChannels):
                    updateDialog.update(35 + int((incval * i)))

                    if self.channels[i].isValid:
                        if self.channels[i].mode & MODE_RESUME == 0:
                            ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(curtime - self.timeStarted + self.channels[i].totalTimePlayed)))

                        else:
                            if i == self.currentChannel - 1:
                                # Determine pltime...the time it at the current playlist position
                                pltime = 0
                                self.log("position for current playlist is " + str(self.lastPlaylistPosition))

                                for pos in range(self.lastPlaylistPosition):
                                    pltime += self.channels[i].getItemDuration(pos)

                                ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(pltime + self.lastPlayTime))
                                
                            else:
                                tottime = 0

                                for j in range(self.channels[i].playlistPosition):
                                    tottime += self.channels[i].getItemDuration(j)

                                tottime += self.channels[i].showTimeOffset
                                ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_time', str(int(tottime)))
                               
                                
                self.storeFiles()
                
        REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
        updateDialog.close()
        self.background.setVisible(False)
        self.close()
        
