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

import xbmc, xbmcgui, xbmcaddon, FileAccess
import subprocess, os, sys, re, shutil
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
    
try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo/submit.php'
except:
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
        self.log('PlaybackValid')
        xbmc.sleep(100)
        PlaybackStatus = False
        if xbmc.Player().isPlaying():
            PlaybackStatus = True
        self.log('PlaybackValid, PlaybackStatus = ' + str(PlaybackStatus))
        return PlaybackStatus
    
    def is_playback_paused(self):
        self.log('is_playback_paused')
        return bool(xbmc.getCondVisibility("Player.Paused"))

    
    def resume_playback(self):
        self.log('resume_playback')
        xbmc.sleep(100)
        if self.is_playback_paused():
            xbmc.Player().pause()

    
    def onPlayBackPaused(self):
        self.log('onPlayBackPaused')
        self.overlay.Paused()

        
    def onPlayBackResumed(self):
        self.log('onPlayBackResumed')
        self.overlay.Resume()
    
    
    def onPlayBackStarted(self):
        self.log('onPlayBackStarted')
        self.resume_playback()
        PlaybackStatus = self.PlaybackValid()
        
        if PlaybackStatus:
            self.overlay.seektime = 0
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
        # else:
            # self.log('onPlayBackStarted, PlaybackStatus False Stopping Playback')
            # json_query = '{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"stop"},"id":1}'
            # self.channelList.sendJSON(json_query);

            
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
                    self.overlay.sleepTimer = threading.Timer(1, self.overlay.sleepAction)

                self.overlay.background.setVisible(True)
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
        self.OnNowTitleLst = []        
        self.OnNowArtLst = []
        self.lastActionTime = 0
        self.actionSemaphore = threading.BoundedSemaphore()
        self.channelThread = ChannelListThread()
        self.channelThread.myOverlay = self
        self.timeStarted = 0
        self.infoOnChange = True
        self.showingPop = False
        self.showingInfo = False
        self.showingMenu = False
        self.showingNextAired = False
        self.showingMenuAlt = False
        self.showingIdle = False
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
        self.PVRdbid = ''
        self.PVRid  = ''
        self.PVRtype = ''
        self.LastChannel = 0
        self.InfTimer = INFOBAR_TIMER[int(REAL_SETTINGS.getSetting('InfoTimer'))]
        self.Artdownloader = Artdownloader()
        self.VideoWindow = False
        self.disableEnd = False
        self.notPlayingAction = 'Up'
        self.ActionTimeInt = int(REAL_SETTINGS.getSetting("Playback_timeout"))
        self.Browse = ''
        self.showingEPG = False
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
        self.getControl(101).setLabel('Please Wait')
        self.channelList = ChannelList()
        settingsFile_flesize = 0
        nsettingsFile_flesize = 0
        atsettingsFile_flesize = 0
        settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
        nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.bak.xml'))
        atsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.pretune.xml'))
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
            file1 = FileAccess.open(settingsFile, "r")
            settingsFile_flesize = self.getSize(file1)
            file1.close()
            
        if FileAccess.exists(nsettingsFile):
            file2 = FileAccess.open(nsettingsFile, "r")
            nsettingsFile_flesize = self.getSize(file2)
            file2.close()
                
        if FileAccess.exists(atsettingsFile):
            file3 = FileAccess.open(atsettingsFile, "r")
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
        self.getControl(119).setVisible(False)
        self.getControl(130).setVisible(False)
        self.getControl(120).setVisible(False)

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
        self.MenuAltTimer = threading.Timer(5.0, self.hideMenuAlt)
        self.popTimer = threading.Timer(5.0, self.hidePOP)
        self.channelLabelTimer = threading.Timer(5.0, self.hideChannelLabel)
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)
        self.playerTimer.name = "PlayerTimer"
        
        try:
            self.myEPG = EPGWindow("script.pseudotv.live.EPG.xml", ADDON_PATH, Skin_Select)
        except:
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
        self.getControl(101).setLabel('Loading')

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
            youtube_plugin = self.channelList.youtube_player()
             
            if youtube_plugin != False:
                self.Player.play(youtube_plugin + 'Y8WlAhpHzkM')
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
                self.ArtServiceThread = threading.Timer(float(self.InfTimer), self.ArtService)
                self.ArtServiceThread.name = "ArtServiceThread"
                self.ArtServiceThread.start()
                       
        if SETTOP == True:
            self.log('onInit, Settop Enabled')
            self.channelThread_Timer = threading.Timer(float(SETTOP_REFRESH), self.Settop)
            self.channelThread_Timer.name = "channelThread_Timer"
            self.channelThread_Timer.start() 
            
        self.actionSemaphore.release()
        REAL_SETTINGS.setSetting('Normal_Shutdown', "false")
        
        if REAL_SETTINGS.getSetting('StartupMessage') == "false":
            if self.channelList.autoplaynextitem == True:
                self.message('Its recommend you DISABLE XBMC Video Playback Setting "Play the next video Automatically"')
            REAL_SETTINGS.setSetting('StartupMessage', 'true')
        
        try:
            self.Arttype1 = str(self.getControl(507).getLabel())
            self.type1EXT = self.EXTtype(self.Arttype1)
            REAL_SETTINGS.setSetting("type1EXT_Overlay",self.type1EXT)
        except:
            pass
        try:
            self.Arttype2 = str(self.getControl(509).getLabel())
            self.type2EXT = self.EXTtype(self.Arttype2)
            REAL_SETTINGS.setSetting("type2EXT_Overlay",self.type2EXT)
        except:
            pass

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
        
        self.channelThread_Timer = threading.Timer(float(SETTOP_REFRESH), self.Settop)
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
    
    
    def setOnNowArt(self):
        self.log('setOnNowArt')
        self.ShowMenuAlt(self.InfTimer)
        try:
            # item = self.list.getSelectedItem()
            # label = item.getLabel()    
            pos = self.list.getSelectedPosition()
            element = self.OnNowArtLst[pos]
            print pos, element
            if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
                Image = self.Artdownloader.FindArtwork(element[1], element[2], element[3], element[4], element[5], element[6], element[7])
            else:
                Image = self.Artdownloader.FindArtwork_NEW(element[1], element[2], element[3], element[4], element[5], element[6], element[7])
            self.getControl(131).setImage(Image)
        except:
            self.getControl(131).setImage('NA.png')
            pass
   
   
    def setOnNow(self):
        self.log('setOnNow')   
        self.OnNowTitleLst = []        
        self.OnNowArtLst = []
        curtime = time.time()
        ChannelChk = 0 
        
        for i in range(999):
            try:
                Channel = i
                try:
                    try:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                    except:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                        pass

                    timedif = (curtime - self.channels[Channel].lastAccessTime)
                    ChannelChk = int(self.channels[Channel].getCurrentDuration())
                
                    if ChannelChk == 0:
                        self.log('setOnNow, channel ' + str(Channel) + ' no playlist')
                        raise

                    # if self.channels[Channel].isPaused == False:
                        # # adjust the show and time offsets to properly position inside the playlist
                        # #for Live TV get the first item in playlist convert to epoch time  add duration until we get to the current item
                        # if chtype == 8:
                            # self.channels[Channel].setShowPosition(0)
                            # tmpDate = self.channels[Channel].getItemtimestamp(0)   
                            # self.log("overlay tmpdate " + str(tmpDate))   
                            
                            # try:#sloppy fix, for threading issue with strptime.
                                # t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            # except:
                                # t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                                # pass
                                
                            # epochBeginDate = time.mktime(t)
                            # #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                            # #index till we get to the current show
                            # while epochBeginDate + self.channels[Channel].getCurrentDuration() <  curtime:
                                # epochBeginDate += self.channels[Channel].getCurrentDuration()
                                # self.channels[Channel].addShowPosition(1)
                        # else:   #loop for other channel types
                            # while self.channels[Channel].showTimeOffset + timedif > self.channels[Channel].getCurrentDuration():
                                # timedif -= self.channels[Channel].getCurrentDuration() - self.channels[Channel].showTimeOffset
                                # self.channels[Channel].addShowPosition(1)
                                # self.channels[Channel].setShowTime(0) 
                                
                        # position = self.channels[Channel].playlistPosition
                        
                        
                    
                    #same logic as in setchannel; loop till we get the current show
                    if chtype == 8:
                        self.channels[Channel].setShowPosition(0)
                        tmpDate = self.channels[Channel].getItemtimestamp(0)
                         
                        try:#sloppy fix, for threading issue with strptime.
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                        except:
                            t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                            pass
                         
                        epochBeginDate = time.mktime(t)
                        position = self.channels[Channel].playlistPosition
                        #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                        #loop till we get to the current show this is done to display the correct show on the info listing for Live TV types
                        while epochBeginDate + self.channels[Channel].getCurrentDuration() <  time.time():
                            epochBeginDate += self.channels[Channel].getCurrentDuration()
                            self.channels[Channel].addShowPosition(1)
                            position = self.channels[Channel].playlistPosition
                    else: #original code
                        position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                                
                    label = self.channels[Channel].getItemTitle(position)  
                    print label
                    
                    if not label:
                        self.log('setOnNow, no label')
                        raise
                        
                    mediapath = (self.channels[Channel].getItemFilename(position))
                    myLiveID = self.channels[Channel].getItemLiveID(position)
                    title = ("[COLOR=%s][B]%d)[/B][/COLOR] %s" % ((self.channelbugcolor).replace('0x',''), i+1, label))
                    self.OnNowTitleLst.append(title)  
                    chname = (self.channels[Channel].name)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    dbid = (self.channelList.unpackLiveID(myLiveID))[2]
                    
                    if mediapath[0:5] == 'stack':
                        smpath = (mediapath.split(' , ')[0]).replace('stack://','').replace('rar://','')
                        mpath = (os.path.split(smpath)[0]) + '/'
                    elif mediapath[0:6] == 'plugin':
                        mpath = 'plugin://' + mediapath.split('/')[2] + '/'
                    elif mediapath[0:4] == 'upnp':
                        mpath = 'upnp://' + mediapath.split('/')[2] + '/'
                    else:
                        mpath = (os.path.split(mediapath)[0]) + '/'
                    
                    type1EXT = REAL_SETTINGS.getSetting('type2EXT_Overlay')
                    Art = [title, type, chtype, chname, id, dbid, mpath, type1EXT]     
                    print Art
                    self.OnNowArtLst.append(Art)
                except:
                    raise
            except:
                pass  
                
        # Before = Titlelst[self.currentChannel - 1:]
        # After = Titlelst[:self.currentChannel - 1]
        if DEBUG == 'true':
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "DEBUGGING: setOnNow finished", 1000, THUMB) )
        self.log('setOnNow return')     

 
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
          
        self.getControl(101).setLabel('Loading Channel')
        self.getControl(102).setVisible(False)
        self.getControl(119).setVisible(False)
        self.getControl(130).setVisible(False)
        self.getControl(120).setVisible(False)
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
        self.log("setChannel, about to load");

        if xbmc.PlayList(xbmc.PLAYLIST_MUSIC).load(self.channels[channel - 1].fileName) == False:
            self.log("Error loading playlist", xbmc.LOGERROR)
            self.InvalidateChannel(channel)
            return

        # Disable auto playlist shuffling if it's on
        if xbmc.getInfoLabel('Playlist.Random').lower() == 'random':
            self.log('setChannel, Random on.  Disabling.')
            xbmc.PlayList(xbmc.PLAYLIST_MUSIC).unshuffle()
  
        self.log("setChannel, repeat all");
        xbmc.executebuiltin("PlayerControl(repeatall)")
        curtime = time.time()
        timedif = (curtime - self.channels[self.currentChannel - 1].lastAccessTime)
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            pass
            
        self.log('setChannel, Chtype = ' + str(chtype))
        
        if self.channels[self.currentChannel - 1].isPaused == False:
            # adjust the show and time offsets to properly position inside the playlist
            #for Live TV get the first item in playlist convert to epoch time  add duration until we get to the current item
            if chtype == 8:
                self.channels[self.currentChannel - 1].setShowPosition(0)
                tmpDate = self.channels[self.currentChannel - 1].getItemtimestamp(0)
                self.logDebug("setChannel, overlay tmpdate " + str(tmpDate))
                
                try:#sloppy fix, for threading issue with strptime.
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                except:
                    t = time.strptime(tmpDate, '%Y-%m-%d %H:%M:%S')
                    pass
                    
                epochBeginDate = time.mktime(t)
                #beginDate = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                #index till we get to the current show
                while epochBeginDate + self.channels[self.currentChannel - 1].getCurrentDuration() <  curtime:
                    self.logDebug('epoch '+ str(epochBeginDate) + ', ' + 'time ' + str(curtime))
                    epochBeginDate += self.channels[self.currentChannel - 1].getCurrentDuration()
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    self.logDebug('live tv overlay while loop')
            else:   #loop for other channel types
                while self.channels[self.currentChannel - 1].showTimeOffset + timedif > self.channels[self.currentChannel - 1].getCurrentDuration():
                    timedif -= self.channels[self.currentChannel - 1].getCurrentDuration() - self.channels[self.currentChannel - 1].showTimeOffset
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    self.channels[self.currentChannel - 1].setShowTime(0)

        # First, check to see if the video is a strm
        if self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)[-4:].lower() == 'strm' or chtype >= 8:
            self.log("setChannel, Ignoring a stop because of a strm or chtype >= 8")
            self.Player.ignoreNextStop = True

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
            
        # Mute the channel before changing
        self.log("setChannel, about to mute");
        xbmc.executebuiltin("Mute()");           
        xbmc.sleep(self.channelDelay)
        
        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(curtime)
        
        if mediapath[0:4] == 'hdhomerun' or mediapath[0:4] == 'rtmp' or mediapath[0:4] == 'rtsp' or mediapath[0:4] == 'http':
            #use item player for two reasons, seektime not needed, setInfo fills kodi meta properties.
            self.log("setChannel, using listitem player")
            if mediapath[0:4] == 'rtmp' or mediapath[0:4] == 'rtsp':
                mediapath = (mediapath + ' live=1 timeout=20')    
                
            listitem = xbmcgui.ListItem()
            genre = (self.channels[self.currentChannel - 1].getItemgenre(self.channels[self.currentChannel - 1].playlistPosition))
            title = (self.channels[self.currentChannel - 1].getItemTitle(self.channels[self.currentChannel - 1].playlistPosition))
            listitem.setInfo('video', {'Title': title, 'Genre': genre})
            self.Player.play(mediapath,listitem, 0)            
            # self.PlayerTimeout(self.ActionTimeInt)
        else:
            self.log("setChannel, using playlist player")
            self.log("playing selected file");
            self.Player.playselected(self.channels[self.currentChannel - 1].playlistPosition)
            
            # set the show offset
            if self.channels[self.currentChannel - 1].isPaused:
                self.channels[self.currentChannel - 1].setPaused(False)
                if plugchk not in BYPASS_SEEK:
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
                if plugchk not in BYPASS_SEEK:
                    self.log("Seeking")
                    seektime1 = self.channels[self.currentChannel - 1].showTimeOffset + timedif + int((time.time() - curtime))
                    seektime2 = self.channels[self.currentChannel - 1].showTimeOffset + timedif
                    overtime = float((int(self.channels[self.currentChannel - 1].getItemDuration(self.channels[self.currentChannel - 1].playlistPosition))/8)*6)
            
                    if (mediapath[-4:].lower() == 'strm' or mediapath[0:6].lower() == 'plugin'):
                        self.seektime = self.SmartSeek(mediapath, seektime1, seektime2, overtime)
                    else:
                        try:
                            self.Player.seekTime(seektime1)
                            self.log("seektime1")
                        except:
                            self.log("Unable to set proper seek time, trying different value")
                            try:
                                self.Player.seekTime(seektime2)
                                self.log("seektime2")
                            except:
                                self.log('Exception during seek', xbmc.LOGERROR)
                                pass 
                                
        if self.UPNP:
            self.PlayUPNP(mediapath, self.seektime)   
            
        # if self.Player.ignoreNextStop == True:
            # self.PlayerTimeout(self.ActionTimeInt)
            
        # Seek without infobar work around todo? needs testing...
        # http://forum.xbmc.org/showthread.php?pid=1547665#pid1547665
        # listitem = xbmcgui.ListItem()
        # listitem.setProperty('StartOffset', str(randomStart))
        # playlist.add(str(filename), listitem, 0)
        
        # url = str(mediapath)
        # print url, str(self.seektime)
        # listitem = xbmcgui.ListItem()
        # listitem.setInfo('video', {'Title': 'test', 'Genre': 'Sports'})
        # listitem.setProperty('StartOffset', str(self.seektime))
        # self.Player.play(url,listitem, 0)
        
        # fix rtmp playable todo
        # rtmp://url_stuff_as_normal.stream live=1 timeout=20

        # Unmute
        self.log("Finished, unmuting");
        xbmc.executebuiltin("Mute()");
        
        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
        self.runActions(RULES_ACTION_OVERLAY_SET_CHANNEL_END, channel, self.channels[channel - 1])
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
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
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
        self.log('setShowInfo, setshowposition = ' + str(position)) 
        
        #Artwork Handling
        mediapath = (self.channels[self.currentChannel - 1].getItemFilename(position))       
        chname = (self.channels[self.currentChannel - 1].name)
        self.SetMediaInfo(chtype, chname, mediapath, position)
        
        
    def SetMediaInfo(self, chtype, chname, mediapath, position):
        self.log('SetMediaInfo')  
        # tmpstr = self.GetFileInfo(mediapath)
        # use xbmc player info todo
        # compare to ptvl to detect ondemand?
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
            LiveID = self.channelList.unpackLiveID(LiveID)
            
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
        
        ##LIVEID##
        type = LiveID[0]
        id = LiveID[1]
        dbid = LiveID[2]
        Managed = LiveID[3]
        playcount = int(LiveID[4])        
        
        #PVR Globals
        self.PVRchtype = chtype
        self.PVRmediapath = mediapath
        self.PVRchname = chname
        self.PVRtitle = title
        self.PVRtype = type
        self.PVRdbid = dbid
        self.PVRid = id
        
        if mediapath[0:5] == 'stack':
            smpath = (mediapath.split(' , ')[0]).replace('stack://','').replace('rar://','')
            mpath = (os.path.split(smpath)[0]) + '/'
        elif mediapath[0:6] == 'plugin':
            mpath = 'plugin://' + mediapath.split('/')[2] + '/'
        elif mediapath[0:4] == 'upnp':
            mpath = 'upnp://' + mediapath.split('/')[2] + '/'
        else:
            mpath = (os.path.split(mediapath)[0]) + '/'

        #Sickbeard/Couchpotato
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
            self.getControl(508).setVisible(False)
            type1EXT = REAL_SETTINGS.getSetting('type1EXT_Overlay')
            self.setArtwork1(type, chtype, chname, id, dbid, mpath, type1EXT)
        except:
            self.log('setShowInfo, Label 507 not found')
            pass
           
        #Dynamic Art2
        try:
            self.getControl(510).setVisible(False)
            type2EXT = REAL_SETTINGS.getSetting('type2EXT_Overlay')
            self.setArtwork2(type, chtype, chname, id, dbid, mpath, type2EXT)
        except:
            self.log('setShowInfo, Label 509 not found')
            pass
               
               
    def setArtwork1(self, type, chtype, chname, id, dbid, mpath, type1EXT):
        try:
            if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
                setImage1 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type1EXT)
            else:
                setImage1 = self.Artdownloader.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, type1EXT)
            self.getControl(508).setImage(setImage1)
            self.getControl(508).setVisible(True)
        except:
            self.getControl(508).setVisible(False)
            self.log('setArtwork1, Failed!')
            pass  
    
    
    def setArtwork2(self, type, chtype, chname, id, dbid, mpath, type2EXT):
        try: 
            if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
                setImage2 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type2EXT)
            else:
                setImage2 = self.Artdownloader.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, type2EXT)
            self.getControl(510).setImage(setImage2)
            self.getControl(510).setVisible(True)
        except:
            self.getControl(510).setVisible(False)
            self.log('setArtwork2, Failed!')
            pass
    
    
    # Display the current channel based on self.currentChannel.
    # Start the timer to hide it.
    def showChannelLabel(self, channel):
        self.log('showChannelLabel ' + str(channel))
        chtype = (ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
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
                if int(chtype) != 8:
                    setImage = self.Artdownloader.FindBug(chtype, chname, mediapath)
                    self.getControl(103).setImage(setImage)  
                else:
                    self.getControl(103).setImage('NA.png')
            else:
                self.getControl(103).setImage('NA.png')
        except:
            pass
                
        # Channel name label #      
        self.getControl(300).setLabel(self.channels[self.currentChannel - 1].name)
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
        self.log('hideInfo')
        try:
            self.getControl(102).setVisible(False)
            self.infoOffset = 0

            if self.infoTimer.isAlive():
                self.infoTimer.cancel()
            self.infoTimer = threading.Timer(5.0, self.hideInfo)
            xbmc.sleep(100)
            self.showingInfo = False
        except:
            pass
        
        
    def showInfo(self, timer):
        self.log("showInfo")
        try:
            if self.hideShortItems:
                position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
                try:
                    chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
                except:
                    chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
                    pass
                    
                # if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(position) < self.shortItemLength:
                    # return
                    
                if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()) < self.shortItemLength:
                    return
                    
            self.getControl(102).setVisible(True)
            if self.showingPop == False:
                self.showingInfo = True
                self.setShowInfo()

            if self.infoTimer.isAlive():
                self.infoTimer.cancel()

            self.infoTimer = threading.Timer(timer, self.hideInfo)
            self.infoTimer.name = "InfoTimer"        
            
            if xbmc.getCondVisibility('Player.ShowInfo'):
                json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
                self.ignoreInfoAction = True
                self.channelList.sendJSON(json_query);
                
            self.infoTimer.start()
        except:
            pass

            
    def hideMenuAlt(self):
        self.log("hideMenuAlt")
        try:
            self.list.setVisible(False)
            self.getControl(130).setVisible(False)                       
            self.setFocusId(998)
            self.showMenu(self.InfTimer)
            
            if self.MenuAltTimer.isAlive():
                self.MenuAltTimer.cancel()
            
            self.MenuAltTimer = threading.Timer(5.0, self.hideMenuAlt)
            xbmc.sleep(100)
            self.showingMenuAlt = False    
        except:
            pass
            
        
    def ShowMenuAlt(self, timer):
        self.log("ShowMenuAlt")
        try:
            self.hideInfo()
            self.hidePOP()
            # skin control todo
            # xpos = int(self.getControl(132).getLabel())
            # ypos = int(self.getControl(132).getLabel2())
            # print xpos, ypos
            
            if not self.showingMenuAlt:
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
                curchannel = 0
                self.showingMenuAlt = True
                self.setOnNow()
                # 'button-nofocus.png'
                self.list = xbmcgui.ControlList(198, 160, -50, 600, 'font12', self.myEPG.textcolor, BUTTON_NO_FOCUS_ALT, BUTTON_FOCUS, self.myEPG.focusedcolor, 0, 0, 0, 0, 40, 0, 100)
                self.list.setWidth(260)
                self.addControl(self.list)
                self.list.addItems(items=self.OnNowTitleLst)
                self.getControl(131).setImage('NA.png')
                
                for i in range(len(self.OnNowTitleLst)):
                    item = self.OnNowTitleLst[i]
                    title = (item.split(')')[1]).replace('[/B][/COLOR] ','')
                    if title.lower() == self.PVRtitle.lower():
                        break
                    
                self.list.selectItem(i)
                self.getControl(130).setVisible(True)
                self.list.setVisible(True)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.sleep(100)
                self.setFocus(self.list)
                self.setOnNowArt()
            
            if self.MenuAltTimer.isAlive():
                self.MenuAltTimer.cancel()

            self.MenuAltTimer = threading.Timer(timer, self.hideMenuAlt)
            self.MenuAltTimer.name = "MenuAltTimer" 
            self.MenuAltTimer.start()
        except:
            pass
    
    
    def pauseMenuAlt(self):
        self.log("pauseMenuAlt")
        try:
            if self.MenuAltTimer.isAlive():
                self.MenuAltTimer.cancel()      
        except:
            pass
        
        
    def hideMenu(self):    
        self.log("hideMenu")
        try:
            self.hideMenuAlt()  
            self.getControl(119).setVisible(False)
            
            if self.MenuTimer.isAlive():
                self.MenuTimer.cancel()
            
            self.MenuTimer = threading.Timer(5.0, self.hideMenu)
            xbmc.sleep(100)
            self.showingMenu = False
            xbmc.sleep(100)
        except:
            pass
        
        
    def showMenu(self, timer):
        self.log("showMenu")
        try:
            self.hideInfo()
            self.hidePOP()
           
            #Set button labels n logo
            self.getControl(995).setImage(THUMB)
            self.getControl(997).setLabel('Now Playing')
            self.getControl(998).setLabel('OnNow')
            self.getControl(999).setLabel('OnDemand')
            self.getControl(1000).setLabel('NextAired')
            self.getControl(1001).setLabel('')
            self.getControl(1002).setLabel('')
            self.getControl(1003).setLabel('EPGType')
            self.getControl(1004).setLabel('Last Channel')
            self.getControl(1005).setLabel('Mute')
            self.getControl(1006).setLabel('Subtitle')
            self.getControl(1007).setLabel('Player Control')
            self.getControl(1008).setLabel('Sleep')
            self.getControl(1009).setLabel('')
            self.getControl(1010).setLabel('Exit')
                
            if not self.showingMenu:      
                #Set first button focus, show menu
                self.showingMenu = True    
                self.getControl(119).setVisible(True)
                self.setFocusId(997) 
                xbmc.sleep(100)   
                self.setFocusId(997)    
                
            if self.MenuTimer.isAlive():
                self.MenuTimer.cancel()

            self.MenuTimer = threading.Timer(timer, self.hideMenu)
            self.MenuTimer.name = "MenuTimer" 
            self.MenuTimer.start()
        except:
            pass
            
        
    def pauseMenu(self):
        self.log("pauseMenu")
        try:
            if self.MenuTimer.isAlive():
                self.MenuTimer.cancel()      
        except:
            pass
            
        
    def hidePOP(self):
        self.log("hidePOP")
        try:
            self.infoOffset = 0
            self.getControl(120).setVisible(False)

            if self.popTimer.isAlive():
                self.popTimer.cancel()

            self.popTimer = threading.Timer(5.0, self.hidePOP)
            self.getControl(103).setVisible(True)
            xbmc.sleep(100)
            self.showingPop = False
        except:
            pass
                     
                     
    def showPOP(self, timer):
        self.log("showPOP")
        try:
            #disable channel bug
            self.getControl(103).setVisible(False)
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            except:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
                pass

            if self.hideShortItems:
                #Skip short videos
                position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition() + self.infoOffset
                if self.channels[self.currentChannel - 1].getItemDuration(position) < self.shortItemLength:
                    return
                    
            if self.showingInfo == False:
                self.showingPop = True
                self.getControl(120).setVisible(True)

            if self.popTimer.isAlive():
                self.popTimer.cancel()

            self.popTimer = threading.Timer(timer, self.hidePOP)
            self.popTimer.name = "popTimer"
            self.popTimer.start()
        except:
            pass
            
            
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
        self.IdleSeconds = 300 #5min
        self.PausedPlayback = bool(xbmc.getCondVisibility("Player.Paused"))
        self.ActivePlayback = bool(xbmc.Player().isPlaying())
        self.xbmcIdle = int(xbmc.getGlobalIdleTime())
        
        if self.showingEPG or self.PausedPlayback:
            idling = True 
        else: 
            idling = False 
            
        if self.xbmcIdle >= self.IdleSeconds and idling == True:
                if self.showingIdle == False:
                    self.showingIdle = True
                    xbmc.executebuiltin('XBMC.RunScript(' + ADDON_PATH + '/resources/lib/idle.py)')
        else:
            self.showingIdle = False
        
        self.log("IdleTimer, XBMCidle = " + str(self.xbmcIdle) + ", IdleSeconds = " + str(self.IdleSeconds) + ', PausedPlayback = ' + str(self.PausedPlayback) + ', showingIdle = ' + str(self.showingIdle) + ', showingEPG = ' + str(self.showingEPG) + ', ActivePlayback = ' + str(self.ActivePlayback))
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
        self.log('onFocus ' + str(controlId))
        
        
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
                self.log("Now Playing")
                self.pauseMenu()  
                print self.PVRtype, self.PVRdbid, self.PVRtitle, self.PVRid
                if self.PVRtype == 'tvshow':
                    info = 'extendedtvinfo'
                    dbtype = 'tvdb_id'
                else:
                    info = 'extendedinfo'
                    dbtype = 'imdbid'

                xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,name=%s,%s=%s)" % (info, self.PVRdbid, self.PVRtitle, dbtype, self.PVRid))
                self.showMenu(self.InfTimer)
                
        elif controlId == 998:
            if self.showingMenu:
                self.log("OnNow")
                self.pauseMenu()
                self.ShowMenuAlt(self.InfTimer)
                # self.pauseMenuAlt()
                
        elif controlId == 999:
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
                
        elif controlId == 1000:
            if self.showingMenu:
                self.log("NextAired")
                # self.hideMenu()  
                # self.showingNextAired = True
                # xbmc.executebuiltin("RunScript(script.tv.show.next.aired)")
                
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
                self.log("LastChannel")
                self.LastChannelJump()
                self.setChannel(self.LastChannel)
                self.hideMenu()    
                
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
    
    
    def onControl(self, controlId):
        self.log('onControl ' + str(controlId))
        pass

        
    # Handle all input while videos are playing
    def onAction(self, act):
        action = act.getId()
        self.log('onAction ' + str(action))
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            pass
            
        try:
            mediapath = self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)
            try:
                plugchk = mediapath.split('/')[2]
            except:
                plugchk = mediapath
                pass
        except:
            mediapath = ''
            plugchk = ''
            pass
            
        if self.Player.stopped:
            return

        # Since onAction isnt always called from the same thread (weird),
        # ignore all actions if we're in the middle of processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return
        elif self.showingNextAired:
            return
        lastaction = time.time() - self.lastActionTime

        # during certain times we just want to discard all input
        if lastaction < 2:
            self.log('Not allowing actions')
            action = ACTION_INVALID

        self.startSleepTimer()

        if action == ACTION_SELECT_ITEM:
            if self.showingMenuAlt:
                self.hideMenu()
                try:
                    item = self.list.getSelectedItem()
                    channel = (((item.getLabel()).split(')')[0]).replace('[B]',''))
                    channel = re.sub('\[COLOR=(.+?)\]', '', channel)
                    self.setChannel(int(channel))
                except:
                    pass
            elif not self.showingMenu:
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
            if self.showingMenuAlt:
                self.setOnNowArt()
            elif not self.showingMenu:
                self.channelUp()
            else:
                self.showMenu(self.InfTimer)
                
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            if self.showingMenuAlt:
                self.setOnNowArt()
            elif not self.showingMenu:
                self.channelDown()
            else:
                self.showMenu(self.InfTimer)
                
        elif action == ACTION_MOVE_LEFT:   
            if self.showingMenuAlt:
                self.hideMenuAlt()
            elif self.showingMenu:
                self.hideMenu()
            elif self.showingInfo:
                self.infoOffset -= 1  
                
                if self.infoOffset < 0:
                    self.showMenu(self.InfTimer)
                elif not self.showingMenu:
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
            if self.showingMenuAlt:
                self.hideMenuAlt()
            elif self.showingMenu:
                self.hideMenu()
            elif self.showingInfo:
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
            if self.ignoreInfoAction:
                self.ignoreInfoAction = False
            else:
                if self.showingInfo:
                    self.hidePOP()
                    self.hideMenu()
                    self.hideInfo()           
            
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
        try:
            if self.sleepTimeValue == 0:
                return

            # Cancel the timer if it is still running
            if self.sleepTimer.isAlive():
                self.sleepTimer.cancel()
                self.sleepTimer = threading.Timer(self.sleepTimeValue, self.sleepAction)

            if self.Player.stopped == False:
                self.sleepTimer.name = "SleepTimer"
                self.sleepTimer.start()
        except:
            pass
    
    
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
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
                        pass
                    title = 'Coming Up Next'   
                    ShowTitle = self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', '')
                    myLiveID = self.channels[self.currentChannel - 1].getItemLiveID(nextshow)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    dbid = (self.channelList.unpackLiveID(myLiveID))[2]
                        
                    if mediapath[0:5] == 'stack':
                        smpath = (mediapath.split(' , ')[0]).replace('stack://','').replace('rar://','')
                        mpath = (os.path.split(smpath)[0]) + '/'
                    elif mediapath[0:6] == 'plugin':
                        mpath = 'plugin://' + mediapath.split('/')[2] + '/'
                    elif mediapath[0:4] == 'upnp':
                        mpath = 'upnp://' + mediapath.split('/')[2] + '/'
                    else:
                        mpath = (os.path.split(mediapath)[0]) + '/'
                    
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
                        type1EXT = REAL_SETTINGS.getSetting('type1EXT_Overlay')
                        
                        if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
                            NotifyTHUMB = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type1EXT)
                        else:
                            NotifyTHUMB = self.Artdownloader.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, type1EXT)
                            
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

        
    def PlayerTimeout(self, sleepTime):
        self.log("PlayerTimeout") 
        try:
            start_time = self.Player.getTime()   
        except:
            start_time = 0
        xbmc.sleep(sleepTime)
        try:
            if self.Player.getTime() == start_time: 
                raise
        except:
            self.getControl(101).setLabel('Playback Failed')
            json_query = '{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"stop"},"id":1}'
            self.channelList.sendJSON(json_query);
        
        
    def playerTimerAction(self):
        self.log("playerTimerAction")
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)  

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            pass

        if self.Player.isPlaying():
            self.notPlayingCount = 0   
            self.lastPlayTime = int(self.Player.getTime())
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()                  
        else:          
            self.notPlayingCount += 1
            self.log("Adding to notPlayingCount, " + str(self.notPlayingCount)) 

        if self.notPlayingCount > 5:
            # if chtype <= 7:
                # self.getControl(101).setLabel('Error Loading: Changing Channel')
                # self.Player.playnext()
                # MSG = "Playback Failed - Skipping Program"
            # else:
            if self.notPlayingAction == 'Down':
                self.channelDown()
                MSG = "Playback Failed - Changing Channel Down"
            elif self.notPlayingAction == 'Last':
                self.LastChannelJump()
                self.setChannel(self.LastChannel)
                MSG = "Playback Failed - Returning to Previous Channel"
            else:
                self.channelUp()
                MSG = "Playback Failed - Changing Channel Up"

            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
                
            self.playerTimer.start()   
            self.log("error invalid channel, Changing Channel")
            return
        else:
            if DEBUG == 'true' and self.notPlayingCount > 1:
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "notPlayingCount " + str(self.notPlayingCount), 1000, THUMB) )
        
        if self.Player.stopped == False:
            self.playerTimer.name = "PlayerTimer"
            self.playerTimer.start()
    
    
    # Adapted from lamdba's plugin.video.genesis
    # def change_watched(self):
        # if self.content == 'movie':
            # try:
                # from metahandler import metahandlers
                # metaget = metahandlers.MetaData(preparezip=False)

                # metaget.get_meta('movie', self.title ,year=self.year)
                # metaget.change_watched(self.content, '', self.imdb, season='', episode='', year='', watched=7)
            # except:
                # pass

            # try:
                # if not getSetting("watched_trakt") == 'true': raise Exception()
                # if (link().trakt_user == '' or link().trakt_password == ''): raise Exception()
                # imdb = self.imdb
                # if not imdb.startswith('tt'): imdb = 'tt' + imdb
                # url = 'http://api.trakt.tv/movie/seen/%s' % link().trakt_key
                # post = {"movies": [{"imdb_id": imdb}], "username": link().trakt_user, "password": link().trakt_password}
                # result = getUrl(url, post=json.dumps(post), timeout='30').result
            # except:
                # pass

            # try:
                # if not getSetting("watched_library") == 'true': raise Exception()
                # try: movieid = self.meta['movieid']
                # except: movieid = ''

                # if movieid == '':
                    # movieid = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
                    # movieid = unicode(movieid, 'utf-8', errors='ignore')
                    # movieid = json.loads(movieid)['result']['movies']
                    # movieid = [i for i in movieid if i['file'].endswith(self.file)][0]
                    # movieid = movieid['movieid']

                # while xbmc.getInfoLabel('Container.FolderPath').startswith(sys.argv[0]) or xbmc.getInfoLabel('Container.FolderPath') == '': xbmc.sleep(1000)
                # xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }' % str(movieid))
            # except:
                # pass

        # elif self.content == 'episode':
            # try:
                # from metahandler import metahandlers
                # metaget = metahandlers.MetaData(preparezip=False)

                # metaget.get_meta('tvshow', self.show, imdb_id=self.imdb)
                # metaget.get_episode_meta(self.show, self.imdb, self.season, self.episode)
                # metaget.change_watched(self.content, '', self.imdb, season=self.season, episode=self.episode, year='', watched=7)
            # except:
                # pass

            # try:
                # if not getSetting("watched_trakt") == 'true': raise Exception()
                # if (link().trakt_user == '' or link().trakt_password == ''): raise Exception()
                # imdb = self.imdb
                # if not imdb.startswith('tt'): imdb = 'tt' + imdb
                # season, episode = int('%01d' % int(self.season)), int('%01d' % int(self.episode))
                # url = 'http://api.trakt.tv/show/episode/seen/%s' % link().trakt_key
                # post = {"imdb_id": imdb, "episodes": [{"season": season, "episode": episode}], "username": link().trakt_user, "password": link().trakt_password}
                # result = getUrl(url, post=json.dumps(post), timeout='30').result
            # except:
                # pass

            # try:
                # if not getSetting("watched_library") == 'true': raise Exception()
                # try: episodeid = self.meta['episodeid']
                # except: episodeid = ''

                # if episodeid == '':
                    # episodeid = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["file"]}, "id": 1}' % (self.season, self.episode))
                    # episodeid = unicode(episodeid, 'utf-8', errors='ignore')
                    # episodeid = json.loads(episodeid)['result']['episodes']
                    # episodeid = [i for i in episodeid if i['file'].endswith(self.file)][0]
                    # episodeid = episodeid['episodeid']

                # while xbmc.getInfoLabel('Container.FolderPath').startswith(sys.argv[0]) or xbmc.getInfoLabel('Container.FolderPath') == '': xbmc.sleep(1000)
                # xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }' % str(episodeid))
            # except:
                # pass
                
                
    def Unwatch(self, type, title, imdbid, season, episode, year, watched):
        self.log('Unwatch')
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }' % str(movieid))
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }' % str(episodeid))
        try:        
            from metahandler import metahandlers
            self.metaget = metahandlers.MetaData(preparezip = False)
            self.metaget.change_watched(type, title, imdbid, season=season, episode=episode, year='', watched=watched)
        except:
            self.log('Unwatch Failed')
            pass
    
    
    def Paused(self):
        self.log('Paused')
        self.getControl(101).setLabel('Paused')
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
                
            self.channelList.SyncUSTVnow(True, False)
            self.channelList.SyncSSTV(True, False)
            self.channelList.SyncFTV(True, False)
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
        return tmpstr
         
         
    def PreArtService(self):
        self.log('PreArtService')
        # ADDON_SETTINGS.loadSettings()
        exclude = ['#EXTM3U', '#EXTINF']
        i = 0
        lineLST = []
        newLST = []
        ArtLST = []
        
        for i in range(999):
            chtype = -1
            id = -1
            type = ''
            mpath = ''
            
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chname = (self.channels[i + 1].name)
                fle = xbmc.translatePath(os.path.join(LOCK_LOC, ("channel_" + str(i + 1) + '.m3u')))
            except:
                chtype = 0
                chname = ''
                fle = ''
                pass
                
            if chtype >= 0 and fle != '':
                try:
                    if FileAccess.exists(fle):
                        f = FileAccess.open(fle, 'r')
                        lineLST = f.readlines()
                        lineLST.pop(0) #Remove unwanted first line '#EXTM3U'
                        for n in range(len(lineLST)):
                            line = lineLST[n]
                            
                            if line[0:7] == '#EXTINF':
                                liveid = line.rsplit('//',1)[1]
                                type = liveid.split('|')[0]
                                id = liveid.split('|')[1]
                                dbid = liveid.split('|')[2]
                                
                            elif line[0:7] not in exclude:
                                if id != -1:
                                    if line[0:5] == 'stack':
                                        smpath = (line.split(' , ')[0]).replace('stack://','').replace('rar://','')
                                        mpath = (os.path.split(smpath)[0]) + '/'
                                    elif line[0:6] == 'plugin':
                                        mpath = 'plugin://' + line.split('/')[2] + '/'
                                    elif line[0:4] == 'upnp':
                                        mpath = 'upnp://' + line.split('/')[2] + '/'
                                    else:
                                        mpath = (os.path.split(line)[0]) + '/'

                                    if type and mpath:
                                        newLST = [type, chtype, chname, id, dbid, mpath]
                                        ArtLST.append(newLST)
                except:
                    pass
                    
        # shuffle list to evenly distribute queue
        random.shuffle(ArtLST)
        self.log('PreArtService, ArtLST Count = ' + str(len(ArtLST)))
        return ArtLST

        
    def ArtService(self):
        self.log('ArtService')  
        if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
            REAL_SETTINGS.setSetting('ArtService_Running', "true")
            start = datetime.datetime.today()
            ArtLst = self.PreArtService() 
            
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Spooler Started", 4000, THUMB) )
            
            # Clear Artwork Cache Folders
            if REAL_SETTINGS.getSetting("ClearLiveArtCache") == "true":
                artwork.delete("%") 
                artwork1.delete("%")
                artwork2.delete("%")
                artwork3.delete("%")
                artwork4.delete("%")
                artwork5.delete("%")
                artwork6.delete("%")
                self.log('ArtService, ArtCache Purged!')
                REAL_SETTINGS.setSetting('ClearLiveArtCache', "false")
                
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Cache Cleared", 4000, THUMB) )
                xbmc.sleep(5)
                
            try:
                type1EXT_Overlay = REAL_SETTINGS.getSetting('type1EXT_Overlay')
            except:
                type1EXT_Overlay = ''
                pass
                
            try:
                type2EXT_Overlay = REAL_SETTINGS.getSetting('type2EXT_Overlay')
            except:
                type2EXT_Overlay = ''
                pass
                
            try:
                type1EXT_EPG = REAL_SETTINGS.getSetting('type1EXT_EPG')
            except:
                type1EXT_EPG = ''
                pass
                
            try:
                type2EXT_EPG = REAL_SETTINGS.getSetting('type2EXT_EPG')
            except:
                type2EXT_EPG = ''
                pass
    
            for i in range(len(ArtLst)):
                setImage1 = ''
                setImage2 = ''
                lineLST = ArtLst[i]
                type = lineLST[0]
                chtype = lineLST[1]
                chname = lineLST[2]
                id = lineLST[3]
                dbid = lineLST[4]
                mpath = lineLST[5]
                
                if type1EXT_Overlay != '': 
                    setImage1 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type1EXT_Overlay)
    
                if type2EXT_Overlay != '':
                    setImage2 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type2EXT_Overlay)
                                 
                if type1EXT_EPG != '': 
                    setImage1 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type1EXT_EPG)
    
                if type2EXT_EPG != '':
                    setImage2 = self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, type2EXT_EPG)
                 
            stop = datetime.datetime.today()
            finished = stop - start
            MSSG = ("Artwork Spooled in %d seconds" %finished.seconds)              
            REAL_SETTINGS.setSetting("ArtService_Running","false")
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(stop))
            
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 1000, THUMB) ) 

                
    def EXTtype(self, arttype): 
        self.log('EXTtype')
        JPG = ['banner', 'fanart', 'folder', 'landscape', 'poster']
        PNG = ['character', 'clearart', 'logo', 'disc']
        
        if arttype in JPG:
            arttypeEXT = (arttype + '.jpg')
        else:
            arttypeEXT = (arttype + '.png')
        self.logDebug('EXTtype = ' + str(arttypeEXT))
        return arttypeEXT
      

    def end(self):
        self.log('end')  
        self.isExiting = True   
        self.getControl(101).setLabel('Exiting')
        # Prevent the player from setting the sleep timer
        self.Player.stopped = True
        self.background.setVisible(True)
        self.getControl(119).setVisible(False)
        self.getControl(130).setVisible(False)
        self.getControl(120).setVisible(False)
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

            if self.channelThread_Timer.isAlive():
                self.channelThread_Timer.cancel()
                self.channelThread_Timer.join()

            if self.ArtServiceThread.isAlive():
                self.ArtServiceThread.cancel()
                self.ArtServiceThread.join()

            if self.AutoJumpThread.isAlive():
                self.AutoJumpThread.cancel()
                self.AutoJumpThread.join()

            if self.MenuTimer.isAlive():
                self.MenuTimer.cancel()
                self.MenuTimer.join()
                
            if self.MenuAltTimer.isAlive():
                self.MenuAltTimer.cancel()
                self.MenuAltTimer.join()
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