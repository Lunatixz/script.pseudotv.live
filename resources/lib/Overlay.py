#   Copyright (C) 2014 Kevin S. Graer
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

import xbmc, xbmcgui, xbmcaddon, FileAccess
import subprocess, os, sys, re, shutil
import datetime, time, threading, _strptime
import random, traceback, buggalo
import urllib, urllib2, json

from fanarttv import *
from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow
from ChannelList import ChannelList
from ChannelListThread import ChannelListThread
from FileAccess import FileAccess
from Migrate import Migrate
from Artdownloader import *
from upnp import *
from PVRdownload import *
from utils import *

try:
    from PIL import Image
    from PIL import ImageEnhance
except:
    REAL_SETTINGS.setSetting("UNAlter_ChanBug","true")
    pass
   
    
class MyPlayer(xbmc.Player):
    
    def __init__(self):
        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)
        self.channelList = ChannelList()
        self.stopped = False
        self.ignoreNextStop = False
    
    
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Player: ' + msg, level)
    
    
    def PlaybackValid(self):
        self.PlaybackStatus = False
        if xbmc.Player().isPlaying():
            self.PlaybackStatus = True
        self.log('PlaybackValid, PlaybackStatus = ' + str(self.PlaybackStatus))
    
    
    def is_playback_paused(self):
        self.log('is_playback_paused')
        return bool(xbmc.getCondVisibility("Player.Paused"))

    
    def resume_playback(self):
        self.log('resume_playback')
        xbmc.sleep(100)
        if self.is_playback_paused():
            xbmc.Player().pause()
            if DEBUG == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "DEBUGGING: resume_playback", 1000, THUMB) )
    
    
    def onPlayBackPaused(self):
        self.log('onPlayBackPaused')
        self.overlay.Paused()

        
    def onPlayBackResumed(self):
        self.log('onPlayBackResumed')
        self.overlay.Resume()
    
    
    def onPlayBackStarted(self):
        self.log('onPlayBackStarted')
        self.resume_playback()
        self.PlaybackValid()
        self.overlay.seektime = 0
        
        if xbmc.Player().isPlaying():
            file = xbmc.Player().getPlayingFile()
            file = file.replace("\\\\","\\")
            
            if self.overlay.seektime == 0:
                self.overlay.seektime = xbmc.Player().getTime()
                
            try:
                if REAL_SETTINGS.getSetting("UPNP1") == "true":
                    self.log('UPNP1 Sharing')
                    UPNP1 = SendUPNP(IPP1, file, self.overlay.seektime)
                if REAL_SETTINGS.getSetting("UPNP2") == "true":
                    self.log('UPNP2 Sharing')
                    UPNP2 = SendUPNP(IPP2, file, self.overlay.seektime)
                if REAL_SETTINGS.getSetting("UPNP3") == "true":
                    self.log('UPNP3 Sharing')
                    UPNP3 = SendUPNP(IPP3, file, self.overlay.seektime)
            except Exception: 
                buggalo.onExceptionRaised()  
    
    
    def onPlayBackEnded(self):
        self.log('onPlayBackEnded') 
        if self.overlay.OnDemand == True:
            self.overlay.OnDemand = False  
            xbmc.executebuiltin("PlayerControl(SmallSkipForward)")
        
    
    def onPlayBackStopped(self):
        if self.stopped == False:
            self.log('Playback stopped')
            if self.overlay.OnDemand == True:
                self.overlay.OnDemand = False
                xbmc.executebuiltin("PlayerControl(SmallSkipForward)")

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
        self.showingPop = False
        self.showingInfo = False
        self.showingMenu = False
        self.OnDemand = False
        self.infoOffset = 0
        self.invalidatedChannelCount = 0
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
        self.disableEnd = False
        self.notPlayingAction = 'Up'
        self.ActionTimerInt = float(REAL_SETTINGS.getSetting("Playback_timeout"))
        self.Browse = ''
        self.showingEPG = False
        REAL_SETTINGS.setSetting("ArtService_Running","false")
        REAL_SETTINGS.setSetting('SyncXMLTV_Running', "false")
        
        if REAL_SETTINGS.getSetting("UPNP1") == "true" or REAL_SETTINGS.getSetting("UPNP2") == "true" or REAL_SETTINGS.getSetting("UPNP3") == "true":
            self.UPNP = True
        else:
            self.UPNP = False

        if FileAccess.exists(os.path.join(XBMC_SKIN_LOC, 'custom_script.pseudotv.live_9506.xml')):
            self.VideoWindow = True
            
        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse = self.channelbugcolor))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)
        self.doModal()
        self.log('__init__ return')
     
     
    def resetChannelTimes(self):
        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(self.timeStarted - self.channels[i].totalTimePlayed)

    
    def getSize(self, fileobject):
        fileobject.seek(0,2) # move the cursor to the end of the file
        size = fileobject.tell()
        return size
        
           
    def Backup(self, org, bak):
        self.log('Backup ' + str(org) + ' - ' + str(bak))
        if FileAccess.exists(org):
            if FileAccess.exists(bak):
                try:
                    xbmcvfs.delete(bak)
                except:
                    pass
            FileAccess.copy(org, bak)
        
        if DEBUG == 'true':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Backup Complete", 1000, THUMB) )
            
            
    def Restore(self, bak, org):
        self.log('Restore ' + str(bak) + ' - ' + str(org))
        if FileAccess.exists(bak):
            if FileAccess.exists(org):
                try:
                    xbmcvfs.delete(org)
                except:
                    pass
            FileAccess.copy(bak, org)
        
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Restore Complete, Restarting...", 1000, THUMB) )

        
    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('onInit')
        self.log('PTVL Version = ' + ADDON_VERSION)
              
        try:
            self.getControl(101).setLabel('Please Wait')
        except:
            pass
            
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
            Normal_Shutdown = REAL_SETTINGS.getSetting('Normal_Shutdown') == "true"
        except:
            Normal_Shutdown = True
            REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
            pass
            
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live: Started"}, "id": 1}')
        self.channelList.sendJSON(json_query)
        
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
                if settingsFile_flesize > 100:
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
        self.background.setVisible(True)
        self.getControl(102).setVisible(False)
        
        try:
            self.getControl(119).setVisible(False)
        except:
            pass
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
        try:
            #Set button labels n logo
            self.getControl(995).setImage(THUMB)
            self.getControl(997).setLabel('OnNow')
            self.getControl(998).setLabel('OnDemand')
            self.getControl(999).setLabel('LastChannel')
            self.getControl(1000).setLabel('')
            self.getControl(1001).setLabel('')
            self.getControl(1002).setLabel('')
            self.getControl(1003).setLabel('EPGType')
            self.getControl(1004).setLabel('')
            self.getControl(1005).setLabel('Mute')
            self.getControl(1006).setLabel('Subtitle')
            self.getControl(1007).setLabel('VOSD')
            self.getControl(1008).setLabel('Sleep')
            self.getControl(1009).setLabel('Settings')
            self.getControl(1010).setLabel('Exit')
        except:
            pass

        if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true":
            self.SyncXMLTV()
            
        updateDialog = xbmcgui.DialogProgress()
        updateDialog.create("PseudoTV Live", "Initializing")
        self.backupFiles(updateDialog)
        ADDON_SETTINGS.loadSettings()
        
        if CHANNEL_SHARING == True:
            FileAccess.makedirs(LOCK_LOC)
            updateDialog.update(70, "Initializing", "Checking Other Instances")
            self.isMaster = GlobalFileLock.lockFile("MasterLock", False)
        else:
            self.isMaster = True

        updateDialog.update(95, "Initializing", "PseudoTV Live")

        if self.isMaster:
            migratemaster = Migrate()     
            migratemaster.migrate()
        self.infoTimer = threading.Timer(5.0, self.hideInfo)
        self.MenuTimer = threading.Timer(5.0, self.hideMenu)
        self.popTimer = threading.Timer(5.0, self.hidePOP)
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)
        self.playerTimer.name = "PlayerTimer"
        
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
              
        updateDialog.update(95, "Initializing", "Channels")
        
        if REAL_SETTINGS.getSetting("ATRestore") == "true" and REAL_SETTINGS.getSetting("Warning2") == "true":
            self.log('Setting2 ATRestore onInit') 
            if atsettingsFile_flesize > 100:
                REAL_SETTINGS.setSetting("ATRestore","false")
                REAL_SETTINGS.setSetting("Warning2","false")
                REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
                self.Restore(atsettingsFile, settingsFile)   
                xbmc.executebuiltin('XBMC.AlarmClock( RestartPTVL, XBMC.RunScript(' + ADDON_PATH + '/default.py),0.5,true)')
                self.end()
                return 
        elif Normal_Shutdown == False:
            if settingsFile_flesize < 100 and nsettingsFile_flesize > 100:
                self.log('Setting2 Restore onInit') 
                self.Restore(nsettingsFile, settingsFile)
                xbmc.executebuiltin('XBMC.AlarmClock( RestartPTVL, XBMC.RunScript(' + ADDON_PATH + '/default.py),0.5,true)')
                self.end()
                return 
        else:
            if settingsFile_flesize > 100:
                self.Backup(settingsFile, nsettingsFile)
        
        if self.readConfig() == False:
            return
        
        self.myEPG.channelLogos = self.channelLogos
        self.maxChannels = len(self.channels)

        if self.maxChannels == 0 and REAL_SETTINGS.getSetting("Autotune") == "false":
            autoTune = False
            dlg = xbmcgui.Dialog()     
                
            if dlg.yesno("No Channels Configured", "Would you like PseudoTV Live to Auto Tune Channels?"):
                REAL_SETTINGS.setSetting("Autotune","true")
                REAL_SETTINGS.setSetting("Warning1","true")
                REAL_SETTINGS.setSetting("autoFindLivePVR","true")
                REAL_SETTINGS.setSetting("autoFindUSTVNOW","true")
                REAL_SETTINGS.setSetting("autoFindNetworks","true")
                REAL_SETTINGS.setSetting("autoFindMovieGenres","true")
                REAL_SETTINGS.setSetting("autoFindMixGenres","true")
                REAL_SETTINGS.setSetting("autoFindRecent","true")
                REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_RSS","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Plugins","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Networks","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Seasonal","true")
                autoTune = True
                
                if autoTune:
                    xbmc.executebuiltin('XBMC.AlarmClock( Restarting PseudoTV Live, XBMC.RunScript(' + ADDON_PATH + '/default.py),0.5,true)')
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

        try:
            self.getControl(101).setLabel('Loading')
        except:
            pass

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
            self.Player.play(self.channelList.youtube_ok + 'Y8WlAhpHzkM')
            time.sleep(17) 
            self.background.setVisible(True)
            REAL_SETTINGS.setSetting("INTRO_PLAYED","true")
        
        self.resetChannelTimes()
        self.setChannel(self.currentChannel)
        self.background.setVisible(False)
        self.startSleepTimer()
        self.startNotificationTimer()
        self.playerTimer.start()
        
        if REAL_SETTINGS.getSetting("Idle_Screensaver") == "true":
            REAL_SETTINGS.setSetting("Idle_showingIdle","false")
            self.IdleTime = threading.Timer(60.0, self.IdleTimer)
            self.IdleTime.name = "IdleTime"
            self.IdleTime.start()

        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()
        else:
            if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true":
                self.ArtServiceThread = threading.Timer(float(self.InfTimer), self.Artdownloader.ArtService)
                self.ArtServiceThread.name = "ArtServiceThread"
                self.ArtServiceThread.start()

        if SETTOP == True:
            self.log('onInit, Settop Enabled')
            self.channelThread_Timer = threading.Timer(float(self.Refresh), self.Settop)
            self.channelThread_Timer.name = "channelThread_Timer"
            self.channelThread_Timer.start() 
            
        self.actionSemaphore.release()
        REAL_SETTINGS.setSetting('Normal_Shutdown', "false")
        
        if REAL_SETTINGS.getSetting('StartupMessage') == "false":
            if self.channelList.autoplaynextitem == True:
                self.message('Its recommend you DISABLE XBMC Video Playback Setting "Play the next video Automatically"')
            REAL_SETTINGS.setSetting('StartupMessage', 'true')

        self.log('onInit return')
    

    def Settop(self):
        self.log('Settop')     
        if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true":
            self.SyncXMLTV()
                                
        self.channels = []
        self.timeStarted = time.time()
        self.channels = self.channelList.setupList()
        self.maxChannels = len(self.channels)                

        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread = ChannelListThread()
            self.channelThread.myOverlay = self
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()
            
        if NOTIFY == 'true':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Settop Update Complete", 1000, THUMB) )
        
        self.channelThread_Timer = threading.Timer(float(self.Refresh), self.Settop)
        self.channelThread_Timer.name = "ChannelThread_Timer"
        self.channelThread_Timer.start()
            

    # setup all basic configuration parameters, including creating the playlists that
    # will be used to actually run this thing
    def readConfig(self):
        self.log('readConfig')
        # Sleep setting is in 30 minute increments...so multiply by 30, and then 60 (min to sec)
        self.sleepTimeValue = int(REAL_SETTINGS.getSetting('AutoOff')) * 1800
        self.log('Auto off is ' + str(self.sleepTimeValue))
        self.sleepTimeMode = int(REAL_SETTINGS.getSetting("AutoOff_Mode"))
        self.log('Auto off Mode is ' + str(self.sleepTimeMode))
        self.infoOnChange = REAL_SETTINGS.getSetting("InfoOnChange") == "true"
        self.log('Show info label on channel change is ' + str(self.infoOnChange))
        self.showChannelBug = REAL_SETTINGS.getSetting("ShowChannelBug") == "true"
        self.log('Show channel bug - ' + str(self.showChannelBug))
        self.forceReset = REAL_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.channelResetSetting = REAL_SETTINGS.getSetting('ChannelResetSetting')
        self.log("Channel reset setting - " + str(self.channelResetSetting))
        self.channelLogos = xbmc.translatePath(REAL_SETTINGS.getSetting('ChannelLogoFolder'))
        
        if SETTOP == True:
            REAL_SETTINGS.setSetting("ThreadMode","0")
            
        self.backgroundUpdating = int(REAL_SETTINGS.getSetting("ThreadMode"))
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
        self.notPlayingAction = 'Down'     

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
        self.notPlayingAction = 'Up'

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
        dlg.ok('PseudoTV Live Announcement:', data)
        del dlg


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('TVOverlay: ' + msg, level)

        
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('TVOverlay: ' + msg, level) 

            
    # set the channel, the proper show offset, and time offset
    def setChannel(self, channel):
        self.log('setChannel ' + str(channel))
        self.showingInfo = True #False flag showingInfo to keep POPup from showing
        chname = (self.channels[self.currentChannel - 1].name)
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live: Channel Name - %s"}, "id": 1}' % (chname))
        self.channelList.sendJSON(json_query)
        
        if self.OnDemand == True:
            self.OnDemand = False
            
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

        try:
            self.getControl(101).setLabel('Loading Channel')
        except:
            pass
          
        self.getControl(102).setVisible(False)
        
        try:
            self.getControl(119).setVisible(False)
        except:
            pass
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        self.getControl(103).setImage('NA.png')
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
        
        # start timeout timer, action stop("close") playback, trigger playerTimerAction
        if self.ActionTimerInt >= 5.00:
            self.log("start ActionTimer")
            self.log("self.ActionTimerInt = " + str(self.ActionTimerInt))
            self.ActionTimer = threading.Timer(self.ActionTimerInt, self.ActionTimerAction)
            self.ActionTimer.name = "ActionTimer"
            self.ActionTimer.start()
            
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
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = 0
            pass
        
        self.log('setChannel Chtype = ' + str(chtype))
        
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
            self.log("Ignoring a stop because of a strm or chtype = 8, 9")
            self.Player.ignoreNextStop = True
        
        self.log("about to mute");
        # Mute the channel before changing
        xbmc.executebuiltin("Mute()");           
        xbmc.sleep(self.channelDelay)
        # set the show offset
        self.Player.playselected(self.channels[self.currentChannel - 1].playlistPosition)
        self.log("playing selected file");
        xbmc.sleep(100);
        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(curtime)
        mediapath = self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)
        
        if chname == 'PseudoCinema':
            self.Cinema_Mode = True
        else:
            self.Cinema_Mode = False
            
        try:
            plugchk = mediapath.split('/')[2]
        except:
            plugchk = mediapath
            pass
                    
        if self.channels[self.currentChannel - 1].isPaused:
            self.channels[self.currentChannel - 1].setPaused(False)
            
            if chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                self.log("Seeking, paused channel")
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
            self.Paused()
        else:
                
            if chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                self.log("Seeking")
                seektime1 = self.channels[self.currentChannel - 1].showTimeOffset + timedif + int((time.time() - curtime))
                seektime2 = self.channels[self.currentChannel - 1].showTimeOffset + timedif
                overtime = float((int(self.channels[self.currentChannel - 1].getItemDuration(self.channels[self.currentChannel - 1].playlistPosition))/8)*6)
        
                if (mediapath[-4:].lower() == 'strm' or mediapath[0:6].lower() == 'plugin'):
                    self.seektime = self.SmartSeek(mediapath, seektime1, seektime2, overtime)
                    
                    if self.UPNP:
                        self.PlayUPNP(mediapath, self.seektime)
                else:
                    try:
                        self.Player.seekTime(seektime1)
                        self.seektime = seektime1
                        self.log("seektime1")
                    except:
                        self.log("Unable to set proper seek time, trying different value")
                        try:
                            self.Player.seekTime(seektime2)
                            self.seektime = seektime2
                            self.log("seektime2")
                        except:
                            self.log('Exception during seek', xbmc.LOGERROR)
                            pass    
                            
                    if self.UPNP:
                        self.PlayUPNP(mediapath, self.seektime)   
        
        # Unmute
        self.log("Finished, unmuting");
        xbmc.executebuiltin("Mute()");
        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
        self.runActions(RULES_ACTION_OVERLAY_SET_CHANNEL_END, channel, self.channels[channel - 1])
        
        try:
            if self.ActionTimer.isAlive():
                self.log("end ActionTimer");
                self.ActionTimer.cancel()
                self.ActionTimer.join()
        except:
            pass
            
        self.log('setChannel return')
        
            
    def SmartSeek(self, mediapath, seektime1, seektime2, overtime):
        self.log("SmartSeek")
        seektime = 0
        if seektime1 < overtime:
            try:
                self.Player.seekTime(seektime1)
                seektime = seektime1
                self.log("seektime1")
            except:
                self.log("Unable to set proper seek time, trying different value")
                if seektime2 < overtime:
                    try:
                        self.Player.seekTime(seektime2)
                        seektime = seektime2
                        self.log("seektime2")
                    except:
                        self.log('Exception during seek', xbmc.LOGERROR)
                        seektime = 0
                        pass
                else:
                    pass
        
        if seektime == 0 and DEBUG == 'true':
            self.log('seektime' + str(seektime))
            self.log('overtime' + str(overtime))
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "DEBUGGING: Overriding Seektime", 1000, THUMB) )

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
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = 0
            pass
              
        try:
            if self.infoOffset > 0:
                self.getControl(502).setLabel('COMING UP:') 
                self.getControl(515).setVisible(False)    
            elif self.infoOffset < 0:
                self.getControl(502).setLabel('ALREADY SEEN:') 
                self.getControl(515).setVisible(False)    
            elif self.infoOffset == 0:
                self.getControl(502).setLabel('NOW WATCHING:')
                self.getControl(515).setVisible(True)    
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
                    
            mediapath = (self.channels[self.currentChannel - 1].getItemFilename(position))
        
        elif self.OnDemand == True:
            print 'self.OnDemand'
            position = -999
            mediapath = self.Browse
        
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
                
        self.log('setShowInfo, setshowposition = ' + str(position)) 
        chname = (self.channels[self.currentChannel - 1].name)
        LiveID = self.SetMediaInfo(chtype, chname, mediapath, position)
        LiveID = self.channelList.unpackLiveID(LiveID)
        
        #Art Info
        type = LiveID[0]
        id = LiveID[1]
        Managed = LiveID[3]
        playcount = int(LiveID[4])

        try:
            if mediapath[0:5] == 'stack':
                smpath = (mediapath.split(' , ')[0]).replace('stack://','')
                mpath = (os.path.split(smpath)[0])
            elif mediapath.startswith('plugin://plugin.video.bromix.youtube') or mediapath.startswith('plugin://plugin.video.youtube'):
                mpath = (os.path.split(mediapath)[0])
                YTid = mediapath.split('id=')[1]
                mpath = (mpath + '/' + YTid).replace('/?path=/root','').replace('/play','')
            else:
                mpath = (os.path.split(mediapath)[0])
        except Exception: 
            mpath = mediapath
            buggalo.onExceptionRaised()  
                
        if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true" and REAL_SETTINGS.getSetting("ArtService_Running") == "false" and REAL_SETTINGS.getSetting("ArtService_Primed") == "true":
            self.log('Dynamic artwork enabled')
                
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
                    self.getControl(511).setImage(IMAGES_LOC + 'NA.png') 
            except:
                self.log('setShowInfo, Label 511 not found')
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
                    self.getControl(512).setImage(MEDIA_LOC + 'NA.png')     
            except:
                self.log('setShowInfo, Label 512 not found')
                pass  

            try:
                type1 = str(self.getControl(507).getLabel())
                type1EXT = self.Artdownloader.EXTtype(type1)
                REAL_SETTINGS.setSetting("type1EXT",type1EXT)
                self.setArtwork1(type, chtype, chname, id, mpath, type1EXT)
            except:
                self.log('setShowInfo, Label 507 not found')
                pass
               
            try:
                type2 = str(self.getControl(509).getLabel())
                type2EXT = self.Artdownloader.EXTtype(type2)
                REAL_SETTINGS.setSetting("type2EXT",type2EXT)
                self.setArtwork2(type, chtype, chname, id, mpath, type2EXT)
            except:
                self.log('setShowInfo, Label 509 not found')
                pass
        else:
            try:
                self.getControl(508).setImage(THUMB)
            except:
                pass  
            try:
                self.getControl(510).setImage(THUMB)
            except:
                pass  
                
        self.log('setShowInfo return')

        
    def setArtwork1(self, type, chtype, chname, id, mpath, type1EXT):
        self.log('setArtwork1')
        try:
            self.getControl(508).setVisible(True)
            self.getControl(508).setImage('NA.png')
            setImage1 = self.Artdownloader.FindArtwork(type, chtype, chname, id, mpath, type1EXT)
            self.getControl(508).setImage(setImage1)
        except:
            self.getControl(508).setVisible(False)
            pass  
    
    
    def setArtwork2(self, type, chtype, chname, id, mpath, type2EXT):
        self.log('setArtwork2')
        try: 
            self.getControl(510).setVisible(True)
            self.getControl(510).setImage('NA.png')
            setImage2 = self.Artdownloader.FindArtwork(type, chtype, chname, id, mpath, type2EXT)
            self.getControl(510).setImage(setImage2)
        except:
            self.getControl(510).setVisible(False)
            pass
    
    
    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = 0
            pass
            
        chname = (self.channels[self.currentChannel - 1].name)
        
        if self.Player.isPlaying():
            mediapath = xbmc.Player().getPlayingFile()
        else:
            mediapath = ''
        
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
                if not FileAccess.exists(LOGO_CACHE_LOC):
                    FileAccess.makedirs(LOGO_CACHE_LOC)
                    
                if chtype != 8:
                    setImage = self.Artdownloader.FindBug(chtype, chname, mediapath)
                    self.getControl(103).setImage(setImage)  
                else:
                    self.getControl(103).setImage('NA.png')     
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
        
        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
            self.channelLabelTimer.start()
        else:
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
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            except:
                chtype = 0
                pass

            # if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(position) < self.shortItemLength:
                # return
                
            if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()) < self.shortItemLength:
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
        
        
    def hideMenu(self):    
        self.log("hideMenu")
        try:
            self.getControl(119).setVisible(False)
            xbmc.sleep(100)
            self.showingMenu = False
        except:
            pass
        
        if self.MenuTimer.isAlive():
            self.MenuTimer.cancel()
        
        self.MenuTimer = threading.Timer(5.0, self.hideMenu)
        
        
    def showMenu(self, timer):
        self.log("showMenu")
        self.hideInfo()
        self.hidePOP()
        
        if not self.showingMenu:
            try:                                
                #Set first button focus, show menu
                self.setFocusId(997)
                self.getControl(119).setVisible(True)
                self.showingMenu = True
            except:
                pass
            
        if self.MenuTimer.isAlive():
            self.MenuTimer.cancel()

        self.MenuTimer = threading.Timer(timer, self.hideMenu)
        self.MenuTimer.name = "MenuTimer" 
        self.MenuTimer.start()

        
    def pauseMenu(self):
        self.log("pauseMenu")
        if self.MenuTimer.isAlive():
            self.MenuTimer.cancel()        
        
        
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
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = 0
            pass
            
        if self.hideShortItems:
            #Skip short videos
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
            
            
    def SleepButton(self):
        self.sleepTimeValue = (self.sleepTimeValue + 1800)
        
        #Disable when max sleep reached
        if self.sleepTimeValue > 14400:
            self.sleepTimeValue = 0
            
        if self.sleepTimeValue != 0:
            Stime = self.sleepTimeValue / 60
            SMSG = 'Sleep in ' +str(Stime) + ' minutes'
        else:
            SMSG = 'Sleep Disabled'
        
        self.startSleepTimer()
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", SMSG, 1000, THUMB) )    
            
            
    def IdleTimer(self):
        self.log("IdleTimer")
        self.showingIdle = REAL_SETTINGS.getSetting("Idle_showingIdle")            
        self.IdleSeconds = 300
        self.PausedPlayback = bool(xbmc.getCondVisibility("Player.Paused"))
        self.ActivePlayback = bool(xbmc.Player().isPlaying())
        
        if ((xbmc.getGlobalIdleTime() >= self.IdleSeconds and self.showingIdle == "false") and (self.PausedPlayback or self.showingEPG)):
            REAL_SETTINGS.setSetting("Idle_showingIdle","true")
            xbmc.executebuiltin('XBMC.RunScript(' + ADDON_PATH + '/resources/lib/idle.py)')
        elif xbmc.getGlobalIdleTime() < self.IdleSeconds:
            REAL_SETTINGS.setSetting("Idle_showingIdle","false")
            
        self.log("IdleTimer, XBMCidle = " + str(xbmc.getGlobalIdleTime()) + ", IdleSeconds = " + str(self.IdleSeconds) + ', PausedPlayback = ' + str(self.PausedPlayback) + ', showingIdle = ' + str(self.showingIdle) + ', showingEPG = ' + str(self.showingEPG) + ', ActivePlayback = ' + str(self.ActivePlayback))
        self.IdleTime = threading.Timer(60.0, self.IdleTimer)
        self.IdleTime.name = "IdleTime"
        self.IdleTime.start()
                 
                 
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
        
            
    def onFocus(self, controlId):
        pass

        
    def onClick(self, controlId):
        self.log('onClick ' + str(controlId))
        # Since onAction isnt always called from the same thread (weird),
        # ignore all actions if we're in the middle of processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return

        lastaction = time.time() - self.lastActionTime
 
        # during certain times we just want to discard all input
        if lastaction < 2:
            self.log('Not allowing actions')
            action = ACTION_INVALID

        self.startSleepTimer()
        
        if controlId == 997:
            if self.showingMenu:
                self.log("OnNow")
                self.pauseMenu()
                xbmc.executebuiltin("ActivateWindow(12003)")
                self.showMenu(self.InfTimer)
                
        elif controlId == 998:
            if self.showingMenu:
                self.log("OnDemand")
                self.pauseMenu()
                extTypes = ['.avi', '.flv', '.mkv', '.mp4', '.strm', '.ts']
                self.Browse = dlg.browse(1,'OnDemand', 'video', '.avi|.flv|.mkv|.mp4|.strm|.ts', True, True, 'special://videoplaylists')
                if (self.Browse)[-4:].lower() in extTypes:
                    self.log("onClick, OnDemand = " + self.Browse)
                    self.Player.play(self.Browse)
                    self.OnDemand = True
                    self.hideMenu()
                else:
                    self.showMenu(self.InfTimer)
                
        elif controlId == 999:
            if self.showingMenu:
                self.log("LastChannel")
                self.LastChannelJump()
                self.setChannel(self.LastChannel)
                self.hideMenu()
                    
        elif controlId == 1000:
            if self.showingMenu:
                self.log("Favorites")
                # xbmc.executebuiltin("ActivateWindow(10134)")
                
        elif controlId == 1001:
            if self.showingMenu:
                self.log("")
                    
        elif controlId == 1002:
            if self.showingMenu:
                self.log("")
                
        elif controlId == 1003:
            if self.showingMenu:
                self.log("EPGType")
                self.pauseMenu()
                self.EPGtypeToggle()
                self.showMenu(self.InfTimer)
                
        elif controlId == 1004:
            if self.showingMenu:
                self.log("Record")
                
        elif controlId == 1005:
            if self.showingMenu:
                self.log("Mute")
                self.pauseMenu()
                xbmc.executebuiltin("Mute()");
                self.showMenu(self.InfTimer)

        elif controlId == 1006:
            if self.showingMenu:
                self.log("Subtitle")
                self.pauseMenu()
                # xbmc.executebuiltin("ActivateWindow(10153)")
                xbmc.executebuiltin("ActivateWindow(SubtitleSearch)")
                self.showMenu(self.InfTimer)
                
        elif controlId == 1007:
            if self.showingMenu:
                self.log("VideoMenu")
                xbmc.executebuiltin("ActivateWindow(12901)")
                self.hideMenu()
                    
        elif controlId == 1008:
            if self.showingMenu:
                self.log("Sleep")
                self.pauseMenu()
                self.SleepButton()    
                self.showMenu(self.InfTimer)       
                    
        elif controlId == 1009:
            if self.showingMenu:
                self.log("Settings")
                self.pauseMenu()
                xbmcaddon.Addon(id='script.pseudotv.live').openSettings()
                self.showMenu(self.InfTimer)
                
        elif controlId == 1010:
            if self.showingMenu:
                self.log("Exit")
                self.pauseMenu()
                if dlg.yesno("Exit?", "Are you sure you want to exit PseudoTV Live?"):
                    self.hideMenu()
                    self.end()
                else:
                    self.showMenu(self.InfTimer)
            
        self.actionSemaphore.release()
        self.log('onClick return')
                
                
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
                if not self.showingMenu:
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
                    self.showingEPG = True
                    self.myEPG.doModal()

                    if self.channelThread.isAlive():
                        self.channelThread.unpause()

                    self.startNotificationTimer()

                    if self.newChannel != 0:
                        self.background.setVisible(True)
                        self.setChannel(self.newChannel)
                        self.background.setVisible(False)
                    
        elif action == ACTION_MOVE_UP or action == ACTION_PAGEUP:
            if not self.showingMenu:
                self.channelUp()
            else:
                self.showMenu(self.InfTimer)
        
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            if not self.showingMenu:
                self.channelDown()
            else:
                self.showMenu(self.InfTimer)

        elif action == ACTION_MOVE_LEFT:
            if self.showingInfo:
                self.infoOffset -= 1  
                
                if self.infoOffset < 0:
                    self.showMenu(self.InfTimer)
                                        
                if not self.showingMenu:
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
                
            elif self.showingMenu:
                self.hideMenu()
                
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
                
            elif self.showingMenu:
                self.hideMenu()
            
            else:        
                if self.disableEnd == False:
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
            self.hidePOP()
            self.hideMenu()
                    
            if self.ignoreInfoAction:
                self.ignoreInfoAction = False
            else:
                if xbmc.getCondVisibility('Player.ShowInfo'):
                    json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
                    self.ignoreInfoAction = True
                    self.channelList.sendJSON(json_query);
                        
                if self.showingInfo:
                    self.hideInfo()
                    self.hidePOP()
                    self.hideMenu()

                    if xbmc.getCondVisibility('Player.ShowInfo'):
                        json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
                        self.ignoreInfoAction = True
                        self.channelList.sendJSON(json_query);
                else:
                    self.showInfo(self.InfTimer)
        
        elif action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            self.notPlayingAction = 'Last'
            if self.inputChannel < 0:
                self.inputChannel = action - ACTION_NUMBER_0
            else:
                if self.inputChannel < 100:
                    self.inputChannel = self.inputChannel * 10 + action - ACTION_NUMBER_0
            
            self.SetLastChannel()
            self.showChannelLabel(self.inputChannel)
        
        elif action == ACTION_SHOW_SUBTITLES:
            xbmc.executebuiltin("ActivateWindow(SubtitleSearch)")
            
        elif action == ACTION_AUDIO_NEXT_LANGUAGE:#notworking
            xbmc.executebuiltin("ActivateWindow(NextSubtitle)")
            
        elif action == ACTION_SHOW_CODEC:
            xbmc.executebuiltin("ActivateWindow(CodecInfo)")
            
        elif action == ACTION_ASPECT_RATIO:
            self.SleepButton()
            
        elif action == ACTION_RECORD:
            self.log('ACTION_RECORD')
            PVRrecord(self.PVRchtype, self.PVRmediapath, self.PVRchname, self.PVRtitle)
        
        elif action == ACTION_SHIFT: #Previous channel button
            self.log('ACTION_SHIFT')
            self.LastChannelJump()
            self.setChannel(self.LastChannel)
                    
        # elif action == ACTION_OSD:
            # xbmc.executebuiltin("ActivateWindow(12901)")

        self.actionSemaphore.release()
        self.log('onAction return')


    # Reset the sleep timer
    def startSleepTimer(self):
        if self.sleepTimeValue == 0:
            try:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
            except:
                return

        # Cancel the timer if it is still running
        try:
            if self.sleepTimer.isAlive():
                self.sleepTimer.cancel()
                self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
        except:
            self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
            pass

        if self.Player.stopped == False:
            self.sleepTimer.name = "SleepTimer"
            self.sleepTimer.start()


    def startNotificationTimer(self, timertime = NOTIFICATION_CHECK_TIME):
        self.log("startNotificationTimer")
        try:
            if self.notificationTimer.isAlive():
                self.notificationTimer.cancel()


            self.notificationTimer = threading.Timer(timertime, self.notificationAction)

            if self.Player.stopped == False:
                self.notificationTimer.name = "NotificationTimer"
                self.notificationTimer.start()
        except:
            pass

            
    # This is called when the sleep timer expires
    def sleepAction(self):
        self.log("sleepAction")
        self.actionSemaphore.acquire()
#        self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)
        # TODO: show some dialog, allow the user to cancel the sleep
        # perhaps modify the sleep time based on the current show
        if self.sleepTimeMode == 0:
            self.end()
        elif self.sleepTimeMode == 1:
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Quit(),%d,false)" % ( 1.0, ) )
            self.end()
        elif self.sleepTimeMode == 2:
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Suspend(),%d,false)" % ( 1.0, ) )
            self.end()
        elif self.sleepTimeMode == 3:
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Powerdown(),%d,false)" % ( 1.0, ) )
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
                    chname = (self.channels[self.currentChannel - 1].name)
                    ChannelLogo = (self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png')
                    
                    try:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
                    except:
                        chtype = 0
                        pass
                        
                    title = 'Coming Up Next'   
                    ShowTitle = self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', '')
                    myLiveID = self.channels[self.currentChannel - 1].getItemLiveID(nextshow)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    
                    if mediapath[0:5] == 'stack':
                        smpath = (mediapath.split(' , ')[0]).replace('stack://','')
                        mpath = (os.path.split(smpath)[0])
                    elif mediapath.startswith('plugin://plugin.video.bromix.youtube') or mediapath.startswith('plugin://plugin.video.youtube'):
                        mpath = (os.path.split(mediapath)[0])
                        YTid = mediapath.split('id=')[1]
                        mpath = (mpath + '/' + YTid).replace('/?path=/root','').replace('/play','')
                    else:
                        mpath = (os.path.split(mediapath)[0])
                    
                    try:
                        ShowEpisode = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(nextshow).replace(',', ''))
                        ShowEpisode = ShowEpisode.split("- ")[1]
                    except:
                        ShowEpisode = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(nextshow).replace(',', ''))
                        pass
                    
                    #ArtType for Classic
                    if REAL_SETTINGS.getSetting("EnableComingUp") == "3":
                        ArtType = {}
                        ArtType['0'] = 'poster'
                        ArtType['1'] = 'fanart' 
                        ArtType['2'] = 'landscape'        
                        ArtType['3'] = 'logo'       
                        ArtType['4'] = 'clearart'              
                        ArtType = ArtType[REAL_SETTINGS.getSetting('ComingUpArtwork')] #notification art type for classic
                    
                    #ArtType for Popup
                    elif REAL_SETTINGS.getSetting("EnableComingUp") == "2":
                        self.log('notification, Classic')  
                        try:
                            ArtType = str(self.getControl(121).getLabel()) #notification art type for new overlay
                            self.getControl(123).setLabel(title)
                            self.getControl(124).setLabel(ShowTitle)
                            self.getControl(125).setLabel(ShowEpisode)
                        except:
                            #No Overlay Popup code in skin, default to Cassic Popup
                            ClassicPOPUP = True
                            pass
                    
                    if REAL_SETTINGS.getSetting("EnableComingUp") != "1":
                        self.log('notification, Popup')  
                        typeEXT = self.Artdownloader.EXTtype(ArtType)
                        self.log('notification.type.ext = ' + str(typeEXT))
                        
                        if REAL_SETTINGS.getSetting("ArtService_Enabled") == "true" and REAL_SETTINGS.getSetting("ArtService_Running") == "false" and REAL_SETTINGS.getSetting("ArtService_Primed") == "true":
                            NotifyTHUMB = self.Artdownloader.FindArtwork(type, chtype, chname, id, mpath, typeEXT)
                        else:
                            NotifyTHUMB = THUMB  
                        
                        if self.showingInfo == False and self.notificationShowedNotif == False:
                            if REAL_SETTINGS.getSetting("EnableComingUp") == "3" or ClassicPOPUP == True:
                                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (title, self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', ''), str(NOTIFICATION_DISPLAY_TIME * 2000), NotifyTHUMB))
                            else:
                                self.getControl(122).setImage(NotifyTHUMB)
                                self.showPOP(self.InfTimer + 2.5)
                            self.notificationShowedNotif = True
                    
                        self.log("notification.plugin.NotifyTHUMB = " + NotifyTHUMB) 
                        
                    if REAL_SETTINGS.getSetting("EnableComingUp") == "1":
                        self.log('notification, Overlay') 
                        self.infoOffset = ((nextshow) - self.notificationLastShow)
                        self.log('snotification, Overlay infoOffset = ' + str(self.infoOffset))
                        self.showInfo(self.InfTimer + 2.5)
                        self.notificationShowedNotif = True
        # sfx todo
        # if self.notificationShowedNotif == True:
            # try:
                # xbmc.playSFX(os.path.join(IMAGES_LOC,'plwing.wav'))
            # except:
                # xbmc.log('playSFX failed')
        
        self.startNotificationTimer()
            
            
    def ActionTimerAction(self):
        self.log("ActionTimerAction, not playing")
        self.disableEnd = True
        # xbmc.executebuiltin( "XBMC.Action(backspace)" )
        # xbmc.executebuiltin( "XBMC.Action(Close)" )
        # if self.Player.isPlaying():
            # xbmc.executebuiltin( "XBMC.Action(Stop)" )
        xbmc.executebuiltin( "XBMC.Action(Select)" )
        
        if self.notPlayingAction == 'Down':
            self.channelDown()
        elif self.notPlayingAction == 'Last':
            self.LastChannelJump()
            self.setChannel(self.LastChannel)
        else:
            self.channelUp()
        self.disableEnd = False
        

    def playerTimerAction(self):
        self.log("playerTimerAction")
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)  
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = 0
            pass

        if self.Player.isPlaying():
            self.notPlayingCount = 0   
            self.lastPlayTime = int(self.Player.getTime())
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()                  
        else:          
            self.notPlayingCount += 1
            self.log("Adding to notPlayingCount, " + str(self.notPlayingCount)) 

        if self.notPlayingCount > 3:
            try:
                self.getControl(101).setLabel('Error Loading: Changing Channel')
            except:
                pass
                
            if self.notPlayingAction == 'Down':
                MSG = "Playback Failed - Changing Channel Down"
            elif self.notPlayingAction == 'Last':
                MSG = "Playback Failed - Returning to Previous Channel"
            else:
                MSG = "Playback Failed - Changing Channel Up"
                
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 4000, THUMB) )
                
            if self.notPlayingAction == 'Down':
                self.channelDown()
            elif self.notPlayingAction == 'Last':
                self.LastChannelJump()
                self.setChannel(self.LastChannel)
            else:
                self.channelUp()
            
            self.playerTimer.start()   
            self.log("error invalid channel, Changing Channel")
            return
        else:
            if DEBUG == 'true' and self.notPlayingCount > 1:
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "notPlayingCount " + str(self.notPlayingCount), 1000, THUMB) )
        
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
    
    
    def Paused(self):
        self.log('Paused')
        try:
            self.getControl(101).setLabel('Paused')
        except:
            pass
            
        self.background.setVisible(True)
        self.showInfo(self.InfTimer)

        if REAL_SETTINGS.getSetting("UPNP1") == "true":
            UPNP1 = PauseUPNP(IPP1)
        if REAL_SETTINGS.getSetting("UPNP2") == "true":
            UPNP2 = PauseUPNP(IPP2)
        if REAL_SETTINGS.getSetting("UPNP3") == "true":
            UPNP3 = PauseUPNP(IPP3)
    
    
    def Resume(self):
        self.log('Resume')
        self.background.setVisible(False)
        
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                UPNP1 = ResumeUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                UPNP2 = ResumeUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                UPNP3 = ResumeUPNP(IPP3)
        except:
            pass
    
    
    def SetLastChannel(self):
        self.log('SetLastChannel') 
        CurChannel = self.fixChannel(self.currentChannel)
        REAL_SETTINGS.setSetting('LastChannel', str(CurChannel))
        
    
    def LastChannelJump(self):
        self.log('LastChannelJump') 
        try:
            self.LastChannel = int(REAL_SETTINGS.getSetting('LastChannel'))
        except:
            pass
        self.SetLastChannel()
    
    
    def SetAutoJump(self, time, cleanTime, title, channel):
        self.log('SetAutoJump') 
        try:
            if self.AutoJumpThread.isAlive():
                self.AutoJumpThread.join()
        except:
            pass
        self.AutoJumpThread = threading.Timer(float(time), self.AutoJump, [title, channel])
        self.AutoJumpThread.name = "AutoJumpThread"
        self.AutoJumpThread.start()
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","Reminder Set for " + str(cleanTime), 4000, THUMB) )
    
    
    def AutoJump(self, title, channel):
        self.log('AutoJump') 
        msg = title + ' starts in 1m'
        if dlg.yesno("PseudoTV Live", msg, "Would you like to switch to channel " + str(channel) + ' ?'):
            # Kill Prompt after a minute, todo
            # self.KillAutoJump = threading.Timer(1.0, self.KillAutoJump)
            # self.KillAutoJump.name = "KillAutoJump"
            # self.KillAutoJump.start()
            
            #Set Lastchannel recall, then jump
            self.SetLastChannel()
            self.setChannel(channel)
    
    
    def KillAutoJump():
        xbmc.executebuiltin("Dialog.Close(PseudoTV Live)")
        
        
    def SyncXMLTV(self):
        self.log('SyncXMLTV') 
        
        if REAL_SETTINGS.getSetting("SyncXMLTV_Running") == "false":
            REAL_SETTINGS.setSetting('SyncXMLTV_Running', "true")
            
            if not FileAccess.exists(XMLTV_CACHE_LOC):
                FileAccess.makedirs(XMLTV_CACHE_LOC)
                
            USxmltv = self.channelList.SyncUSTVnow(False, False)
            SSxmltv = self.channelList.SyncSSTV(False, False)
            FTVxmltv = self.channelList.SyncFTV(False, False)
            REAL_SETTINGS.setSetting('SyncXMLTV_Running', "false")
    
    
    def EPGtypeToggle(self):
        self.log('EPGtype')     
        ColorType = REAL_SETTINGS.getSetting('EPGcolor_enabled')
 
        if ColorType == '0':
            REAL_SETTINGS.setSetting("EPGcolor_enabled", "1")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "EPG Color by Genre ", 1000, THUMB) )
        elif ColorType == '1':
            REAL_SETTINGS.setSetting("EPGcolor_enabled", "2")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "EPG Color by Chtype", 1000, THUMB) )
        elif ColorType == '2':
            REAL_SETTINGS.setSetting("EPGcolor_enabled", "3")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "EPG Color by Rating", 1000, THUMB) )
        elif ColorType == '3':
            REAL_SETTINGS.setSetting("EPGcolor_enabled", "0")
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "EPG Color Disabled", 1000, THUMB) )
      

    def SetMediaInfo(self, chtype, chname, mediapath, position):
        self.log('SetMediaInfo')  
        # tmpstr = self.GetFileInfo(mediapath)
        
        if position == -999:
            #Core OnDemand Info
            genre = 'Unknown'
            title = 'OnDemand'
            LiveID  = 'tvshow|0|0|False|1|NR|'
            EpisodeTitle = 'OnDemand'
            SEtitle = 'OnDemand'
            Description = tmpstr
            self.getControl(506).setImage(os.path.join(IMAGES_LOC,'Default.png'))
        else:
            #Core Playlist Info
            genre = (self.channels[self.currentChannel - 1].getItemgenre(position))
            title = (self.channels[self.currentChannel - 1].getItemTitle(position))
            LiveID = (self.channels[self.currentChannel - 1].getItemLiveID(position))
            EpisodeTitle = (self.channels[self.currentChannel - 1].getItemEpisodeTitle(position))
            SEtitle = self.channels[self.currentChannel - 1].getItemEpisodeTitle(position)
            Description = (self.channels[self.currentChannel - 1].getItemDescription(position))
            self.getControl(506).setImage(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png') 
 
        #PVR Globals
        self.PVRchtype = chtype
        self.PVRmediapath = mediapath
        self.PVRchname = chname
        self.PVRtitle = title
        
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

        self.getControl(503).setLabel((title).replace("*NEW*",""))
        self.getControl(504).setLabel(swtitle)
        self.getControl(505).setLabel(Description)
        return LiveID
               
                
    def GetFileInfo(self, mediapath, FleType='video'):
        self.log('GetFileInfo')     
        file_detail = []
        json_query = uni('{"jsonrpc": "2.0", "method": "Files.GetFileDetails", "params": {"file": "%s", "media": "%s", "properties":["title","year","mpaa","imdbnumber","description","season","episode","playcount","genre","duration","runtime","showtitle","album","artist","plot","plotoutline","tagline"]}, "id": 23}' % (mediapath, FleType))
        json_folder_detail = self.channelList.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in file_detail:
            match = re.search('"filedetails" *: *"(.*?)",', f)
            istvshow = False

            if match:
                duration = re.search('"duration" *: *([0-9]*?),', f)
                titles = re.search('"label" *: *"(.*?)"', f)
                showtitles = re.search('"showtitle" *: *"(.*?)"', f)
                plots = re.search('"plot" *: *"(.*?)",', f)
                plotoutlines = re.search('"plotoutline" *: *"(.*?)",', f)
                years = re.search('"year" *: *([0-9]*?)', f)
                genres = re.search('"genre" *: *\[(.*?)\]', f)
                playcounts = re.search('"playcount" *: *([0-9]*?),', f)
                imdbnumbers = re.search('"imdbnumber" *: *"(.*?)"', f)
                ratings = re.search('"mpaa" *: *"(.*?)"', f)
                descriptions = re.search('"description" *: *"(.*?)"', f)
                            
                if showtitles != None and len(showtitles.group(1)) > 0:
                    type = 'tvshow'
                    dbids = re.search('"tvshowid" *: *([0-9]*?),', f)    
                else:
                    type = 'movie'
                    dbids = re.search('"movieid" *: *([0-9]*?),', f)
                
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
                    rating = self.channelList.cleanRating(ratings.group(1))
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
                    theplot = (self.channelList.trim(theplot, 350, '...'))
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
                        print 'EnhancedGuideData' 

                        if imdbnumber == 0:
                            imdbnumber = self.channelList.getTVDBID(showtitles.group(1), year)
                                
                        if genre == 'Unknown':
                            genre = (self.channelList.getGenre(type, showtitles.group(1), year))
                            
                        if rating == 'NR':
                            rating = (self.channelList.getRating(type, showtitles.group(1), year, imdbnumber))

                        if imdbnumber != 0:
                            Managed = self.channelList.sbManaged(imdbnumber)

                    GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating] 
                    genre, LiveID = self.channelList.packGenreLiveID(GenreLiveID)
                    
                    tmpstr += (showtitles.group(1)) + "//" + swtitle + "//" + theplot + "//" + genre + "////" + (LiveID)
                    istvshow = True

                else:
                    if year != 0:
                        tmpstr += titles.group(1) + ' (' + str(year) + ')' + "//"
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
                                imdbnumber = self.channelList.getIMDBIDmovie(titles.group(1), year)

                            if genre == 'Unknown':
                                genre = (self.channelList.getGenre(type, titles.group(1), year))

                            if rating == 'NR':
                                rating = (self.channelList.getRating(type, titles.group(1), year, imdbnumber))

                        if imdbnumber != 0:
                            Managed = self.channelList.cpManaged(titles.group(1), imdbnumber)
                                
                        GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating]
                        genre, LiveID = self.channelList.packGenreLiveID(GenreLiveID)           
                        tmpstr += "//" + theplot + "//" + (genre) + "////" + (LiveID)
                    
                    else: #Music
                        LiveID = 'music|0|0|False|1|NR|'
                        artist = re.search('"artist" *: *"(.*?)"', f)
                        tmpstr += album.group(1) + "//" + artist.group(1) + "//" + 'Music' + "////" + LiveID
                
                print tmpstr
                return tmpstr
         
         
    def end(self):
        self.log('end')  
        self.isExiting = True   
        
        try:
            self.getControl(101).setLabel('Exiting')
        except:
            pass
            
        # Prevent the player from setting the sleep timer
        self.Player.stopped = True
        self.background.setVisible(True)
        
        try:
            self.getControl(119).setVisible(False)
        except:
            pass
        try:
            self.getControl(120).setVisible(False)
        except:
            pass
            
        curtime = time.time()
        xbmc.executebuiltin("PlayerControl(repeatoff)")
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
        
        if CHANNEL_SHARING == True and self.isMaster:
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
            
        try:
            if self.AutoJumpThread.isAlive():
                self.AutoJumpThread.cancel()
                self.AutoJumpThread.join()
        except:
            pass
            
        try:
            if self.ActionTimer.isAlive():
                self.ActionTimer.cancel()
                self.ActionTimer.join()
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

        try:
            if self.IdleTime.isAlive():
                self.IdleTime.cancel()
                self.IdleTime.join()
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
                
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live: Stopped"}, "id": 1}')
        self.channelList.sendJSON(json_query)
        REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
        updateDialog.close()
        self.background.setVisible(False)
        self.close()