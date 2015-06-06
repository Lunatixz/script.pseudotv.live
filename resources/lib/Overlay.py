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

from Playlist import Playlist
from Globals import *
from Channel import Channel
from EPGWindow import EPGWindow
from ChannelList import ChannelList
from ChannelListThread import ChannelListThread
from FileAccess import FileAccess
from Migrate import Migrate
from Artdownloader import *
from Upnp import Upnp
from PVR import *
from utils import *
from urllib import unquote, quote

try:
    from PIL import Image
    from PIL import ImageEnhance
except:
    REAL_SETTINGS.setSetting("UNAlter_ChanBug","true")
    
try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo-web/submit.php'
except:
    pass

sys.setrecursionlimit(10000)

class MyPlayer(xbmc.Player):
    
    def __init__(self):
        self.log('__init__')
        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)
        self.channelList = ChannelList()
        self.stopped = False
        self.ignoreNextStop = False        
        
        
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Player: ' + msg, level)
    
  
    def PlaybackValid(self):
        PlaybackStatus = False
        xbmc.sleep(10)
        if self.isPlaying():
            PlaybackStatus = True
        self.log('PlaybackValid, PlaybackStatus = ' + str(PlaybackStatus))
        return PlaybackStatus
    
    
    def is_playback_paused(self):
        self.log('is_playback_paused')
        return bool(xbmc.getCondVisibility("Player.Paused"))

    
    def resume_playback(self):
        self.log('resume_playback')
        xbmc.sleep(10)
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
        clearProperty("Playing.OnDemand_tmpstr")
        if getProperty("PTVL.EPG_Opened") == "true" and self.overlay.VideoWindow == True and self.overlay.OnDemand == False:
            self.log('onPlayBackStarted, Force EPG Reload')
            self.overlay.myEPG.closeEPG() 
            xbmc.sleep(525)
            self.overlay.myEPG.doModal()
            
        self.resume_playback()
        xbmc.sleep(10)
        if self.PlaybackValid():
            file = xbmc.Player().getPlayingFile()
            file = file.replace("\\\\","\\")
            
            # if getProperty("PTVL.OVERLAY_INIT") == "true" and self.overlay.OnDemand == False:
                # if int(getProperty("Playing.Chtype")) <= 7 and file[0:4] != 'http':    
                    # if len(getProperty("Playing.Mediapath")) > 0 and (((getProperty("Playing.Mediapath"))[-4:].lower() != 'strm') or ((getProperty("Playing.Mediapath"))[0:6] != 'plugin')):
                        # print file.lower()
                        # print (getProperty("Playing.Mediapath")).lower()
                        # if file.lower() != (getProperty("Playing.Mediapath")).lower():
                            # self.overlay.OnDemand = True  
                # else:
                # if len(getProperty("Playing.Mediapath")) > 0 and len(getProperty("Playing.LastMediapath")) > 0:
                    # if (getProperty("Playing.Mediapath")).lower() != (getProperty("Playing.LastMediapath")).lower():
                        # self.overlay.OnDemand = True    
            # setProperty("Playing.LastMediapath",(getProperty("Playing.Mediapath")))                       
            self.log('onPlayBackStarted, OnDemand = '+ str(self.overlay.OnDemand))

            try:
                self.overlay.seektime = xbmc.Player().getTime()
            except:
                self.overlay.seektime = 0
                
            if self.overlay.UPNP:
                try:
                    self.overlay.PlayUPNP(file, self.overlay.seektime)  
                except: 
                    self.overlay.Error('Video Mirroring configuration error','Please verify IP and Port of Kodi Client')
                    pass
                            
            # Close epg after starting ondemand
            if getProperty("PTVL.EPG_Opened") == "true" and self.overlay.VideoWindow == True and self.overlay.OnDemand == True:
                self.log('onPlayBackStarted, Force Close EPG')
                self.overlay.myEPG.closeEPG()
                
            # Force showinfo ondemand
            if self.overlay.OnDemand == True:
                self.overlay.showInfo(self.overlay.InfTimer)
             
            self.overlay.PrimeSetOnNow()
            
    def onPlayBackEnded(self):
        self.log('onPlayBackEnded') 
        # self.finish()
        try:
            #Force next playlist item after impromptu play selection
            if self.overlay.OnDemand == True:
                self.overlay.OnDemand = False  
                xbmc.executebuiltin("PlayerControl(SmallSkipForward)")
        except:
            pass
    
    
    def onPlayBackStopped(self):
        # self.finish()
        try:
            if self.stopped == False:
                self.log('Playback stopped')
                #Force next playlist item after impromptu play selection
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
        except:
            pass
    
    
    def onPlayBackFailed(self):
        self.log('onPlayBackFailed')
    
    
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
        self.showingMoreInfo = False
        self.showingMenu = False
        self.showingStartover = False   
        self.showingNextAired = False
        self.showingMenuAlt = False
        self.OnAction = False
        self.DisableOverlay = False
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
        self.shortItemLength = 120
        self.runningActionChannel = 0
        self.channelDelay = 0
        self.channelbugcolor = CHANBUG_COLOR
        self.showSeasonEpisode = REAL_SETTINGS.getSetting("ShowSeEp") == "true"
        self.LastChannel = 0
        self.InfTimer = INFOBAR_TIMER[int(REAL_SETTINGS.getSetting('InfoTimer'))]
        self.Artdownloader = Artdownloader()
        self.notPlayingAction = 'Up'
        self.ActionTimeInt = float(REAL_SETTINGS.getSetting("ActionTimeInt"))
        self.Browse = ''
        self.MUTE = REAL_SETTINGS.getSetting('enable_mute') == "true"
        self.Quickflip = REAL_SETTINGS.getSetting('quickflip') == "true"
        self.lastActionCount = 0
        self.OnDemand = False  
        self.FavChanLst = (REAL_SETTINGS.getSetting("FavChanLst")).split(',')
        self.DirectInput = REAL_SETTINGS.getSetting("DirectInput") == "true"
        
        if REAL_SETTINGS.getSetting("UPNP1") == "true" or REAL_SETTINGS.getSetting("UPNP2") == "true" or REAL_SETTINGS.getSetting("UPNP3") == "true":
            self.UPNP = True
        else:
            self.UPNP = False
            
        if FileAccess.exists(os.path.join(XBMC_SKIN_LOC, 'custom_script.pseudotv.live_9506.xml')):
            self.VideoWindow = True
        else:
            self.VideoWindow = False

        for i in range(3):
            self.channelLabel.append(xbmcgui.ControlImage(50 + (50 * i), 50, 50, 50, IMAGES_LOC + 'solid.png', colorDiffuse = self.channelbugcolor))
            self.addControl(self.channelLabel[i])
            self.channelLabel[i].setVisible(False)
            
        setProperty("PTVL.OVERLAY_INIT","false")
        setProperty("ArtService_Running","false")
        self.doModal()
        self.log('__init__ return')
        
        
    def resetChannelTimes(self):
        for i in range(self.maxChannels):
            self.channels[i].setAccessTime(self.timeStarted - self.channels[i].totalTimePlayed)


    # override the doModal function so we can setup everything first
    def onInit(self):
        self.log('onInit')
        self.log('PTVL Version = ' + ADDON_VERSION)
        
        # Avoid cache collisions between artservice and channel building cache functions
        # Disable artwork till channel building is finished
        setProperty("EnableArtwork","false")
        
        try:
            self.getControl(101).setLabel('Please Wait')
        except:
            pass
            
        self.background = self.getControl(101)
        self.background.setVisible(True)
        self.getControl(102).setVisible(False)
        self.getControl(104).setVisible(False)
        self.getControl(222).setVisible(False)
        self.getControl(119).setVisible(False)
        self.getControl(130).setVisible(False)
        self.getControl(120).setVisible(False)
        
        try:
            self.getControl(508).setImage(THUMB)
            self.getControl(510).setImage(THUMB)
        except:
            pass

        self.channelList = ChannelList()
        self.Upnp = Upnp()
        dlg = xbmcgui.Dialog()
  
        self.settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
        self.nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.bak.xml'))
        self.atsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.pretune.xml'))
            
        try:
            Normal_Shutdown = REAL_SETTINGS.getSetting('Normal_Shutdown') == "true"
        except:
            REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
            Normal_Shutdown = REAL_SETTINGS.getSetting('Normal_Shutdown') == "true"
            
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live - Starting"}, "id": 1}')
        self.channelList.sendJSON(json_query)

        # Clear Setting2 for fresh autotune
        if REAL_SETTINGS.getSetting("Autotune") == "true" and REAL_SETTINGS.getSetting("Warning1") == "true":
            self.log('Autotune onInit') 
            try:
                self.getControl(101).setLabel('Initializing, Autotuning')
            except:
                pass
            #Reserve channel check            
            if REAL_SETTINGS.getSetting("reserveChannels") == "false":
                self.log('Autotune not reserved') 
                if getSize(self.settingsFile) > 100:
                    Backup(self.settingsFile, self.atsettingsFile)

                    if FileAccess.exists(self.atsettingsFile):
                        self.log('Autotune, Back Complete!')
                        f = FileAccess.open(self.settingsFile, "w")
                        f.write('\n')
                        self.log('Autotune, Setting2 Deleted...')
                        f.close()

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
                
        if FileAccess.exists(ART_LOC) == False:
            try:
                FileAccess.makedirs(ART_LOC)
            except:
                self.Error('Unable to create the artwork directory')
                return

        if getProperty("PseudoTVOutdated") == "true":
            json_query = ('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"script.pseudotv.live","enabled":true}, "id": 1}')
            self.channelList.sendJSON(json_query)
            okDialog('It is recommended you update your copy of PseudoTV Live')
        
        if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true":
            self.background.setLabel('Updating Guidedata...')
            SyncXMLTV()
                    
        if self.UPNP:
            self.background.setLabel('Initializing, Video Mirroring')
            self.StopUPNP()
            time.sleep(5)
            
        updateDialog = xbmcgui.DialogProgress()
        updateDialog.create("PseudoTV Live", "Initializing")
        self.background.setLabel('Initializing')
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
            
        # Overylay timers
        self.infoTimer = threading.Timer(self.InfTimer, self.hideInfo)
        self.popTimer = threading.Timer(5.0, self.hidePOP)
        self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)
        self.TogglesetVisibleTimer = threading.Timer(900.0, self.TogglesetVisible)
        
        try:
            self.myEPG = EPGWindow("script.pseudotv.live.EPG.xml", ADDON_PATH, Skin_Select)
            self.myDVR = EPGWindow("script.pseudotv.live.DVR.xml", ADDON_PATH, Skin_Select)
            self.myApps = EPGWindow("script.pseudotv.live.Apps.xml", ADDON_PATH, Skin_Select)
        except:
            pass  
            
        self.myEPG.MyOverlayWindow = self
        self.myDVR.MyOverlayWindow = self
        self.myApps.MyOverlayWindow = self
                    
        # if DEBUG == 'true':
            # try:
                # __addon__        = xbmcaddon.Addon('script.extendedinfo')
                # __cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
                # __resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
                # sys.path.append(__resource__)
                # import DialogVideoList, DialogVideoInfo
                # self.myOndemand = DialogVideoList.DialogVideoList(u'script.pseudotv.live.Ondemand.xml', ADDON_PATH)
                # self.myVideoInfo = DialogVideoInfo.DialogVideoInfo(u'script-PseudoTV Live-DialogVideoInfo.xml', ADDON_PATH)
            # except:
                # pass
                   
        # Don't allow any actions during initialization
        self.actionSemaphore.acquire()
        updateDialog.close()
        self.timeStarted = time.time() 
        updateDialog.update(95, "Initializing", "Channels")
        self.background.setLabel('Initializing Channels')

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
                REAL_SETTINGS.setSetting("MEDIA_LIMIT","0")
                REAL_SETTINGS.setSetting("PVR_Listing","0")
                REAL_SETTINGS.setSetting("autoFindLivePVR","true")
                REAL_SETTINGS.setSetting("autoFindNetworks","true")
                REAL_SETTINGS.setSetting("autoFindMovieGenres","true")
                REAL_SETTINGS.setSetting("autoFindRecent","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_RSS","true")
                REAL_SETTINGS.setSetting("autoFindCommunity_Youtube_Networks","true")
                if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true":
                    REAL_SETTINGS.setSetting("autoFindUSTVNOW","true")
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

        for i in range(self.maxChannels):
            if self.channels[i].isValid:
                found = True
                break

        if found == False:
            self.Error("Unable to populate channels. Please verify that you", "have scraped media in your library and that you have", "properly configured channels.")
            return

        # Auto-off startup timer
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
            # Scan through all chtype find valid channel then fixchannel, buggy?
            # for i in range(999):
                # try:
                    # chtype = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type')
                    # self.currentChannel = self.fixChannel(i+1)
                    # print 'curchan scan', str(chtype)
                    # break
                # except:
                    # pass

        if REAL_SETTINGS.getSetting('INTRO_PLAYED') != 'true':     
            self.background.setVisible(False)
            youtube_plugin = self.channelList.youtube_player()
            if youtube_plugin != False:
                self.Player.play(youtube_plugin + 'Y8WlAhpHzkM')
                time.sleep(17) 
                
            REAL_SETTINGS.setSetting("INTRO_PLAYED","true") 
                        
        self.resetChannelTimes()
        self.setChannel(self.currentChannel, self.Quickflip)
            
        self.startSleepTimer()
        self.startNotificationTimer()
        self.playerTimer.start()
        self.TogglesetVisibleTimer.start()
        setProperty("PTVL.FEEDtoggle","false")

        # Artwork types
        try:
            self.Arttype1 = str(self.getControl(507).getLabel())
            self.type1EXT = EXTtype(self.Arttype1)
            setProperty("type1EXT_Overlay",self.type1EXT)
        except:
            pass
        try:
            self.Arttype2 = str(self.getControl(509).getLabel())
            self.type2EXT = EXTtype(self.Arttype2)
            setProperty("type2EXT_Overlay",self.type2EXT)
        except:
            pass
        try:
            self.Arttype3 = str(self.getControl(121).getLabel())
            self.type3EXT = EXTtype(self.Arttype3)
            setProperty("type3EXT_Overlay",self.type3EXT)
        except:
            pass
            
        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()
        else:
            # self.ArtServiceThread = threading.Timer(float(self.InfTimer), self.ArtService)
            # self.ArtServiceThread.name = "ArtServiceThread"
            # self.ArtServiceThread.start()
            setProperty("EnableArtwork","true")
                
            if REAL_SETTINGS.getSetting("EnableSettop") == "true":
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
            
        setProperty("PTVL.OVERLAY_INIT","true")
        self.log('onInit return')
    

    def Settop(self):
        self.log('Settop')
        curtime = time.time()
        
        if REAL_SETTINGS.getSetting("SyncXMLTV_Enabled") == "true":
            SyncXMLTV()
            
        if CHANNEL_SHARING == True and self.isMaster:
            GlobalFileLock.unlockFile('MasterLock')
        
        GlobalFileLock.close()
        
        if self.timeStarted > 0 and self.isMaster:
            validcount = 0
        
            for i in range(self.maxChannels):
                if self.channels[i].isValid:
                    validcount += 1
        
            if validcount > 0:
                for i in range(self.maxChannels):
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
                
        self.channels = []
        ADDON_SETTINGS.loadSettings()
        
        if CHANNEL_SHARING == True:
            self.isMaster = GlobalFileLock.lockFile("MasterLock", False)
        else:
            self.isMaster = True
        
        self.backupFiles(False)
        self.timeStarted = time.time()
        self.channels = self.channelList.setupList(True)  
        # self.maxChannels = len(self.channels)   
        self.resetChannelTimes()
        # self.startSleepTimer()
        self.log('Settop, self.maxChannels = ' + str(self.maxChannels))
        time.sleep(2)
        
        if self.backgroundUpdating < 2 or self.isMaster == False:
            self.channelThread = ChannelListThread()
            self.channelThread.myOverlay = self
            self.channelThread.name = "ChannelThread"
            self.channelThread.start()
            
        if NOTIFY == True:
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Settop Update Started", 1000, THUMB) )

        
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
        self.backgroundUpdating = int(REAL_SETTINGS.getSetting("ThreadMode"))
        self.hideShortItems = REAL_SETTINGS.getSetting("HideClips") == "true"
        self.log("Hide Short Items - " + str(self.hideShortItems))
        self.shortItemLength = SHORT_CLIP_ENUM[int(REAL_SETTINGS.getSetting("ClipLength"))]
        self.log("Short item length - " + str(self.shortItemLength))
        self.channelDelay = int(REAL_SETTINGS.getSetting("ChannelDelay")) * 250
        
        if REAL_SETTINGS.getSetting("EnableSettop") == "true":
            REAL_SETTINGS.setSetting("ThreadMode","0")
            
        if REAL_SETTINGS.getSetting("EnableComingUp") != "0":
            self.showNextItem = REAL_SETTINGS.getSetting("showNextItem") == "true"
            
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
        try:
            self.notPlayingAction = 'Down'     
            if self.maxChannels == 1:
                return
                
            self.background.setVisible(True)
            channel = self.fixChannel(self.currentChannel - 1, False)
            self.setChannel(channel, self.Quickflip)      
        except:
            pass
        self.background.setVisible(False)
        self.log('channelDown return')  
        
        
    def backupFiles(self, updatedlg):
        self.log('backupFiles')

        if CHANNEL_SHARING == False:
            return
            
        if updatedlg:
            updatedlg.update(1, "Initializing", "Copying Channels...")
        realloc = REAL_SETTINGS.getSetting('SettingsFolder')
        FileAccess.copy(realloc + '/settings2.xml', SETTINGS_LOC + '/settings2.xml')
        realloc = xbmc.translatePath(os.path.join(realloc, 'cache')) + '/'

        for i in range(999):
            FileAccess.copy(realloc + 'channel_' + str(i) + '.m3u', CHANNELS_LOC + 'channel_' + str(i) + '.m3u')
            if updatedlg:
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
        try:
            self.notPlayingAction = 'Up'
            if self.maxChannels == 1:
                return
                
            self.background.setVisible(True)                
            channel = self.fixChannel(self.currentChannel + 1)
            self.setChannel(channel, self.Quickflip)
        except:
            pass
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
        self.MenuControl('MenuAlt',self.InfTimer)
        try:  
            pos = self.list.getSelectedPosition()            
            if getProperty("EnableArtwork") == "false":
                setImage = self.Artdownloader.SetDefaultArt_NEW(self.OnNowArtLst[pos][3], self.OnNowArtLst[pos][6], self.OnNowArtLst[pos][7])
            else:
                setImage = self.Artdownloader.FindArtwork_NEW(self.OnNowArtLst[pos][1], self.OnNowArtLst[pos][2], self.OnNowArtLst[pos][3], self.OnNowArtLst[pos][4], self.OnNowArtLst[pos][5], self.OnNowArtLst[pos][6], self.OnNowArtLst[pos][7])
                if FileAccess.exists(setImage) == False:
                    setImage = self.Artdownloader.SetDefaultArt_NEW(self.OnNowArtLst[pos][3], self.OnNowArtLst[pos][6], self.OnNowArtLst[pos][7])
            self.getControl(131).setImage(setImage)
        except:
            self.getControl(131).setImage('NA.png')
            pass
   
   
    def PrimeSetOnNow(self):
        self.log('PrimeSetOnNow')   
        try:
            if self.SetOnNowTimer.isAlive():
                self.SetOnNowTimer.cancel()
        except:
            pass
            
        self.SetOnNowTimer = threading.Timer(15.0, self.setOnNow)
        self.SetOnNowTimer.name = "SetOnNowTimer"
        self.SetOnNowTimer.start()
   
   
    def setOnNow(self):
        self.log('setOnNow')   
        self.OnNowTitleLst = []        
        self.OnNowArtLst = []
        curtime = time.time()
        ChannelChk = 0 
        
        try:
            if self.SetOnNowTimer.isAlive():
                self.SetOnNowTimer.cancel()
        except:
            pass
            
        for Channel in range(999):
            try:
                try:
                    try:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(Channel + 1) + '_type'))
                    except:
                        chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(Channel + 1) + '_type'))
                        pass

                    timedif = (curtime - self.channels[Channel].lastAccessTime)
                    ChannelChk = int(self.channels[Channel].getCurrentDuration())
                
                    if ChannelChk == 0:
                        self.log('setOnNow, channel ' + str(Channel + 1) + ' no playlist')
                        raise
                        
                    #same logic as in setchannel; loop till we get the current show
                    if chtype == 8 and len(self.channels[Channel].getItemtimestamp(0)) > 0:
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
                    else:
                        position = self.channels[Channel].playlistPosition
                                
                    label = self.channels[Channel].getItemTitle(position)  

                    if not label:
                        self.log('setOnNow, no label')
                        raise
                        
                    mediapath = (self.channels[Channel].getItemFilename(position))
                    myLiveID = self.channels[Channel].getItemLiveID(position)
                    ChanColor = (self.channelbugcolor).replace('0x','')
                    if self.isChanFavorite(Channel+1):
                        ChanColor = 'gold'
                    title = ("[COLOR=%s][B]%d|[/B][/COLOR] %s" % (ChanColor, Channel+1, label))
                    self.OnNowTitleLst.append(title)  
                    chname = (self.channels[Channel].name)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    dbid = (self.channelList.unpackLiveID(myLiveID))[2]
                    mpath = self.GetMpath(mediapath)
                    Art = [title, type, chtype, chname, id, dbid, mpath, self.type1EXT]     
                    self.OnNowArtLst.append(Art)
                except:
                    raise
            except Exception,e: 
                pass  
        self.log('setOnNow return')     
                
 
    # set the channel, the proper show offset, and time offset
    def setChannel(self, channel, quickflip=False):
        self.log('setChannel ' + str(channel))
        self.seektime = 0
        
        if self.OnDemand == True:
            self.OnDemand = False
        
        try:
            if self.PlayerTimeoutThread.isAlive():
                self.PlayerTimeoutThread.cancel()
        except:
            pass

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
        self.background.setVisible(True)
        self.getControl(102).setVisible(False)
        self.getControl(120).setVisible(False)
        self.getControl(103).setImage('NA.png')
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
        except:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            pass
            
        # first of all, save playing state, time, and playlist offset for
        # the currently playing channel
        if self.Player.isPlaying():
            if chtype != 8 and chtype != 9:
                if channel != self.currentChannel:
                    self.channels[self.currentChannel - 1].setPaused(xbmc.getCondVisibility('Player.Paused'))

                    # Automatically pause in serial mode
                    if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE > 0:
                        self.channels[self.currentChannel - 1].setPaused(True)

                    self.channels[self.currentChannel - 1].setShowTime(self.Player.getTime())
                    self.channels[self.currentChannel - 1].setShowPosition(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition())
                    self.channels[self.currentChannel - 1].setAccessTime(time.time())
            else:
                self.channels[self.currentChannel - 1].setPaused(False)
                
        self.currentChannel = channel       
        # now load the proper channel playlist
        chname = (self.channels[self.currentChannel - 1].name)
        self.background.setLabel(('Loading: %s') % chname)
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
            if chtype == 8 and len(self.channels[self.currentChannel - 1].getItemtimestamp(0)) > 0:
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
            else:#loop for other channel types
                while self.channels[self.currentChannel - 1].showTimeOffset + timedif > self.channels[self.currentChannel - 1].getCurrentDuration():
                    timedif -= self.channels[self.currentChannel - 1].getCurrentDuration() - self.channels[self.currentChannel - 1].showTimeOffset
                    self.channels[self.currentChannel - 1].addShowPosition(1)
                    self.channels[self.currentChannel - 1].setShowTime(0)

     
        # First, check to see if the video is a strm
        if self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)[-4:].lower() == 'strm' or chtype >= 8:
            self.log("setChannel, Ignoring a stop because of a strm or chtype >= 8")
            self.Player.ignoreNextStop = True
            
        mediapath = self.channels[self.currentChannel - 1].getItemFilename(self.channels[self.currentChannel - 1].playlistPosition)
        
        if quickflip and self.maxChannels > 1:
            if mediapath[-4:].lower() == 'strm' or chtype == 15:
                return self.lastActionTrigger()
            
        if chname == 'PseudoCinema':
            self.Cinema_Mode = True
        else:
            self.Cinema_Mode = False
        try:
            plugchk = mediapath.split('/')[2]
        except:
            plugchk = mediapath
                  
        xbmc.sleep(self.channelDelay)
        
        # Mute the channel before changing
        self.log("setChannel, about to mute");
        if self.MUTE:
            xbmc.executebuiltin("Mute()");     
        
        if self.Player.ignoreNextStop == True:
            self.PlayerTimeout()
            
        self.log("playing selected file");           
        self.Player.playselected(self.channels[self.currentChannel - 1].playlistPosition)
        self.lastActionCount = 0
        title = self.channels[self.currentChannel - 1].getItemTitle(self.channels[self.currentChannel - 1].playlistPosition)
        setProperty("Playing.Title",title)
        self.background.setVisible(False)
        # set the time offset
        self.channels[self.currentChannel - 1].setAccessTime(curtime)
        
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live - Loading: %s"}, "id": 1}' % (chname))
        self.channelList.sendJSON(json_query)
            
        # set the show offset
        if self.channels[self.currentChannel - 1].isPaused:
            self.channels[self.currentChannel - 1].setPaused(False)
            
            try:
                self.Player.seekTime(self.channels[self.currentChannel - 1].showTimeOffset)

                if self.channels[self.currentChannel - 1].mode & MODE_ALWAYSPAUSE == 0:
                    self.Player.pause()

                    if self.waitForVideoPaused() == False:
                        xbmc.executebuiltin("Mute()");
                        return
            except:
                self.log('Exception during seek on paused channel', xbmc.LOGERROR)
        else:       
            if chtype != 8 and chtype != 9 and plugchk not in BYPASS_SEEK:
                self.log("Seeking")
                seektime1 = self.channels[self.currentChannel - 1].showTimeOffset + timedif + int((time.time() - curtime))
                seektime2 = self.channels[self.currentChannel - 1].showTimeOffset + timedif
                overtime = float((int(self.channels[self.currentChannel - 1].getItemDuration(self.channels[self.currentChannel - 1].playlistPosition))/10)*8)
                halftime = float((int(self.channels[self.currentChannel - 1].getItemDuration(self.channels[self.currentChannel - 1].playlistPosition))/2))
        
                if mediapath[-4:].lower() == 'strm' or mediapath[0:6] == 'plugin':
                    self.seektime = self.SmartSeek(mediapath, seektime1, seektime2, overtime)
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
        
                if self.seektime >= halftime: 
                    self.ShowStartover()

        # Unmute
        self.log("Finished, unmuting");
        if self.MUTE:
            xbmc.executebuiltin("Mute()");
                
        self.showChannelLabel(self.currentChannel)
        self.lastActionTime = time.time()
        self.runActions(RULES_ACTION_OVERLAY_SET_CHANNEL_END, channel, self.channels[channel - 1])
        
        if self.UPNP:
            self.PlayUPNP(mediapath, self.seektime)

        self.PrimeSetOnNow()
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
                seektime = 0
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
                    seektime = 0
                    
        if seektime == 0 and DEBUG == 'true':
            self.log('seektime' + str(seektime))
            self.log('overtime' + str(overtime))
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "DEBUGGING: Overriding Seektime", 1000, THUMB) )
        return seektime    

        
    def PlayUPNP(self, file, seektime):
        self.log("PlayUPNP")
        #UPNP
        print file, seektime
        # if seektime == 0.0:
            # seektime = 0
        # print file, seektime
        file = file.replace("\\\\","\\")
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                self.log('UPNP1 Sharing')
                self.Upnp.SendUPNP(IPP1, file, seektime)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                self.log('UPNP2 Sharing')
                self.Upnp.SendUPNP(IPP2, file, seektime)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                self.log('UPNP3 Sharing')
                self.Upnp.SendUPNP(IPP3, file, seektime)
        except:
            pass 

            
    def StopUPNP(self):
        self.log("StopUPNP")
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                self.Upnp.StopUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                self.Upnp.StopUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                self.Upnp.StopUPNP(IPP3)
        except:
            pass
        
                    
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
            
        if self.OnDemand == True:
            position = -999
            mediapath = self.Player.getPlayingFile()
            
        elif self.hideShortItems and self.infoOffset != 0:
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
        else:
            #same logic as in setchannel; loop till we get the current show
            if chtype == 8 and len(self.channels[self.currentChannel - 1].getItemtimestamp(0)) > 0:
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
        self.SetMediaInfo(chtype, chname, mediapath, position)
        
        
    def SetMediaInfo(self, chtype, chname, mediapath, position, tmpstr=None):
        self.log('SetMediaInfo')  
        mpath = self.GetMpath(mediapath)        
        #OnDemand Set Player info, else Playlist
        if position == -999:
            if tmpstr != None:
                tmpstr = tmpstr.split('//')
                title = tmpstr[0]
                SEtitle = ('[COLOR=%s][B]OnDemand[/B][/COLOR]' % ((self.channelbugcolor).replace('0x','')))
                Description = tmpstr[2]
                genre = tmpstr[3]
                LiveID = self.channelList.unpackLiveID(tmpstr[5])
                self.getControl(506).setImage(IMAGES_LOC + 'ondemand.png')
                try:
                    self.getControl(508).setImage(IMAGES_LOC + 'ondemand.png')
                    self.getControl(510).setImage(IMAGES_LOC + 'ondemand.png')
                except:
                    pass
            else:
                try:
                    if self.GetPlayingTmpstrTimer.isAlive():
                        self.GetPlayingTmpstrTimer.cancel()
                except:
                    pass
                data = [chtype, chname, mediapath, position]
                self.GetPlayingTmpstrTimer = threading.Timer(1.0, self.GetPlayingTmpstrThread, [data])
                self.GetPlayingTmpstrTimer.name = "GetPlayingTmpstrTimer"  
                self.GetPlayingTmpstrTimer.start()  
                return
        else:
            title = (self.channels[self.currentChannel - 1].getItemTitle(position))
            SEtitle = self.channels[self.currentChannel - 1].getItemEpisodeTitle(position)
            Description = (self.channels[self.currentChannel - 1].getItemDescription(position))
            genre = (self.channels[self.currentChannel - 1].getItemgenre(position))
            LiveID = (self.channels[self.currentChannel - 1].getItemLiveID(position))
            LiveID = self.channelList.unpackLiveID(LiveID)
            self.getControl(506).setImage(self.channelLogos + (self.channels[self.currentChannel - 1].name) + '.png') 
            
        try:
            SEinfo = SEtitle.split(' -')[0]
            season = int(SEinfo.split('x')[0])
            episode = int(SEinfo.split('x')[1])
        except:
            season = 0
            episode = 0  
            
        setProperty("Playing.Season",str(season))
        setProperty("Playing.Episode",str(episode)) 
            
        try:
            if self.showSeasonEpisode and season != 0 and episode != 0:
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
        setProperty("Playing.Chtype",str(chtype))
        setProperty("Playing.Mpath",mpath)
        setProperty("Playing.Mediapath",mediapath)
        setProperty("Playing.Chname",chname)
        setProperty("Playing.SEtitle",SEtitle)
        setProperty("Playing.Type",type)
        setProperty("Playing.DBID",dbid)
        setProperty("Playing.ID",id)
        setProperty("Playing.Type",type)
        setProperty("Playing.Description",Description)
        
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
        except:
            self.log('setShowInfo, Label 508 not found')
            pass
           
        #Dynamic Art2
        try:
            self.setArtwork2(type, chtype, chname, id, dbid, mpath, self.type2EXT)
        except:
            self.log('setShowInfo, Label 510 not found')
            pass
            
            
    def FindArtwork_Thread(self, data):
        self.log('FindArtwork_Thread, key = ' + str(data[7]))
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
            self.ArtThread1 = threading.Timer(0.1, self.FindArtwork_Thread, [data])
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
            self.ArtThread2 = threading.Timer(0.1, self.FindArtwork_Thread, [data])
            self.ArtThread2.name = "ArtThread2"
            self.ArtThread2.start()
        except Exception,e:
            self.log('setArtwork2, Failed!', str(e))
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
            self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)

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

        if self.infoOnChange == True:
            self.infoOffset = 0
            self.showInfo(self.InfTimer)
        else:
            self.setShowInfo()

        if xbmc.getCondVisibility('Player.ShowInfo'):
            json_query = '{"jsonrpc": "2.0", "method": "Input.Info", "id": 1}'
            self.ignoreInfoAction = True
            self.channelList.sendJSON(json_query);
            
        try:
            setImage = 'NA.png'
            if self.showChannelBug == True:
                if int(chtype) != 8:
                    self.getControl(103).setImage(self.Artdownloader.FindBug(chtype, chname))
        except:
            pass
                
        # Channel name label #      
        self.getControl(300).setLabel(self.channels[self.currentChannel - 1].name)
        self.channelLabelTimer.name = "ChannelLabel"
        
        if self.channelLabelTimer.isAlive():
            self.channelLabelTimer.cancel()
            self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
            self.channelLabelTimer.start()
        else:
            self.channelLabelTimer.start()
            
        self.startNotificationTimer(10.0)
        self.log('showChannelLabel return')

        
    def OnDemandAction(self, type='OnDemand'):
        self.log('OnDemandAction')        
        if type == 'Now Playing' or type == 'MoreInfo':        
            if getProperty("Playing.Type") == 'tvshow':
            
                if type == 'MoreInfo' and getProperty("Playing.Season") != '0' and getProperty("Playing.Episode") != '0':
                    info = 'seasoninfo'
                    dbtype = 'tvdb_id'
                    title = 'tvshow'
                else:
                    info = 'extendedtvinfo'
                    dbtype = 'tvdb_id'
                    title = 'name'                    
            else:
                info = 'extendedinfo'
                dbtype = 'imdb_id'
                title = 'name'  
            
            print info
            xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,%s=%s,%s=%s,season=%s)" % (info, getProperty("Playing.DBID"), title, getProperty("Playing.Title"), dbtype, getProperty("Playing.ID"), getProperty("Playing.Season")))
        
        elif type == 'Search':
            json_query = ('{"jsonrpc":"2.0","method":"Player.PlayPause","params":{"playerid":1}, "id": 1}')
            self.channelList.sendJSON(json_query)
            xbmc.executebuiltin("XBMC.RunScript(script.globalsearch)")

        else:
            xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo)")
            # json_query = ('{"jsonrpc":"2.0","method":"Player.PlayPause","params":{"playerid":1}, "id": 1}')
            # self.channelList.sendJSON(json_query)
            # # self.Paused()
            # self.hideInfo()
            # extTypes = ['.avi', '.flv', '.mkv', '.mp4', '.strm', '.ts']
            # self.Browse = dlg.browse(1,'OnDemand', 'video', '.avi|.flv|.mkv|.mp4|.strm|.ts', True, True, 'special://videoplaylists')
            # if (self.Browse)[-4:].lower() in extTypes:
                # self.log("onClick, OnDemand = " + self.Browse)
                # self.OnDemand = True
                # self.getControl(103).setImage(IMAGES_LOC + 'Default_ondemand.png')
                # self.Player.play(self.Browse)
                # # self.Resume()
                # self.showInfo(self.InfTimer)
            # else:
                # json_query = ('{"jsonrpc":"2.0","method":"Player.PlayPause","params":{"playerid":1}, "id": 1}')
                # self.channelList.sendJSON(json_query)
                # # self.Resume()
                # self.MenuControl('Menu',self.InfTimer)
        

    # Called from the timer to hide the channel label.
    def hideChannelLabel(self):
        self.log('hideChannelLabel')
        self.channelLabelTimer = threading.Timer(2.0, self.hideChannelLabel)
        try:
            if self.GotoChannelTimer.isAlive():
                self.GotoChannelTimer.cancel()
        except:
            pass 
        for i in range(3):
            try:
                self.channelLabel[i].setVisible(False)
            except:
                pass
        if self.DirectInput == True:
            inputChannel = self.inputChannel
            self.GotoChannelTimer = threading.Timer(2.1, self.setChannel, [inputChannel])
            self.GotoChannelTimer.start()
        self.inputChannel = -1

        
    def hideInfo(self):
        self.log('hideInfo')
        try:
            self.showingInfo = False 
            self.getControl(102).setVisible(False)
            self.showingStartover = False  
            self.getControl(104).setVisible(False)
            self.infoOffset = 0

            if self.infoTimer.isAlive():
                self.infoTimer.cancel()
                
            self.infoTimer = threading.Timer(self.InfTimer, self.hideInfo)
            xbmc.sleep(10)
        except:
            pass
                          
        
    def ShowStartover(self):
        self.log('ShowStartover')
        self.getControl(104).setVisible(True)
        self.showingStartover = True   
        
              
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
                    
                if chtype <= 7 and self.channels[self.currentChannel - 1].getItemDuration(xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()) < self.shortItemLength:
                    return
                    
            self.showingInfo = True
            self.getControl(102).setVisible(True)
            self.setShowInfo()
            
            if self.DisableOverlay == True:
                return

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


    def showMenu(self):
        self.log("showMenu")
        try:
            #Set button labels n logo
            self.getControl(1000).setLabel('Now Watching')
            self.getControl(1001).setLabel('OnNow')
            self.getControl(1002).setLabel(self.chkChanFavorite())
            self.getControl(1003).setLabel('Last Channel')
            self.getControl(1004).setLabel('EPGType')
            self.getControl(1005).setLabel('Record')
            self.getControl(1006).setLabel('Search')
            self.getControl(1007).setLabel('Mute')
            self.getControl(1008).setLabel('Subtitle')
            self.getControl(1009).setLabel('Player Settings')
            self.getControl(1010).setLabel('Sleep')
            self.getControl(1011).setLabel('Exit')

            if not self.showingMenu:    
                #Set first button focus, show menu
                self.showingMenu = True
                self.getControl(119).setVisible(True)
                xbmc.sleep(100) 
                self.setFocusId(1001) 
                
            self.MenuControlTimer = threading.Timer(self.InfTimer, self.MenuControl,['Menu',self.InfTimer,True])           
            self.MenuControlTimer.name = "MenuControlTimer"  
            self.MenuControlTimer.start() 
        except:
            pass

            
    def ShowMenuAlt(self):
        self.log("ShowMenuAlt")
        try:
            if not self.showingMenuAlt:
                show_busy_dialog()
                curchannel = 0
                self.showingMenuAlt = True
                
                if len(self.OnNowTitleLst) == 0:
                    self.setOnNow()
                    
                sidex, sidey = self.getControl(132).getPosition()
                sidew = self.getControl(132).getWidth()
                sideh = self.getControl(132).getHeight()
                listWidth = self.getControl(132).getLabel()
                tabHeight = self.getControl(1001).getHeight()
                self.list = xbmcgui.ControlList(sidex, sidey, sidew, sideh, 'font12', self.myEPG.textcolor, MEDIA_LOC + BUTTON_NO_FOCUS, MEDIA_LOC + BUTTON_FOCUS, self.myEPG.focusedcolor, 1, 1, 1, 0, tabHeight, 0, tabHeight/2)
                self.addControl(self.list)
                self.list.addItems(items=self.OnNowTitleLst)
                self.getControl(131).setImage('NA.png')
                
                for i in range(len(self.OnNowTitleLst)):
                    item = self.OnNowTitleLst[i]
                    title = (item.split('|')[1]).replace('[/B][/COLOR] ','')
                    if title.lower() == getProperty("Playing.Title").lower():
                        break
                    
                self.list.selectItem(i)
                self.getControl(130).setVisible(True)
                self.list.setVisible(True)
                hide_busy_dialog()
                xbmc.sleep(100)
                self.setFocus(self.list)
                self.setOnNowArt()
                self.MenuControlTimer = threading.Timer(self.InfTimer, self.MenuControl,['MenuAlt',self.InfTimer,True])           
                self.MenuControlTimer.name = "MenuControlTimer"  
                self.MenuControlTimer.start() 
        except Exception,e:
            self.log("ShowMenuAlt, Failed! " + str(e))


    def ShowMoreInfo(self):
        self.log('ShowMoreInfo')
        try:
            self.getControl(1012).setLabel('More Info')
            self.getControl(1013).setLabel('Find Similar')
            self.getControl(1014).setLabel('Record Show')
            self.getControl(1015).setLabel('Set Reminder')
            
            if not self.showingMoreInfo:
                self.hideInfo()
                self.showingMoreInfo = True   
                self.getControl(222).setVisible(True) 
                xbmc.sleep(100) 
                self.setFocusId(1012)
                
            self.MenuControlTimer = threading.Timer(self.InfTimer, self.MenuControl,['MoreInfo',self.InfTimer,True])           
            self.MenuControlTimer.name = "MenuControlTimer"  
            self.MenuControlTimer.start() 
        except:
            pass

            
    def hidePOP(self):
        self.log("hidePOP")
        try:
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
                    
            if self.DisableOverlay == True:
                return
                
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
        IdleSeconds = 180 #3min
        PausedPlayback = bool(xbmc.getCondVisibility("Player.Paused"))
        ActivePlayback = bool(xbmc.Player().isPlaying())
        xbmcIdle = int(xbmc.getGlobalIdleTime())
        showingEPG = getProperty("PTVL.EPG_Opened") == "true"
        
        if showingEPG or PausedPlayback:
            idling = True 
        else: 
            idling = False 
            
        if xbmcIdle >= IdleSeconds and idling == True:
                if getProperty("PTVL.Idle_Opened") != "true":
                    self.log("IdleTimer, Starting Idle ScreenSaver")                      
                    xbmc.executebuiltin('XBMC.RunScript(' + ADDON_PATH + '/resources/lib/idle.py)')
        self.logDebug("IdleTimer, XBMCidle = " + str(xbmcIdle) + ", IdleSeconds = " + str(IdleSeconds) + ', PausedPlayback = ' + str(PausedPlayback) + ', showingEPG = ' + str(showingEPG) + ', ActivePlayback = ' + str(ActivePlayback))
          
          
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
        
        if getProperty("Playing.Type") == 'tvshow':
            print getProperty("Playing.Season"), getProperty("Playing.Episode")
            if getProperty("Playing.Season") != '0' and getProperty("Playing.Episode") != '0':
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
        
        if controlId == 1000:
            if self.showingMenu:
                self.log("Now Playing")
                self.OnDemandAction('Now Playing')

        elif controlId == 1001:
            if self.showingMenu:
                self.log("OnNow")
                self.MenuControl('MenuAlt',self.InfTimer)
                
        elif controlId == 1002:
            if self.showingMenu:
                self.log("ChannelFavorite")
                if self.getControl(1002).getLabel() == 'Remove Favorite':
                    MSG = "Channel %s removed from favourites" % str(self.currentChannel)
                    self.FavChanLst = removeStringElem(self.FavChanLst, str(self.currentChannel))
                else:
                    MSG = "Channel %s added to favourites" % str(self.currentChannel)
                    self.FavChanLst.append(str(self.currentChannel))
                infoDialog(MSG)
                self.FavChanLst = removeEmptyElem(self.FavChanLst)
                self.FavChanLst = sorted_nicely(self.FavChanLst)
                newFavChanLst = (','.join(self.FavChanLst))
                REAL_SETTINGS.setSetting("FavChanLst",newFavChanLst)
                
        elif controlId == 1003:
            if self.showingMenu:
                self.log("LastChannel")
                self.LastChannelJump()
                self.setChannel(self.LastChannel)
                self.MenuControl('Menu',self.InfTimer,True) 
                
        elif controlId == 1004:
            if self.showingMenu:
                self.log("EPGType")
                self.EPGtypeToggle()
                self.MenuControl('Menu',self.InfTimer)
                   
        elif controlId == 1005:
            if self.showingMenu:
                self.log("Record")
                Comingsoon()
                
        elif controlId == 1006:
            if self.showingMenu:
                self.log("Search")
                self.OnDemandAction('Search')
                            
        elif controlId == 1007:
            if self.showingMenu:
                self.log("Mute")
                xbmc.executebuiltin("Mute()");
                self.MenuControl('Menu',self.InfTimer)
                
        elif controlId == 1008:
            if self.showingMenu:
                self.log("Subtitle")
                # xbmc.executebuiltin("ActivateWindow(10153)")
                xbmc.executebuiltin("ActivateWindow(SubtitleSearch)")
                self.MenuControl('Menu',self.InfTimer)
                
        elif controlId == 1009:
            if self.showingMenu:
                self.log("VideoMenu")
                xbmc.executebuiltin("ActivateWindow(12901)")
                xbmc.sleep(100)
                self.MenuControl('Menu',self.InfTimer,True)
                    
        elif controlId == 1010:
            if self.showingMenu:
                self.log("Sleep")
                self.SleepButton()    
                self.MenuControl('Menu',self.InfTimer)       
                
        elif controlId == 1011:
            if self.showingMenu:
                self.log("Exit")
                if dlg.yesno("Exit?", "Are you sure you want to exit PseudoTV Live?"):
                    self.MenuControl('Menu',self.InfTimer,True)
                    self.end()
                else:
                    self.MenuControl('Menu',self.InfTimer)
                    
        elif controlId == 1012:
            if self.showingMoreInfo:
                self.log("MoreInfo")
                if info == 'seasoninfo':
                    xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,%s=%s,%s=%s,season=%s)" % (info, getProperty("Playing.DBID"), title, getProperty("Playing.Title"), dbtype, getProperty("Playing.ID"), getProperty("Playing.Season")))
                else:
                    xbmc.executebuiltin("XBMC.RunScript(script.extendedinfo,info=%s,dbid=%s,%s=%s,%s=%s)" % (info, getProperty("Playing.DBID"), title, getProperty("Playing.Title"), dbtype, getProperty("Playing.ID")))
            
        elif controlId == 1013:
            if self.showingMoreInfo:
                self.log("Similar")
                Comingsoon()
                    
        elif controlId == 1014:
            if self.showingMoreInfo:
                self.log("Record Show")
                Comingsoon()
                    
        elif controlId == 1015:
            if self.showingMoreInfo:
                self.log("Set Reminder")
                Comingsoon()     
            
        self.actionSemaphore.release()
        self.log('onClick return')
    
    
    def onControl(self, controlId):
        self.log('onControl ' + str(controlId))
        pass

        
    # Handle all input while videos are playing
    def onAction(self, act):
        action = act.getId()
        self.log('onAction ' + str(action))
        self.OnAction = True
        
        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
        except:
            # Threading issue? chtype fails to load proper chtype
            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(self.currentChannel) + '_type'))
            except:
                chtype = 0
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
            self.log('Unable player is stopped')
            return

        # Since onAction isnt always called from the same thread (weird),
        # ignore all actions if we're in the middle of processing one
        if self.actionSemaphore.acquire(False) == False:
            self.log('Unable to get semaphore')
            return
            
        lastaction = time.time() - self.lastActionTime

        # during certain times we just want to discard all input
        if lastaction < 2 and self.showingStartover == False:
            self.log('Not allowing actions')
            action = ACTION_INVALID

        self.startSleepTimer()

        if action == ACTION_SELECT_ITEM:
            if self.showingStartover:
                self.log('showingStartover, Starting Over')
                xbmc.executebuiltin("action(SkipPrevious)")
                self.hideInfo()
            elif self.showingMenuAlt:
                self.MenuControl('MenuAlt',self.InfTimer,True)
                try:
                    item = self.list.getSelectedItem()
                    channel = (((item.getLabel()).split('|')[0]).replace('[B]',''))
                    channel = re.sub('\[COLOR=(.+?)\]', '', channel)
                    self.setChannel(int(channel))
                except:
                    pass
            elif not self.showingMenu and not self.showingMoreInfo:
                # If we're manually typing the channel, set it now
                if self.inputChannel > 0:
                    if self.inputChannel != self.currentChannel and self.inputChannel <= self.maxChannels:
                        self.setChannel(self.inputChannel)
                    self.inputChannel = -1
                else:
                    # Otherwise, show the EPG
                    if self.channelThread.isAlive():
                        self.channelThread.pause()

                    if self.notificationTimer.isAlive():
                        self.notificationTimer.cancel()
                        self.notificationTimer = threading.Timer(NOTIFICATION_CHECK_TIME, self.notificationAction)

                    # Auto-off reset after EPG activity.
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
            elif self.showingMoreInfo:
                self.MenuControl('MoreInfo',self.InfTimer)
            elif self.showingMenu:
                self.MenuControl('Menu',self.InfTimer)
            elif not self.showingMoreInfo:
                self.channelUp()
                
        elif action == ACTION_MOVE_DOWN or action == ACTION_PAGEDOWN:
            if self.showingMenuAlt:
                self.setOnNowArt()
            elif self.showingMoreInfo:
                self.MenuControl('MoreInfo',self.InfTimer)
            elif self.showingMenu:
                self.MenuControl('Menu',self.InfTimer)
            elif not self.showingMoreInfo:
                self.channelDown()

        elif action == ACTION_MOVE_LEFT:   
            self.log("ACTION_MOVE_LEFT")
            print self.showingMenuAlt, self.showingMenu, self.showingInfo, self.infoOffset, self.showingStartover
            if self.showingMenuAlt == True:
                self.MenuControl('MenuAlt',self.InfTimer,True)
            elif self.showingMenu == True:
                self.MenuControl('Menu',self.InfTimer,True)
            elif self.showingInfo == True:
                self.infoOffset -= 1
                if self.infoOffset <= 0:
                    self.MenuControl('Menu',self.InfTimer)
                elif not self.showingMenu:
                    self.showInfo(self.InfTimer)
            elif self.showingInfo == False and chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                xbmc.executebuiltin("ActivateWindow(10115)")
                xbmc.executebuiltin("PlayerControl(SmallSkipBackward)")
                self.log("SmallSkipBackward")
                
                try:
                    if REAL_SETTINGS.getSetting("UPNP1") == "true":
                        self.log('UPNP1 RW')
                        self.Upnp.RWUPNP(IPP1)
                    if REAL_SETTINGS.getSetting("UPNP2") == "true":
                        self.log('UPNP2 RW')
                        self.Upnp.RWUPNP(IPP2)
                    if REAL_SETTINGS.getSetting("UPNP3") == "true":
                        self.log('UPNP3 RW')
                        self.Upnp.RWUPNP(IPP3)
                except:
                    pass
                    
        elif action == ACTION_MOVE_RIGHT:
            self.log("ACTION_MOVE_RIGHT")
            if self.showingMenuAlt:
                self.MenuControl('MenuAlt',self.InfTimer,True)
            elif self.showingMenu:
                self.MenuControl('Menu',self.InfTimer,True)
            elif self.showingInfo:
                self.infoOffset += 1
                self.showInfo(self.InfTimer)
                
            elif chtype != 8 and chtype != 9 and mediapath[0:4] != 'rtmp' and mediapath[0:4] != 'rtsp' and plugchk not in BYPASS_SEEK:
                xbmc.executebuiltin("ActivateWindow(10115)")
                xbmc.executebuiltin("PlayerControl(SmallSkipForward)")
                self.log("SmallSkipForward")
        
                try:
                    if REAL_SETTINGS.getSetting("UPNP1") == "true":
                        self.log('UPNP1 FF')
                        self.Upnp.FFUPNP(IPP1)
                    if REAL_SETTINGS.getSetting("UPNP2") == "true":
                        self.log('UPNP2 FF')
                        self.Upnp.FFUPNP(IPP2)
                    if REAL_SETTINGS.getSetting("UPNP3") == "true":
                        self.log('UPNP3 FF')
                        self.Upnp.FFUPNP(IPP3)
                except:
                    pass
                    
        elif action in ACTION_PREVIOUS_MENU:
            if self.showingMenuAlt:
                self.MenuControl('MenuAlt',self.InfTimer,True)
            elif self.showingMoreInfo:
                self.MenuControl('MoreInfo',self.InfTimer,True)
            elif self.showingMenu:
                self.MenuControl('Menu',self.InfTimer,True)
            elif self.showingInfo:
                self.hideInfo()
            else:        
                dlg = xbmcgui.Dialog()
                
                # Auto-off reset after MENU activity.
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
        
        elif action == ACTION_SHIFT: #Last channel button
            self.log('ACTION_SHIFT')
            self.LastChannelJump()
            self.setChannel(self.LastChannel)

        elif action == ACTION_SYMBOLS:
            self.log('ACTION_SYMBOLS')
            self.setChannel(self.Jump2Favorite())
            
        elif action == ACTION_CURSOR_LEFT:
            self.log('ACTION_CURSOR_LEFT')
            
        elif action == ACTION_CURSOR_RIGHT:
            self.log('ACTION_CURSOR_RIGHT')

        elif action == ACTION_CONTEXT_MENU:
            self.log('ACTION_CONTEXT_MENU')
            if not self.showingMoreInfo:
                self.MenuControl('MoreInfo',self.InfTimer)
            elif self.showingMoreInfo:
                self.MenuControl('MoreInfo',self.InfTimer,True)

        self.actionSemaphore.release()
        self.OnAction = False
        self.log('onAction return')


    # Reset the sleep timer
    def startSleepTimer(self):
        try:
            if self.sleepTimeValue == 0:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
                return
            else:
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
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Quit(),%d,false)" % ( 5.0, ) )
            self.end()
        elif self.sleepTimeMode == 2:
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Suspend(),%d,false)" % ( 5.0, ) )
            self.end()
        elif self.sleepTimeMode == 3:
            xbmc.executebuiltin( "XBMC.AlarmClock(shutdowntimer,XBMC.Powerdown(),%d,false)" % ( 5.0, ) )
            self.end()
        elif self.sleepTimeMode == 4:
            json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live - Sleeping"}, "id": 1}')
            self.channelList.sendJSON(json_query)

            
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
                          
                    ShowTitle = self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', '')
                    myLiveID = self.channels[self.currentChannel - 1].getItemLiveID(nextshow)
                    type = (self.channelList.unpackLiveID(myLiveID))[0]
                    id = (self.channelList.unpackLiveID(myLiveID))[1]
                    dbid = (self.channelList.unpackLiveID(myLiveID))[2]
                    mpath = self.GetMpath(mediapath)
                    
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
                            self.getControl(124).setLabel(ShowTitle)
                            self.getControl(125).setLabel(ShowEpisode)
                        except:
                            #No Overlay Popup code in skin, default to Cassic Popup
                            ClassicPOPUP = True
                            pass

                    # Execute notification
                    if self.showNextItem == True:
                        # Classic/Popup note
                        if REAL_SETTINGS.getSetting("EnableComingUp") != "1":
                            self.log('notification, Classic/Popup')
                            
                            if getProperty("EnableArtwork") == "false":
                                NotifyTHUMB = self.Artdownloader.SetDefaultArt_NEW(chname, mpath, self.type3EXT)
                            else:
                                NotifyTHUMB = self.Artdownloader.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, self.type3EXT)
                                if FileAccess.exists(NotifyTHUMB) == False:
                                    NotifyTHUMB = self.Artdownloader.SetDefaultArt_NEW(chname, mpath, self.type3EXT)
                                                                            
                            if self.showingInfo == False and self.notificationShowedNotif == False:
                                if REAL_SETTINGS.getSetting("EnableComingUp") == "3" or ClassicPOPUP == True:
                                    xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (title, self.channels[self.currentChannel - 1].getItemTitle(nextshow).replace(',', ''), str(NOTIFICATION_DISPLAY_TIME * 2000), NotifyTHUMB))
                                else:
                                    self.getControl(122).setImage(NotifyTHUMB)
                                    self.showPOP(self.InfTimer + 2.5)
                                self.notificationShowedNotif = True
                            self.log("notification.plugin.NotifyTHUMB = " + NotifyTHUMB) 

                        # Overlay note
                        else:
                            self.log('notification, Overlay') 
                            self.infoOffset = ((nextshow) - self.notificationLastShow)
                            self.log('snotification, Overlay infoOffset = ' + str(self.infoOffset))
                            self.showInfo(self.InfTimer + 2.5)
                            self.notificationShowedNotif = True
                        
        self.startNotificationTimer()

        
    def PlayerTimeout(self, start_time=-1):
        self.log("PlayerTimeout, ActionTimeInt = " + str(self.ActionTimeInt))    
        # cancel pending action
        STOP = False
        try:
            if self.PlayerTimeoutThread.isAlive():
                self.PlayerTimeoutThread.cancel()
        except:
            pass 
        try:
            get_time = int(self.Player.getTime())
        except:
            get_time = 0
            
        if start_time == -9:
            self.log("PlayerTimeout, Force Stop")
            STOP = True
        elif start_time == -1:
            self.log("PlayerTimeout, Start Timer")
            self.PlayerTimeoutThread = threading.Timer(self.ActionTimeInt, self.PlayerTimeout, [get_time])
            self.PlayerTimeoutThread.name = "PlayerTimeoutThread"
            self.PlayerTimeoutThread.start() 
        else:
            self.log("PlayerTimeout, get_time = " + str(get_time) + ", start_time = " + str(start_time))
            if get_time == start_time: 
                self.background.setLabel('Playback Timed out')
                STOP = True
        if STOP:
            self.log("PlayerTimeout, Playback Failed: STOPPING!")
            json_query = '{"jsonrpc":"2.0","method":"Input.ExecuteAction","params":{"action":"stop"},"id":1}'
            self.channelList.sendJSON(json_query);
            # self.notPlayingCount = ((int(self.ActionTimeInt))/3) + 1
            # self.playerTimerAction()
            # if DEBUG == 'true':
                # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "DEBUGGING: PlayerTimeout Stopped!", 1000, THUMB) )
                    
                    
    def playerTimerAction(self):
        self.log("playerTimerAction")
        self.playerTimer = threading.Timer(2.0, self.playerTimerAction)  

        if self.Player.isPlaying():
            self.lastPlayTime = int(self.Player.getTime())
            self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()    
            self.notPlayingCount = 0    
            self.background.setVisible(False)
            MSG = ''           
        else:          
            self.notPlayingCount += 1
            self.log("Adding to notPlayingCount, " + str(self.notPlayingCount))
            
            if self.notPlayingCount > 1:
                try:
                    self.background.setVisible(True)
                except:
                    pass
                MSG = (("Playback Failed - %d / %d") % (self.notPlayingCount, ((int(self.ActionTimeInt))/3)))
                self.background.setLabel(MSG)
        
            if self.notPlayingCount > (int(self.ActionTimeInt))/3:
                self.lastActionTrigger()
                self.showChannelLabel(self.currentChannel)
                self.playerTimer.name = "PlayerTimer"
                self.playerTimer.start()
                return
    
        if self.Player.stopped == False:
            self.playerTimer.name = "PlayerTimer"
            self.playerTimer.start()
        
        # Check idle
        if REAL_SETTINGS.getSetting("Idle_Screensaver") == "true":
            self.IdleTimer()

            
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
    
    
    def Paused(self, action=False):
        self.log('Paused')
        self.background.setLabel('Paused')
        
        if action and self.Player.isPlaying():
            json_query = ('{"jsonrpc":"2.0","method":"Player.PlayPause","params":{"playerid":1}, "id": 1}')
            self.channelList.sendJSON(json_query)
            
        if REAL_SETTINGS.getSetting("UPNP1") == "true":
            self.Upnp.PauseUPNP(IPP1)
        if REAL_SETTINGS.getSetting("UPNP2") == "true":
            self.Upnp.PauseUPNP(IPP2)
        if REAL_SETTINGS.getSetting("UPNP3") == "true":
            self.Upnp.PauseUPNP(IPP3)
    
    
    def Resume(self, action=False):
        self.log('Resume')
        self.showInfo(self.InfTimer)
        
        if action and self.Player.is_playback_paused():
            json_query = ('{"jsonrpc":"2.0","method":"Player.PlayPause","params":{"playerid":1}, "id": 1}')
            self.channelList.sendJSON(json_query)
            
        try:
            if REAL_SETTINGS.getSetting("UPNP1") == "true":
                self.Upnp.ResumeUPNP(IPP1)
            if REAL_SETTINGS.getSetting("UPNP2") == "true":
                self.Upnp.ResumeUPNP(IPP2)
            if REAL_SETTINGS.getSetting("UPNP3") == "true":
                self.Upnp.ResumeUPNP(IPP3)
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
    
    
    def lastActionTrigger(self):
        self.log('lastActionTrigger') 
        self.lastActionCount += 1
        if self.lastActionCount > 10:
            return
        elif self.notPlayingAction == 'Down':
            self.background.setLabel("Changing Channel Down")
            self.channelDown()
        elif self.notPlayingAction == 'Last':
            self.background.setLabel("Returning to Previous Channel")
            self.LastChannelJump()
            self.setChannel(self.LastChannel)
        else:
            self.background.setLabel("Changing Channel Up")
            self.channelUp()
              

    # set ShowReminder(self, time, cleanTime, title, channel):
        # self.log('SetAutoJump') 
    
   
    def SetAutoJump(self, time, cleanTime, title, channel):
        self.log('SetAutoJump') 
        try:
            if self.AutoJumpThread.isAlive():
                self.AutoJumpThread.cancel()
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
    
    
    # def KillAutoJump(self):
        # xbmc.executebuiltin("Dialog.Close(PseudoTV Live)")
    
    
    def GetPlayingTmpstrThread(self, data):
        self.log('GetPlayingTmpstrThread') 
        json_query = ('{"jsonrpc":"2.0","method":"Player.GetItem","params":{"playerid":1,"properties":["title","year","mpaa","imdbnumber","description","season","episode","playcount","genre","duration","runtime","showtitle","album","artist","plot","plotoutline","tagline","tvshowid"]}, "id": 1}')
        json_folder_detail = self.channelList.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        print file_detail
        fileList = []
        seasoneplist = []
        filecount = 0
        LiveID = 'other|0|0|False|1|NR|'
        
        for f in file_detail:
            tmpstr = ''
            istvshow = False
            Managed = False   
            try:
                dur = 0
                filecount += 1
                seasonval = -1
                epval = -1
                titles = re.search('"label" *: *"(.*?)",', f)
                showtitles = re.search('"showtitle" *: *"(.*?)",', f)
                plots = re.search('"plot" *: *"(.*?)",', f)
                plotoutlines = re.search('"plotoutline" *: *"(.*?)",', f)
                years = re.search('"year" *: *([\d.]*\d+)', f)
                genres = re.search('"genre" *: *\[(.*?)\],', f)
                playcounts = re.search('"playcount" *: *([\d.]*\d+),', f)
                imdbnumbers = re.search('"imdbnumber" *: *"(.*?)",', f)
                ratings = re.search('"mpaa" *: *"(.*?)",', f)
                descriptions = re.search('"description" *: *"(.*?)",', f)
                
                if showtitles != None and len(showtitles.group(1)) > 0:
                    type = 'tvshow'
                    dbids = re.search('"tvshowid" *: *(.*),', f)
                else:
                    type = 'movie'
                    dbids = re.search('"id" *: *: *(.*),', f)

                # if possible find year by title
                try:
                    year = int(years.group(1))
                except:
                    try:
                        if type == 'tvshow':
                            year = int(((showtitles.group(1)).split(' ('))[1].replace(')',''))
                        else:
                            year = int(((titles.group(1)).split(' ('))[1].replace(')',''))
                    except Exception,e:
                        print str(e)
                        year = 0
                        pass

                self.logDebug("GetPlayingTmpstr, year = " + str(year))  

                if genres != None and len(genres.group(1)) > 0:
                    genre = ((genres.group(1).split(',')[0]).replace('"',''))
                else:
                    genre = 'Unknown'
                                
                self.logDebug("GetPlayingTmpstr, genre = " + genre)  

                if playcounts != None and len(playcounts.group(1)) > 0:
                    playcount = int(playcounts.group(1))
                else:
                    playcount = 1
                        
                self.logDebug("GetPlayingTmpstr, playcount = " + str(playcount))  
        
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
                
                self.logDebug("GetPlayingTmpstr, rating = " + rating)  
                
                if imdbnumbers != None and len(imdbnumbers.group(1)) > 0:
                    imdbnumber = imdbnumbers.group(1)
                else:
                    imdbnumber = 0
                
                self.logDebug("GetPlayingTmpstr, imdbnumber = " + str(imdbnumber))
                            
                if dbids != None and len(dbids.group(1)) > 0:
                    dbid = int((dbids.group(1)).split(',')[0])
                else:
                    dbid = 0
                    
                self.logDebug("GetPlayingTmpstr, dbid = " + str(dbid))

                if plots != None and len(plots.group(1)) > 0:
                    theplot = (plots.group(1)).replace('\\','').replace('\n','')
                elif plotoutlines != None and len(plotoutlines.group(1)) > 0:
                    theplot = (plotoutlines.group(1)).replace('\\','').replace('\n','')
                elif descriptions != None and len(descriptions.group(1)) > 0:
                    theplot = (descriptions.group(1)).replace('\\','').replace('\n','')
                else:
                    theplot = (titles.group(1)).replace('\\','').replace('\n','')
                
                try:
                    theplot = (self.channelList.trim(theplot, 350, '...'))
                except Exception,e:
                    theplot = (theplot[:350])

                # This is a TV show
                if showtitles != None and len(showtitles.group(1)) > 0:
                    season = re.search('"season" *: *([0-9]*?),', f)
                    episode = re.search('"episode" *: *([0-9]*?),', f)
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
                        self.log("GetPlayingTmpstr, Enhanced TV GuideData Enabled")  
                        # try:
                            # showtitle = label.split(' (')[0]
                            # year = (label.split(' (')[1]).replace(')','')
                        # except:
                            # showtitle = label
                            # year = 0
                            # pass
                            
                        if year == 0:
                            year = self.channelList.getYear(type, showtitles.group(1))
                            
                        if imdbnumber == 0:
                            imdbnumber = self.channelList.getTVDBID(showtitles.group(1), year)                         

                        if genre == 'Unknown':
                            genre = self.channelList.getGenre(type, showtitles.group(1), year)
                            
                        if rating == 'NR':
                            rating = self.channelList.getRating(type, showtitles.group(1), year)

                        if imdbnumber != 0:
                            Managed = self.channelList.sbManaged(imdbnumber)
                    GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating] 
                    genre, LiveID = self.channelList.packGenreLiveID(GenreLiveID)
                    tmpstr += (showtitles.group(1)) + "//" + swtitle + "//" + theplot + "//" + genre + "////" + LiveID
                    istvshow = True
                else:                  
                    album = re.search('"album" *: *"(.*?)"', f)
                    # This is a movie
                    if not album or len(album.group(1)) == 0:
                    
                        label = titles.group(1)  
                        showtitle = label  
                        
                        if '(' in showtitle and year == 0:
                            try:
                                year = int(((showtitle.split('('))[1]).replace(')',''))
                            except:
                                pass
                                
                        taglines = re.search('"tagline" *: *"(.*?)"', f)
                        if taglines and len(taglines.group(1)) > 0:
                            tagline = (taglines.group(1)).replace('\\','')
                        else:
                            tagline = ''
                        
                        if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':    
                            self.log("GetPlayingTmpstr, Enhanced Movie GuideData Enabled")                                       
                            try:
                                label = showtitle.split(' (')[0]
                            except:
                                pass
                                
                            if year == 0:
                                year = self.channelList.getYear(type, label)
                                                
                            self.logDebug("GetPlayingTmpstr, label = " + label)
                                                            
                            if imdbnumber == 0:
                                imdbnumber = self.channelList.getIMDBIDmovie(label, year)
                                                            
                            if genre == 'Unknown':
                                genre = self.channelList.getGenre(type, label, year)

                            if rating == 'NR':
                                rating = self.channelList.getRating(type, label, year)
                            
                            try:
                                if not taglines and len(taglines.group(1)) == 0:
                                    tagline = self.channelList.getTagline(label, year)
                            except:
                                tagline = ''
                                
                            if imdbnumber != 0:
                                Managed = self.channelList.cpManaged(label, imdbnumber)
                                
                        if not '(' in label and year != 0:
                            showtitle = label + ' ('+str(year)+')'
                            
                        GenreLiveID = [genre, type, imdbnumber, dbid, Managed, playcount, rating]
                        genre, LiveID = self.channelList.packGenreLiveID(GenreLiveID)           
                        tmpstr += showtitle + "//" + tagline + "//" + theplot + "//" + (genre) + "////" + (LiveID)
                    
                    else: #Music
                        LiveID = 'music|0|0|False|1|NR|'
                        artist = re.search('"artist" *: *"(.*?)"', f)
                        tmpstr += album.group(1) + "//" + artist.group(1) + "//" + 'Music' + "////" + LiveID
                
                file = unquote(match.group(1))
                tmpstr = tmpstr
                tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                tmpstr = tmpstr + '\n' + file.replace("\\\\", "\\")            
            except Exception,e:
                self.log('GetPlayingTmpstr, failed...' + str(e))
                pass
        setProperty("Playing.OnDemand_tmpstr",tmpstr)
        return self.SetMediaInfo(data[0], data[1], data[2], data[3], tmpstr)

        
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

            
    def GetMpath(self, mediapath):
        if mediapath[0:5] == 'stack':
            smpath = (mediapath.split(' , ')[0]).replace('stack://','').replace('rar://','')
            mpath = (os.path.split(smpath)[0]) + '/'
        elif mediapath[0:6] == 'plugin':
            mpath = 'plugin://' + mediapath.split('/')[2] + '/'
        elif mediapath[0:4] == 'upnp':
            mpath = 'upnp://' + mediapath.split('/')[2] + '/'
        else:
            mpath = (os.path.split(mediapath)[0]) + '/'
        return mpath
                
                
    def end(self):
        self.log('end')  
        self.isExiting = True   
        self.background.setLabel('Exiting')
        # Prevent the player from setting the sleep timer
        self.Player.stopped = True
        curtime = time.time()
        xbmc.executebuiltin("PlayerControl(repeatoff)")
        updateDialog = xbmcgui.DialogProgress()
        updateDialog.create("PseudoTV Live", "Exiting")
        self.StopUPNP()

        if CHANNEL_SHARING == True and self.isMaster:
            updateDialog.update(0, "Exiting", "Removing File Locks")
            GlobalFileLock.unlockFile('MasterLock')
        
        GlobalFileLock.close()
        
        # destroy window dialogs
        try:
            del self.myDVR
            del self.myApps
            del self.myOndemand
            del self.myVideoInfo
        except:
            pass
            
        try:
            if self.playerTimer.isAlive():
                self.playerTimer.cancel()
                self.playerTimer.join()
            
            if self.Player.isPlaying():
                self.lastPlayTime = self.Player.getTime()
                self.lastPlaylistPosition = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                self.Player.stop()
        except:
            pass
            
        updateDialog.update(1, "Exiting", "Stopping Timers")
        
        try:
            if self.channelLabelTimer.isAlive():
                self.channelLabelTimer.cancel()
                self.channelLabelTimer.join()
        except:
            pass

        try:
            if self.GotoChannelTimer.isAlive():
                self.GotoChannelTimer.cancel()
        except:
            pass
            
        updateDialog.update(2)

        try:
            if self.notificationTimer.isAlive():
                self.notificationTimer.cancel()
                self.notificationTimer.join()
        except:
            pass
        try:
            if self.infoTimer.isAlive():
                self.infoTimer.cancel()
                self.infoTimer.join()
        except:
            pass

        updateDialog.update(3)

        try:
            if self.sleepTimeValue > 0:
                if self.sleepTimer.isAlive():
                    self.sleepTimer.cancel()
        except:
            pass
          
        updateDialog.update(4, "Exiting", "Stopping Timer Threads")  
          
        try:
            if self.popTimer.isAlive():
                self.popTimer.cancel()
        except:
            pass             
        try:
            if self.MenuControlTimer.isAlive():
                self.MenuControlTimer.cancel()
        except:
            pass
        try:
            if self.SetOnNowTimer.isAlive():
                self.SetOnNowTimer.cancel()
        except:
            pass
        try:
            if self.GetPlayingTmpstrTimer.isAlive():
                self.GetPlayingTmpstrTimer.cancel()
        except:
            pass
        try:
        
            if self.channelThread_Timer.isAlive():
                self.channelThread_Timer.cancel()
        except:
            pass
        try:
            if self.AutoJumpThread.isAlive():
                self.AutoJumpThread.cancel()
        except:
            pass
        try:
            if self.PlayerTimeoutThread.isAlive():
                self.PlayerTimeoutThread.cancel()
        except:
            pass 
        try:
            if self.TogglesetVisibleTimer.isAlive():
                self.TogglesetVisibleTimer.cancel()
        except:
            pass
            
        updateDialog.update(5, "Exiting", "Stopping Artwork Threads")  
            
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
            if self.Artdownloader.DownloadArtTimer.isAlive():
                self.Artdownloader.DownloadArtTimer.cancel()
        except:
            pass
        # try:
            # if self.ArtServiceThread.isAlive():
                # self.ArtServiceThread.cancel()
        # except:
            # pass
            
        updateDialog.update(6)

        if self.channelThread.isAlive():
            for i in range(30):
                try:
                    self.channelThread.join(1.0)
                except:
                    pass

                if self.channelThread.isAlive() == False:
                    break

                updateDialog.update(7 + i, "Exiting", "Stopping Channel Threads")

            if self.channelThread.isAlive():
                self.log("Problem joining channel thread", xbmc.LOGERROR)

        if self.isMaster:
        
            try:#Set Startup Channel
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
        json_query = ('{"jsonrpc": "2.0", "method": "JSONRPC.NotifyAll", "params": {"sender":"PTVL","message":"PseudoTV_Live - Stopping"}, "id": 1}')
        self.channelList.sendJSON(json_query)
        self.background.setVisible(False)
        updateDialog.close()
        self.close()
        
        
    def change_watched(self):
        if getProperty("Playing.Type") == 'movie':
            if getProperty("Playing.DBID") != '0' and getProperty("Playing.ID") != 0:
                try:
                    json_query = ('{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }' % getProperty("Playing.DBID"))
                    self.channelList.sendJSON(json_query)
                except:
                    pass
            else:
                try:
                    from metahandler import metahandlers
                    metaget = metahandlers.MetaData(preparezip=False)
                    metaget.get_meta('movie', self.title ,year=self.year)
                    metaget.change_watched(getProperty("Playing.Type"), '', getProperty("Playing.ID"), season='', episode='', year='', watched=7)
                except:
                    pass

        elif getProperty("Playing.Type") == 'tvshow':
             if (getProperty("Playing.Season") != 0 and getProperty("Playing.Episode") !=0):
                if getProperty("Playing.DBID") != '0' and getProperty("Playing.ID") != 0:
                    try:
                        json_query = ('{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }' % getProperty("Playing.DBID"))
                        self.channelList.sendJSON(json_query)
                    except:
                        pass
                else:
                    try:
                        from metahandler import metahandlers
                        metaget = metahandlers.MetaData(preparezip=False)
                        metaget.get_meta('tvshow', self.show, imdb_id=self.imdb)
                        metaget.get_episode_meta(self.show, self.imdb, self.season, self.episode)
                        metaget.change_watched(getProperty("Playing.Type"), '', getProperty("Playing.ID"), season=getProperty("Playing.Season"), episode=getProperty("Playing.Episode"), year='', watched=7)
                    except:
                        pass

                        
    def MenuControl(self, type, timer, hide=False):
        self.log("MenuControl, type = " + type + ", hide = " + str(hide))
        try:
            if self.MenuControlTimer.isAlive():
                self.MenuControlTimer.cancel()
        except:
            pass
        
        if hide:
            self.DisableOverlay = False
        else:
            self.hideInfo()
            self.hidePOP()
            self.DisableOverlay = True  
            
        if type == 'Menu':
            if hide:
                try:
                    self.showingMenu = False 
                    self.infoOffset = 0        
                    self.getControl(119).setVisible(False)            
                except:
                    pass
            else:
                self.showMenu() 
                
        elif type == 'MenuAlt':
            if hide:
                try:
                    self.showingMenuAlt = False                   
                    self.setFocusId(1001)  
                    self.list.setVisible(False)   
                    self.getControl(130).setVisible(False)
                    self.MenuControl('Menu',self.InfTimer)
                except:
                    pass
            else:
                self.ShowMenuAlt()
                
        elif type == 'MoreInfo':
            if hide:
                try:
                    self.showingMoreInfo = False
                    self.infoOffset = 0     
                    self.getControl(222).setVisible(False)
                except:
                    pass
            else:
                self.ShowMoreInfo()
                
                
    def Jump2Favorite(self):
        NextFav = self.FavChanLst[0]
        for n in range(len(self.FavChanLst)):
            if int(self.FavChanLst[n]) > self.currentChannel:
                NextFav = self.FavChanLst[n]
                break   
        return self.fixChannel(int(NextFav))
      
        # NextFav = int(min(self.FavChanLst, key=lambda x:abs(int(x)-self.currentChannel)))
        # if self.currentChannel == NextFav:
            # try:
                # NextFav = int(self.FavChanLst[(closest(self.FavChanLst, self.currentChannel))+1])
            # except:
                # NextFav = int(self.FavChanLst[(closest(self.FavChanLst, self.currentChannel))-1])
                 
                 
    def isChanFavorite(self, chan):
        Favorite = False
        if str(chan) in self.FavChanLst:
            Favorite = True
        return Favorite
        
        
    def chkChanFavorite(self):
        if str(self.currentChannel) in self.FavChanLst:
            return 'Remove Favorite'
        else:
            return 'Set Favorite'
                

    def TogglesetVisible(self):
        self.log("TogglesetVisible")
        if getProperty("PTVL.FEEDtoggle") == "true":
            setProperty("PTVL.FEEDtoggle","false")
        else:
            setProperty("PTVL.FEEDtoggle","true")
        self.TogglesetVisibleTimer = threading.Timer(1800.0, self.TogglesetVisible)
        self.TogglesetVisibleTimer.name = "TogglesetVisibleTimer"
        self.TogglesetVisibleTimer.start()
     
        # call weather
        # http://localhost:9000/jsonrpc?request={"jsonrpc":"2.0","method":"GUI.ActivateWindow","params":{"window":"weather"},"id":18}
        # set fullscreen
        # http://localhost:9000/jsonrpc?request={"jsonrpc":"2.0","method":"GUI.SetFullscreen","params":{"fullscreen":true},"id":19}
        # call vod
        # http://localhost:9000/jsonrpc?request={"jsonrpc":"2.0","method":"GUI.ActivateWindow","params":{"window":"videoosd"},"id":5}
        # call a/settings2
        # http://localhost:9000/jsonrpc?request={"jsonrpc":"2.0","method":"GUI.ActivateWindow","params":{"window":"osdaudiosettings"},"id":17}
        # http://localhost:9000/jsonrpc?request={"jsonrpc":"2.0","method":"GUI.ActivateWindow","params":{"window":"osdvideosettings"},"id":16}