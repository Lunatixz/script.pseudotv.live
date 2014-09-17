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

import os
import xbmcaddon, xbmc, xbmcgui, xbmcvfs
import Settings
import sys, re

from FileAccess import FileLock

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

    
def log(msg, level = xbmc.LOGDEBUG):
    try:
        xbmc.log(ADDON_ID + '-' + ascii(msg), level)
    except Exception,e:
        pass


def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, encoding, errors='ignore')
    return string

    
def utf(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode( 'utf-8', 'ignore' )
    return string


def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string
    

# Plugin Info
ADDON_ID = 'script.pseudotv.live'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
xbmc.log(ADDON_ID +' '+ ADDON_NAME +' '+ ADDON_PATH +' '+ ADDON_VERSION)

# API Keys
TVDB_API_KEY = '078845CE15BC08A7'
TMDB_API_KEY = '9c47d05a3f5f3a00104f6586412306af'
FANARTTV_API_KEY = '7bc4161cc4add99b14e51eddcdd5b985'

# Timers
AUTOSTART_TIMER = [0,5,10,15,20]#in seconds
SHORT_CLIP_ENUM = [15,30,60,90,120,180,240,300,360,420,460]#in seconds
INFOBAR_TIMER = [3,5,10,15,20,25]#in seconds
MEDIA_LIMIT = [10,25,50,100,250,500,1000,0]#Media Per/Channel, 0 = Unlimited
REFRESH_INT = [3600,10800,21600,43200,86400,172800,216000]#in seconds (1,3,6,12,24,48,72hrs)
TIMEOUT = 15 * 1000
TOTAL_FILL_CHANNELS = 20
PREP_CHANNEL_TIME = 60 * 60 * 24 * 5
ALLOW_CHANNEL_HISTORY_TIME = 60 * 60 * 24 * 1
NOTIFICATION_CHECK_TIME = 5
NOTIFICATION_TIME_BEFORE_END = 240
NOTIFICATION_DISPLAY_TIME = 8

# Rules/Modes
RULES_ACTION_START = 1
RULES_ACTION_JSON = 2
RULES_ACTION_LIST = 4
RULES_ACTION_BEFORE_CLEAR = 8
RULES_ACTION_BEFORE_TIME = 16
RULES_ACTION_FINAL_MADE = 32
RULES_ACTION_FINAL_LOADED = 64
RULES_ACTION_OVERLAY_SET_CHANNEL = 128
RULES_ACTION_OVERLAY_SET_CHANNEL_END = 256
MODE_RESUME = 1
MODE_ALWAYSPAUSE = 2
MODE_ORDERAIRDATE = 4
MODE_RANDOM = 8
MODE_REALTIME = 16
MODE_SERIAL = MODE_RESUME | MODE_ALWAYSPAUSE | MODE_ORDERAIRDATE
MODE_STARTMODES = MODE_RANDOM | MODE_REALTIME | MODE_RESUME

# Maximum is 10 for this
RULES_PER_PAGE = 7

#UPNP Clients
IPP1 = (REAL_SETTINGS.getSetting("UPNP1_IPP"))
IPP2 = (REAL_SETTINGS.getSetting("UPNP2_IPP"))
IPP3 = (REAL_SETTINGS.getSetting("UPNP3_IPP"))

#LOCATIONS
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile') #LOCKED
CHANNELS_LOC = os.path.join(SETTINGS_LOC, 'cache') + '/' #LOCKED
MADE_CHAN_LOC = os.path.join(CHANNELS_LOC, 'stored') + '/' #LOCKED
GEN_CHAN_LOC = os.path.join(CHANNELS_LOC, 'generated') + '/' #LOCKED
LOCK_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache')) + '/' #LOCKED
PVR_DOWNLOAD_LOC = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('PVR_Folder'))) #PVR Download location
ART_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache', 'artwork')) + '/' #Missing Artwork cache location
BCT_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache', 'bct')) + '/' #BCT cache location
FLST_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache', 'filelist')) + '/' #Filelist cache (tmpstr caching) location
LOGO_LOC = xbmc.translatePath(REAL_SETTINGS.getSetting('ChannelLogoFolder')) #Channel Logo location
LOGO_CACHE_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache', 'logos')) + '/' #Post Channel logo IMG Processing location
EPGGENRE_CACHE_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'cache', 'epg-genres')) + '/' #Post EPG IMG Processing location for future use!
BUMPER_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'bumpers')) + '/' #Local bumper location
IMAGES_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'images')) + '/'

# Core Default Image Locations
DEFAULT_MEDIA_LOC =  xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', 'media')) + '/'
DEFAULT_EPGGENRE_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'epg-genres')) + '/'
DEFAULT_LOGO_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'logos')) + '/'

#CORE IMG FILENAMES
TIME_BAR = 'pstvTimeBar.png'
BUTTON_FOCUS = 'pstvButtonFocus.png'
BUTTON_NO_FOCUS = 'pstvButtonNoFocus.png'
THUMB = (IMAGES_LOC + 'icon.png')
INTRO = (IMAGES_LOC + 'PTVL_INTRO.mp4')

#Channel Sharing location
if REAL_SETTINGS.getSetting('ChannelSharing') == "true":
    CHANNEL_SHARING = True
    LOCK_LOC = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('SettingsFolder'), 'cache')) + '/'
    BCT_LOC = xbmc.translatePath(os.path.join(LOCK_LOC, 'bct')) + '/'
else:
    CHANNEL_SHARING = False
    
# Original Skin Location changes    
if int(REAL_SETTINGS.getSetting('SkinSelector')) == 0:
    if os.path.exists(xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Original', xbmc.getSkinDir()))):
        Skin_Select = os.path.join('Original', xbmc.getSkinDir())
        print 'Skin_Select', Skin_Select
        MEDIA_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', Skin_Select, 'media')) + '/'
        EPGGENRE_LOC = xbmc.translatePath(os.path.join(MEDIA_LOC, 'epg-genres')) + '/'
    elif os.path.exists(xbmc.translatePath('special://skin/media/script.pseudotv.live')):
        Skin_Select = 'special://skin/media'
        MEDIA_LOC = xbmc.translatePath(os.path.join(Skin_Select, 'script.pseudotv.live')) + '/'
        EPGGENRE_LOC = xbmc.translatePath(os.path.join(MEDIA_LOC, 'epg-genres')) + '/'
    elif os.path.exists(xbmc.translatePath('special://skin/media/script.pseudotv')):
        Skin_Select = 'special://skin/media'
        MEDIA_LOC = xbmc.translatePath(os.path.join(Skin_Select, 'script.pseudotv')) + '/'
        EPGGENRE_LOC = xbmc.translatePath(os.path.join(MEDIA_LOC, 'epg-genres')) + '/'
    else:
        Skin_Select = 'Default'
        REAL_SETTINGS.setSetting("SkinSelector","2")
        
    if not xbmcvfs.exists(MEDIA_LOC):
        MEDIA_LOC = DEFAULT_MEDIA_LOC 
    if not xbmcvfs.exists(EPGGENRE_LOC):
        EPGGENRE_LOC = DEFAULT_EPGGENRE_LOC         
else:
    # SKIN SELECT
    if int(REAL_SETTINGS.getSetting('SkinSelector')) == 1:
        Skin_Select = 'Custom' 
    elif int(REAL_SETTINGS.getSetting('SkinSelector')) == 2:
        Skin_Select = 'Default'
    elif int(REAL_SETTINGS.getSetting('SkinSelector')) == 3:
        Skin_Select = 'PTVL'   
    elif int(REAL_SETTINGS.getSetting('SkinSelector')) == 4:
        Skin_Select = 'ConCast' 
    elif int(REAL_SETTINGS.getSetting('SkinSelector')) == 5:
        Skin_Select = 'TWC'     
    else: # Default if Skin_Select value isn't found
        Skin_Select = 'Default'
                     
    # Core Skin_Select Image Locations     
    if xbmcvfs.exists(xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', Skin_Select, 'media')) + '/'):
        MEDIA_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', Skin_Select, 'media')) + '/' 
    else:
        MEDIA_LOC = DEFAULT_MEDIA_LOC
            
    if xbmcvfs.exists(xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', Skin_Select, 'media', 'epg-genres')) + '/'):
        EPGGENRE_LOC = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', Skin_Select, 'media', 'epg-genres')) + '/'  
    else:  
        EPGGENRE_LOC = DEFAULT_EPGGENRE_LOC 
        
# Find XBMC Skin path
if xbmcvfs.exists(os.path.join('special://skin' ,'1080i')):
    skinPath = (os.path.join('special://skin' ,'1080i'))
else:
    skinPath = (os.path.join('special://skin' ,'720p'))
    
# PseudoTV Cache Control
if REAL_SETTINGS.getSetting("Cache_Enabled") == 'true': #
    Cache_Enabled = True
    xbmc.log("script.pseudotv.live-Globals: System Caching Enabled")
else:
    Cache_Enabled = False
    xbmc.log("script.pseudotv.live-Globals: System Caching Disabled")

# Globals
dlg = xbmcgui.Dialog()
ADDON_SETTINGS = Settings.Settings()
GlobalFileLock = FileLock()
Donor_Downloaded = False
NOTIFY = REAL_SETTINGS.getSetting('notify')
DEBUG = REAL_SETTINGS.getSetting('enable_Debug')   
SETTOP = REAL_SETTINGS.getSetting("EnableSettop")

# Common Cache types, 22hr clock allows overlap.  
daily = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "daily",22) #System Purge, Force Reset
weekly = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "weekly",22 * 7) #System Purge, Force Reset
monthly = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "monthly",((22 * 7) * 4)) #System Purge
parsers = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "parsers",((22 * 7) * 4)) #No Purge (API Queries)
artwork = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork1 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork1",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork2 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork2",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork3 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork3",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork4 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork4",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork5 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork5",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)
artwork6 = StorageServer.StorageServer("plugin://script.pseudotv.live/" + "artwork6",((22 * 7) * 4)) #Artwork Purge, Force Reset (Art Paths)

# HEX COLOR OPTIONS 4 (Overlay CHANBUG, EPG Genre & CHtype) 
# http://www.w3schools.com/html/html_colornames.asp
COLOR_RED = '#FF0000'
COLOR_GREEN = '#008000'
COLOR_mdGREEN = '#3CB371'
COLOR_BLUE = '#0000FF'
COLOR_ltBLUE = '#ADD8E6'
COLOR_CYAN = '#00FFFF'
COLOR_ltCYAN = '##E0FFFF'
COLOR_PURPLE = '#800080'
COLOR_ltPURPLE = '#9370DB'
COLOR_ORANGE = '#FFA500'
COLOR_YELLOW = '#FFFF00'
COLOR_GRAY = '#808080'
COLOR_ltGRAY = '#D3D3D3'
COLOR_mdGRAY = '#696969'
COLOR_dkGRAY = '#A9A9A9'
COLOR_BLACK = '#000000'
COLOR_WHITE = '#FFFFFF'
COLOR_HOLO = 'FF0297eb'
COLOR_SMOKE = '#F5F5F5'

# EPG Chtype/Genre COLOR TYPES
COLOR_RED_TYPE = ['10', '17', 'TV-MA', 'R', 'NC-17', 'Youtube', 'Sport', 'Sports Event', 'Sports Talk', 'Archery', 'Rodeo', 'Card Games', 'Martial Arts', 'Basketball', 'Baseball', 'Hockey', 'Football', 'Boxing', 'Golf', 'Auto Racing', 'Playoff Sports', 'Hunting', 'Gymnastics', 'Shooting', 'Sports non-event']
COLOR_GREEN_TYPE = ['5', 'News', 'Public Affairs', 'Newsmagazine', 'Politics', 'Entertainment', 'Community', 'Talk', 'Interview', 'Weather']
COLOR_mdGREEN_TYPE = ['9', 'Suspense', 'Horror', 'Horror Suspense', 'Paranormal', 'Thriller', 'Fantasy']
COLOR_BLUE_TYPE = ['Comedy', 'Comedy-Drama', 'Romance-Comedy', 'Sitcom', 'Comedy-Romance']
COLOR_ltBLUE_TYPE = ['2', '4', '14', '15', '16', 'Movie']
COLOR_CYAN_TYPE = ['8', 'Documentary', 'History', 'Biography', 'Educational', 'Animals', 'Nature', 'Health']
COLOR_ltCYAN_TYPE = ['Outdoors', 'Special', 'Reality']
COLOR_PURPLE_TYPE = ['Drama', 'Romance', 'Historical Drama']
COLOR_ltPURPLE_TYPE = ['12', '13', 'LastFM', 'Vevo', 'VevoTV', 'Musical', 'Music', 'Musical Comedy']
COLOR_ORANGE_TYPE = ['11', 'TV-PG', 'TV-14', 'PG', 'PG-13', 'RSS', 'Animation', 'Animated', 'Anime', 'Children', 'Cartoon', 'Family']
COLOR_YELLOW_TYPE = ['1', '3', '6', 'TV-Y7', 'TV-Y', 'TV-G', 'G', 'Action', 'Adventure', 'Action and Adventure', 'Action Adventure', 'Crime', 'Crime Drama', 'Mystery', 'Science Fiction', 'Series', 'Western', 'Soap', 'Variety', 'War', 'Law', 'Adults Only']
COLOR_GRAY_TYPE = ['Auto', 'Collectibles', 'Travel', 'Shopping', 'House Garden', 'Home and Garden', 'Gardening', 'Fitness Health', 'Fitness', 'Home Improvement', 'How-To', 'Cooking', 'Fashion', 'Aviation', 'Dance', 'Auction', 'Art', 'Exercise', 'Parenting']
COLOR_ltGRAY_TYPE = ['0', '7', 'NR', 'Consumer', 'Game Show', 'Other', 'Unknown', 'Religious', 'Anthology', 'None']

# http://developer.android.com/reference/android/graphics/Color.html
#               ['COLOR_HOLO', 'COLOR_CYAN', 'COLOR_GREEN', 'COLOR_GRAY', 'COLOR_ltGRAY', 'COLOR_WHITE']
COLOR_CHANNUM = ['0xFF0297eb', '0xC0C0C0C0', '0xff00ff00', '0xff888888', '0xffcccccc', '0xffffffff']
CHANBUG_COLOR = COLOR_CHANNUM[int(REAL_SETTINGS.getSetting('COLOR_CHANNUM'))]

#Actions
#https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_PAGEUP = 5
ACTION_PAGEDOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = (9, 10, 92, 247, 257, 275, 61467, 61448)
##KEY_BUTTON_BACK = 275   
##ACTION_NAV_BACK = 92
ACTION_SHOW_INFO = 11
ACTION_PAUSE = 12
ACTION_STOP = 13
ACTION_OSD = 122
ACTION_NUMBER_0 = 58
ACTION_NUMBER_1 = 59
ACTION_NUMBER_2 = 60
ACTION_NUMBER_3 = 61
ACTION_NUMBER_4 = 62
ACTION_NUMBER_5 = 63
ACTION_NUMBER_6 = 64
ACTION_NUMBER_7 = 65
ACTION_NUMBER_8 = 66
ACTION_NUMBER_9 = 67
ACTION_INVALID = 999
ACTION_SHOW_SUBTITLES = 25 #turn subtitles on/off. 
ACTION_AUDIO_NEXT_LANGUAGE = 56 #Select next language in movie
ACTION_RECORD = 170 #PVR Backend Record
ACTION_SHOW_CODEC = 27
ACTION_ASPECT_RATIO = 19 
ACTION_SHIFT = 118
#unused
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15
ACTION_STEP_FOWARD = 17
ACTION_STEP_BACK = 18
ACTION_BIG_STEP_FORWARD = 19
ACTION_BIG_STEP_BACK = 20
ACTION_PLAYER_FORWARD = 73
ACTION_PLAYER_REWIND = 74
ACTION_PLAYER_PLAY = 75
ACTION_PLAYER_PLAYPAUSE = 76
ACTION_TRIGGER_OSD = 243 #show autoclosing OSD. Can b used in videoFullScreen.xml window id=2005
ACTION_SHOW_MPLAYER_OSD = 83 #toggles mplayers OSD. Can be used in videofullscreen.xml window id=2005
ACTION_SHOW_OSD_TIME = 123 #displays current time, can be used in videoFullScreen.xml window id=2005
#ACTION_MENU = 117
ACTION_MENU = 7
ACTION_TELETEXT_RED = 215
ACTION_TELETEXT_GREEN = 216
ACTION_TELETEXT_YELLOW = 217
ACTION_TELETEXT_BLUE = 218

#define ACTION_VOLUME_UP            88
#define ACTION_VOLUME_DOWN          89
#define ACTION_MUTE                 91
#define ACTION_VOLAMP_UP            93
#define ACTION_VOLAMP_DOWN          94
#define ACTION_CHANNEL_SWITCH         183 #last channel?
#define ACTION_TOGGLE_WATCHED         200 // Toggle watched status (videos)
#define ACTION_TOGGLE_DIGITAL_ANALOG  202 // switch digital <-> analog
#Touch Support todo
#// touch actions
#define ACTION_TOUCH_TAP              401
#define ACTION_TOUCH_TAP_TEN          410
#define ACTION_TOUCH_LONGPRESS        411
#define ACTION_TOUCH_LONGPRESS_TEN    420
#define ACTION_GESTURE_NOTIFY         500
#define ACTION_GESTURE_BEGIN          501
#define ACTION_GESTURE_ZOOM           502 //sendaction with point and currentPinchScale (fingers together < 1.0 -> fingers apart > 1.0)
#define ACTION_GESTURE_ROTATE         503
#define ACTION_GESTURE_PAN            504
#define ACTION_GESTURE_SWIPE_LEFT       511
#define ACTION_GESTURE_SWIPE_LEFT_TEN   520
#define ACTION_GESTURE_SWIPE_RIGHT      521
#define ACTION_GESTURE_SWIPE_RIGHT_TEN  530
#define ACTION_GESTURE_SWIPE_UP         531
#define ACTION_GESTURE_SWIPE_UP_TEN     540
#define ACTION_GESTURE_SWIPE_DOWN       541
#define ACTION_GESTURE_SWIPE_DOWN_TEN   550
#// 5xx is reserved for additional gesture actions
#define ACTION_GESTURE_END            599

#UTC LiveTV plugin
UTC_PLUGIN = ['plugin.video.ustvnow', 'plugin.video.F.T.V']

#Dynamic Artwork plugin types
DYNAMIC_PLUGIN_TV = ['plugin.video.GOtv', 'plugin.video.genesis', 'PlayOn', 'plugin.video.ororotv']
DYNAMIC_PLUGIN_MOVIE = ['plugin.video.viooz.co', 'plugin.video.glowmovies.hd', 'plugin.video.genesis', 'plugin.video.yifymovies.hd', 'plugin.video.GOmovies', 'plugin.video.muchmovies.hd', 'plugin.video.cartoonhd', 'PlayOn'] #Title format must be "Movie (Year)"

# Plugin seek blacklist
BYPASS_SEEK = ['plugin.video.vevo_tv','plugin.video.g4tv','plugin.video.ustvnow']

# Bypass EPG (paused/stacked) by channel name
BYPASS_EPG = ['PseudoCinema']

# Bypass Overlay Coming up next by channel name
BYPASS_OVERLAY = ['PseudoCinema']