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


# import xbmc
# import xbmcaddon
    # # xbmcaddon.Addon('plugin.program.super.favourites').openSettings()
    # label    = xbmc.getInfoLabel('ListItem.Label')
    # path     = xbmc.getInfoLabel('ListItem.FolderPath')
    # filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    # name     = xbmc.getInfoLabel('ListItem.Label')
    # thumb    = xbmc.getInfoLabel('ListItem.Thumb')
    # playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    # fanart   = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
    # isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1
    
    
# menu = []
# menu.append(label)
# menu.append('Settings')
# choice = xbmcgui.Dialog().select('PLTV', menu)

# if choice == None:
    # return

# if choice == 0:
    # #call you function
    # return

# if choice == 1:
    # xbmcaddon.Addon('plugin.program.super.favourites').openSettings()
    # return
    
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


import subprocess, os, sys, re, threading
import time, datetime, threading
import httplib, urllib, urllib2
import base64, shutil, random, errno
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from Globals import *

#Check settings2.xml for channel nums, channel types, channel names.

def readSettings2():
    print 'readSettings2'
    settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))    
    channelLST = []
    channelsLST = []
    NEWLST = []
    channelTYPE = 0

    if xbmcvfs.exists(settingsFile):
        f = open(settingsFile,'r')
        lineLST = f.readlines()

        for x in range(999):
            channelNUM = x + 1
            channelNAME = ''
            channelINFO = [channelNUM, channelNAME]
            channelsLST.append(channelINFO)

        for i in range(len(lineLST)):
            line = lineLST[i]

            if '_type" value="' in line:
                channelINFO = (line.split('<setting id="Channel_')[1]).replace('" />','')
                channelTYPE = int((channelINFO.split('_type" value="')[1]).replace('\n',''))
                channelNUM = int((channelINFO.split('_type" value="')[0]).replace('\n',''))

            if channelTYPE <= 6:
                if '<setting id="Channel_' + str(channelNUM) + '_1" value="' in line:
                    channelNAME = (line.split('value="')[1]).replace('" />','').replace('\n','')
                    channelINFO = [channelNUM, channelNAME]
                    channelLST.append(channelINFO)

            elif channelTYPE == 7:
                if '<setting id="Channel_' + str(channelNUM) + '_1" value="' in line:
                    channelNAME = 'Directory Channel'
                    channelINFO = [channelNUM, channelNAME]
                    channelLST.append(channelINFO)

            elif channelTYPE >= 8:
                if '<setting id="Channel_' + str(channelNUM) + '_rule_1_opt_1' in line:
                    channelNAME = (line.split('value="')[1]).replace('" />','').replace('\n','')
                    channelINFO = [channelNUM, channelNAME]
                    channelLST.append(channelINFO)

        for n in range(len(channelsLST)):
            try:
                chanLST = channelLST[n]
                NEW = chanLST
            except:
                NUMLST = channelsLST[n]
                NEW = NUMLST
                pass

            NEWLST.append(NEW)

        return NEWLST

        
def AppendPlugin(type, path, name):
    print 'AppendPlugin'

    try:
        plugin = path.split('/')[2]
    except:
        plugin = path
        pass
    print plugin

    if type == 'directory':
        print 'directory'
        #write setting2 config for chtype 16
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "16")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", path)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "0")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", name)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
    else:
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", path)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", name)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", plugin)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", name)
        ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")

        
        
# _STD_SETTINGS = 0
# _ADDTOFAVES   = 100
# _SF_SETTINGS  = 200
# _LAUNCH_SF    = 300
# _SEARCH       = 400
# _DOWNLOAD     = 500
# _PLAYLIST     = 600


# def doStandard():
    # window   = xbmcgui.getCurrentWindowId()

    # if window == 12005: #video playing
        # xbmc.executebuiltin('ActivateWindow(videoplaylist)')
        # return

    # xbmc.executebuiltin('Action(ContextMenu)')


# def copyFave(name, thumb, cmd):
    # import favourite
    # import utils

    # text = utils.GETTEXT(30019)

    # folder = utils.GetFolder(text)
    # if not folder:
        # return False
  
    # file  = os.path.join(folder, utils.FILENAME)
    # faves = favourite.getFavourites(file)

    # #if it is already in there don't add again
    # for fave in faves:
        # if fave[2] == cmd:            
            # return False

    # fave = [name, thumb, cmd] 
  
    # faves.append(fave)
    # favourite.writeFavourites(file, faves)

    # return True


# def activateCommand(cmd):
    # cmds = cmd.split(',', 1)

    # activate = cmds[0]+',return)'
    # plugin   = cmds[1][:-1]

    # #check if it is a different window and if so activate it
    # id = str(xbmcgui.getCurrentWindowId())

    # if id not in activate:
        # xbmc.executebuiltin(activate)
    
    # xbmc.executebuiltin('Container.Update(%s)' % plugin)


# def doMenu():
    # try:
        # import utils
    # except:
        # doStandard()
        # return    

    # import contextmenu

    # # to prevent master profile setting being used in other profiles
    # if (REAL_SETTINGS.getSetting("Context")) != 'true':
        # doStandard()
        # return

    # choice   = 0
    # label    = xbmc.getInfoLabel('ListItem.Label')
    # path     = xbmc.getInfoLabel('ListItem.FolderPath')
    # filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    # name     = xbmc.getInfoLabel('ListItem.Label')
    # thumb    = xbmc.getInfoLabel('ListItem.Thumb')
    # window   = xbmcgui.getCurrentWindowId()
    # playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    # fanart   = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
    # isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1

    # try:    file = xbmc.Player().getPlayingFile()
    # except: file = None

    # isStream = False
    # if file:
        # isStream = file.startswith('http://')

    # #GOTHAM only 
    # #if hasattr(xbmc.Player(), 'isInternetStream'):
    # #    isStream = xbmc.Player().isInternetStream()
    # #elif file:
    # #    isStream = file.startswith('http://')

    # print '**** Context Menu Information ****'
    # print 'Label      : %s' % label
    # print 'Folder     : %s' % folder 
    # print 'Path       : %s' % path    
    # print 'Filename   : %s' % filename
    # print 'Name       : %s' % name    
    # print 'Thumb      : %s' % thumb
    # print 'Fanart     : %s' % fanart   
    # print 'Window     : %d' % window  
    # print 'IsPlayable : %s' % playable
    # print 'IsFolder   : %s' % isFolder
    # print 'File       : %s' % file
    # print 'IsStream   : %s' % isStream

    # menu = []

    # if (len(menu) == 0) and window == 12005: #video playing
        # if isStream:
            # menu.append(('Download  %s' % label , _DOWNLOAD))
            # menu.append(('Show Playlist',         _PLAYLIST))
        # else:
            # return doStandard()
        # #cancel download feature for now
        # return doStandard()
    
    # if (len(menu) == 0) and len(path) > 0:    
        # menu.append(('Add to PseudoTV Live', _ADDTOFAVES))
        # menu.append(('PseudoTV Live Settings', _SF_SETTINGS))
        
    # #elif window == 10000: #Home screen
    # #    menu.append((utils.GETTEXT(30053), _LAUNCH_SF))
    # #    menu.append((utils.GETTEXT(30049), _SF_SETTINGS))


    # if len(menu) == 0:
        # doStandard()
        # return

    # xbmcgui.Window(10000).setProperty('SF_MENU_VISIBLE', 'true')
    # choice = contextmenu.showMenu(utils.ADDONID, menu)

    # if choice == _PLAYLIST:
        # xbmc.executebuiltin('ActivateWindow(videoplaylist)')

    # if choice == _DOWNLOAD: 
        # import download
        # download.download(file, 'c:\\temp\\file.mpg', 'Super Favourites')
    
    # if choice == _STD_SETTINGS:
        # xbmc.executebuiltin('XBMC.Action(ContextMenu)')

    # if choice == _SF_SETTINGS:
        # utils.ADDON.openSettings()

    # if choice == _ADDTOFAVES:
        # if isFolder:
            # cmd =  'ActivateWindow(%d,"%s")' % (window, path)
        # elif path.lower().startswith('script'):
            # if path[-1] == '/':
                # path = path[:-1]
            # cmd = 'RunScript("%s")' % path.replace('script://', '')
        # elif path.lower().startswith('videodb') and len(filename) > 0:
            # cmd = 'PlayMedia("%s")' % filename
        # #elif path.lower().startswith('musicdb') and len(filename) > 0:
        # #    cmd = 'PlayMedia("%s")' % filename
        # else:
            # cmd = 'PlayMedia("%s&sf_win_id=%d_")' % (path, window)

        # copyFave(name, thumb, cmd)

    # if choice == _LAUNCH_SF:
        # xbmc.executebuiltin('ActivateWindow(programs,plugin://%s)' % utils.ADDONID)

    # if choice == _SEARCH:
        # thumb  = thumb  if len(thumb)  > 0 else 'null'
        # fanart = fanart if len(fanart) > 0 else 'null'
        # import urllib
        # _SUPERSEARCH = 0     #declared as 0 in default.py
        # winID        = 10025 #video
        # cmd = 'ActivateWindow(%d,"plugin://%s/?mode=%d&keyword=%s&image=%s&fanart=%s")' % (window, utils.ADDONID, _SUPERSEARCH, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(fanart))
        # activateCommand(cmd)


# if xbmcgui.Window(10000).getProperty('SF_MENU_VISIBLE') != 'true':
    # doMenu()
    # xbmcgui.Window(10000).clearProperty('SF_MENU_VISIBLE')