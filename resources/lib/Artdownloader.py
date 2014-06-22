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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random, traceback
import urllib, urllib2
import fanarttv

from Globals import *
from FileAccess import FileLock, FileAccess
from xml.etree import ElementTree as ET
from tvdb import *
from tmdb import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

class Artdownloader:

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Artdownloader: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if REAL_SETTINGS.getSetting('enable_Debug') == "true":
            log('Artdownloader: ' + msg, level)
     
     
    def FindArtwork(self, type, chtype, id, title, mediapath, type1EXT, type2EXT):
        if Cache_Enabled:
            self.log("FindArtwork Cache")
            try:
                result = artwork.cacheFunction(self.FindArtwork_NEW, type, chtype, id, title, mediapath, type1EXT, type2EXT)
            except:
                self.log("FindArtwork Cache Failed Fowarding to FindArtwork_NEW")
                result = self.FindArtwork_NEW(type, chtype, id, title, mediapath, type1EXT, type2EXT)
                pass
        else:
            self.log("FindArtwork Cache Disabled")
            result = self.FindArtwork_NEW(type, chtype, id, title, mediapath, type1EXT, type2EXT)    
        if not result:
            result = 0
        return result
         
     
    def FindArtwork_NEW(self, type, chtype, id, title, mediapath, type1EXT, type2EXT):
        self.log('FindArtwork')
        print type, chtype, id, title, mediapath, type1EXT, type2EXT
        
        ArtDownload = ''            
        mediapathSeason, filename = os.path.split(mediapath)
        mediapathSeries = os.path.dirname(mediapathSeason)
        
        fle1 = str(id) + '-' + type1EXT
        type1 = type1EXT.split(".")[0]
        MediaImage1 = os.path.join(MEDIA_LOC, (type1 + '.png'))
        DefaultImage1 = os.path.join(DEFAULT_MEDIA_LOC, (type1 + '.png'))
        
        fle2 = str(id) + '-' + type2EXT
        type2 = type2EXT.split(".")[0]
        MediaImage2 = os.path.join(MEDIA_LOC, (type2 + '.png'))
        DefaultImage2 = os.path.join(DEFAULT_MEDIA_LOC, (type2 + '.png'))
              
        if FileAccess.exists(MediaImage1):
            setImage1 = MediaImage1
        elif FileAccess.exists(DefaultImage1):
            setImage1 = DefaultImage1
        else:
            setImage1 = 'NA.png'
            
        bakImage1 = setImage1
        
        if FileAccess.exists(MediaImage2):
            setImage2 = MediaImage2
        elif FileAccess.exists(DefaultImage2):
            setImage2 = DefaultImage2
        else:
            setImage2 = 'NA.png'
            
        bakImage2 = setImage2

        ArtLocal_Series1 = ascii(os.path.join(mediapathSeries, type1EXT))
        ArtLocal_Season1 = ascii(os.path.join(mediapathSeason, type1EXT))
        ArtCache1 = os.path.join(ART_LOC, fle1)
        
        ArtLocal_Season2 = ascii(os.path.join(mediapathSeason, type2EXT))
        ArtLocal_Series2 = ascii(os.path.join(mediapathSeries, type2EXT))
        ArtCache2 = os.path.join(ART_LOC, fle2)
        
        ###############
        if chtype <= 6:
            self.log('FindArtwork, Local')
            #508
            try:
                if FileAccess.exists(ArtLocal_Series1):
                    setImage1 = ArtLocal_Series1
                elif FileAccess.exists(ArtLocal_Season1):
                    setImage1 = ArtLocal_Season1
                elif FileAccess.exists(ArtCache1):
                    setImage1 = ArtCache1
                else:
                    setImage1 = self.DownloadArt(type, id, fle1, type1EXT, ART_LOC)
            except:
                pass
            
            #510   
            try:
                if FileAccess.exists(ArtLocal_Series2):
                    setImage2 = ArtLocal_Series2
                elif FileAccess.exists(ArtLocal_Season2):
                    setImage2 = ArtLocal_Season2
                elif FileAccess.exists(ArtCache2):
                    setImage2 = ArtCache2
                else:
                    setImage2 = self.DownloadArt(type, id, fle2, type2EXT, ART_LOC)
            except:
                pass
                
        ###############
        elif chtype == 7:
            self.log('FindArtwork, Directory')
            #508
            if FileAccess.exists(ArtLocal_Season1):
                setImage1 = ArtLocal_Season1
            elif FileAccess.exists(MediaImage1):
                setImage1 = MediaImage1
            elif FileAccess.exists(DefaultImage1):
                setImage1 = DefaultImage1
            
            #510
            if FileAccess.exists(ArtLocal_Season2):
                setImage2 = ArtLocal_Season2
            elif FileAccess.exists(MediaImage2):
                setImage2 = MediaImage2
            elif FileAccess.exists(DefaultImage2):
                setImage2 = DefaultImage2
            
        #################
        elif chtype == 8:
            self.log('FindArtwork, LiveTV')
            
            if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':
                self.log('LiveTV Art Enabled')
                
                #508
                try:
                    if FileAccess.exists(ArtCache1):
                        setImage1 = ArtCache1
                    else:
                        setImage1 = self.DownloadArt(type, id, fle1, type1EXT, ART_LOC)
                except:
                    pass
                    
                #510
                try:
                    if FileAccess.exists(ArtCache2):
                        setImage2 = ArtCache2
                    else:
                        setImage2 = self.DownloadArt(type, id, fle2, type2EXT, ART_LOC)
                except:
                    pass
                    
            else:
            
                if FileAccess.exists(MediaImage1):
                    setImage1 = MediaImage1
                elif FileAccess.exists(DefaultImage1):
                    setImage1 = DefaultImage1
                      
                if FileAccess.exists(MediaImage2):
                    setImage2 = MediaImage2
                elif FileAccess.exists(DefaultImage2):
                    setImage2 = DefaultImage2
                    
        #################
        elif chtype == 9:  
            self.log('FindArtwork, InternetTV')        
                    
            if FileAccess.exists((MEDIA_LOC + 'InternetTV.'+ type1 + '.png')):
                setImage1 = (MEDIA_LOC + 'InternetTV.'+ type1 + '.png')
            elif FileAccess.exists((DEFAULT_MEDIA_LOC + 'InternetTV.'+ type1 + '.png')):
                setImage1 = (DEFAULT_MEDIA_LOC + 'InternetTV.'+ type1 + '.png')
                  
            if FileAccess.exists((MEDIA_LOC + 'InternetTV.'+ type2 + '.png')):
                setImage2 = (MEDIA_LOC + 'InternetTV.'+ type2 + '.png')
            elif FileAccess.exists(DEFAULT_MEDIA_LOC + 'InternetTV.'+ type2 + '.png'):
                setImage2 = (DEFAULT_MEDIA_LOC + 'InternetTV.'+ type2 + '.png')
                    
        #################
        elif chtype == 10 or chtype == 17:   
            self.log('FindArtwork, Youtube')        
                    
            if FileAccess.exists((MEDIA_LOC + 'Youtube.'+ type1 + '.png')):
                setImage1 = (MEDIA_LOC + 'Youtube.'+ type1 + '.png')
            elif FileAccess.exists((DEFAULT_MEDIA_LOC + 'Youtube.'+ type1 + '.png')):
                setImage1 = (DEFAULT_MEDIA_LOC + 'Youtube.'+ type1 + '.png')
                  
            if FileAccess.exists((MEDIA_LOC + 'Youtube.'+ type2 + '.png')):
                setImage2 = (MEDIA_LOC + 'Youtube.'+ type2 + '.png')
            elif FileAccess.exists(DEFAULT_MEDIA_LOC + 'Youtube.'+ type2 + '.png'):
                setImage2 = (DEFAULT_MEDIA_LOC + 'Youtube.'+ type2 + '.png')
                    
        #################
        elif chtype == 11: 
            self.log('FindArtwork, RSS')          
                    
            if FileAccess.exists((MEDIA_LOC + 'RSS.'+ type1 + '.png')):
                setImage1 = (MEDIA_LOC + 'RSS.'+ type1 + '.png')
            elif FileAccess.exists((DEFAULT_MEDIA_LOC + 'RSS.'+ type1 + '.png')):
                setImage1 = (DEFAULT_MEDIA_LOC + 'RSS.'+ type1 + '.png')
                  
            if FileAccess.exists((MEDIA_LOC + 'RSS.'+ type2 + '.png')):
                setImage2 = (MEDIA_LOC + 'RSS.'+ type2 + '.png')
            elif FileAccess.exists(DEFAULT_MEDIA_LOC + 'RSS.'+ type2 + '.png'):
                setImage2 = (DEFAULT_MEDIA_LOC + 'RSS.'+ type2 + '.png')
                
        #################
        # elif chtype == 12:           
                    
                    
        #################
        elif chtype == 13:  
            self.log('FindArtwork, LastFM')         
                    
            if FileAccess.exists((MEDIA_LOC + 'LastFM.'+ type1 + '.png')):
                setImage1 = (MEDIA_LOC + 'LastFM.'+ type1 + '.png')
            elif FileAccess.exists((DEFAULT_MEDIA_LOC + 'LastFM.'+ type1 + '.png')):
                setImage1 = (DEFAULT_MEDIA_LOC + 'LastFM.'+ type1 + '.png')
                
            if FileAccess.exists((MEDIA_LOC + 'LastFM.'+ type2 + '.png')):
                setImage2 = (MEDIA_LOC + 'LastFM.'+ type2 + '.png')
            elif FileAccess.exists(DEFAULT_MEDIA_LOC + 'LastFM.'+ type2 + '.png'):
                setImage2 = (DEFAULT_MEDIA_LOC + 'LastFM.'+ type2 + '.png')
                    
        #################
        elif chtype == 14:    
            self.log('FindArtwork, Extras')       
                    
            #508
            try:
                if FileAccess.exists(ArtCache1):
                    setImage1 = ArtCache1
                else:
                    setImage1 = self.DownloadArt(type, id, fle1, type1EXT, ART_LOC)
            except:
                pass
                
            #510
            try:
                if FileAccess.exists(ArtCache2):
                    setImage2 = ArtCache2
                else:
                    setImage2 = self.DownloadArt(type, id, fle2, type2EXT, ART_LOC)
            except:
                pass
        
        #################           
        elif chtype == 15 or chtype == 16:
            self.log('FindArtwork, PluginTV')
            
            if id != '0':
                #508
                try:
                    if FileAccess.exists(ArtCache1):
                        setImage1 = ArtCache1
                    else:
                        setImage1 = self.DownloadArt(type, id, fle1, type1EXT, ART_LOC)
                except:
                    pass
                    
                #510
                try:
                    if FileAccess.exists(ArtCache2):
                        setImage2 = ArtCache2
                    else:
                        setImage2 = self.DownloadArt(type, id, fle2, type2EXT, ART_LOC)
                except:
                    pass
            else:
                id = mediapathSeason.replace("/?path=/root", "")
                id = id.split('plugin://', 1)[-1]
                
                icon = 'special://home/addons/'+ id + '/icon.png'
                fanart = 'special://home/addons/'+ id + '/fanart.jpg'
                
                if FileAccess.exists(icon):
                    setImage1 = icon
                elif FileAccess.exists(MediaImage1):
                    setImage1 = MediaImage1
                elif FileAccess.exists(DefaultImage1):
                    setImage1 = DefaultImage1
                    
                if FileAccess.exists(fanart):
                    setImage2 = fanart
                else:
                    setImage2 = setImage1
                          
        if type1EXT == 'NA.png' or type1EXT == '.png':
            setImage1 = bakImage1
        elif type2EXT == 'NA.png' or type2EXT == '.png':
            setImage2 = bakImage2
        
        print setImage1, setImage2
        return setImage1, setImage2
        
  
    def DownloadArt(self, type, id, fle, typeEXT, ART_LOC):
        self.log('DownloadArt')
        print type, id, fle, typeEXT, ART_LOC
        tvdbAPI = TVDB(TVDB_API_KEY)
        tmdbAPI = TMDB(TMDB_API_KEY)     

        if not FileAccess.exists(ART_LOC):
            os.makedirs(ART_LOC)

        ArtType = typeEXT.split('.')[0]
        MediaImage = os.path.join(MEDIA_LOC, (ArtType + '.png'))
        DefaultImage = os.path.join(DEFAULT_MEDIA_LOC, (ArtType + '.png'))
        
        if FileAccess.exists(MediaImage):
            setImage = MediaImage
        elif FileAccess.exists(DefaultImage):
            setImage = DefaultImage
        else:
            setImage = ''
        
        if type == 'tvshow':
            FanTVDownload = False
            TVFilePath = os.path.join(ART_LOC, fle)
            self.log('TVFilePath = ' + TVFilePath) 
            
            tvdb_Types = ['banner', 'fanart', 'folder', 'poster']
            
            if ArtType in tvdb_Types:
                ArtType = ArtType.replace('banner', 'graphical').replace('folder', 'poster')
                tvdb = str(tvdbAPI.getBannerByID(id, ArtType))
                try:
                    tvdbPath = tvdb.split(', ')[0].replace("[('", "").replace("'", "")
                    self.log('tvdbPath = ' + tvdbPath)  
                    resource = urllib.urlopen(tvdbPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return TVFilePath
                except Exception,e:
                    FanTVDownload = True
                    self.log('tvdbAPI Failed!') 
                    pass
            else:
                FanTVDownload = True

            if FanTVDownload == True:
                ArtType = ArtType.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'tvfanart')
                fan = fanarttv.get_image_list_TV(id)
                try:
                    FallbackFailed = True
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('fanPath = ' + fanPath)
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    FallbackFailed = False
                    return TVFilePath
                except Exception,e:
                    self.log('FanTVDownload Failed!')    
                    TVFilePath = setImage
                    if ArtType == 'landscape' and FallbackFailed == True:
                        TVFilePath = self.DownloadArt(type, id, fle, 'fanart.jpg', ART_LOC)
                        return TVFilePath

                    return setImage
                    pass

        elif type == 'movie':
            FanMovieDownload = False
            MovieFilePath = os.path.join(ART_LOC, fle)
            self.log('MovieFilePath = ' + MovieFilePath) 

            tmdb = ['fanart', 'folder', 'poster']
            
            if ArtType in tmdb:
                ArtType = ArtType.replace('folder', 'poster')
                tmdb = tmdbAPI.get_image_list(id)
                self.log('tmdb = ' + str(tmdb))
                try:
                    data = str(tmdb).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    tmdbPath = str([s for s in data if ArtType in s]).split("', 'width: ")[0]
                    match = re.search('url *: *(.*?),', tmdbPath)
                    tmdbPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('tmdbPath = ' + tmdbPath) 
                    resource = urllib.urlopen(tmdbPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return MovieFilePath
                except Exception,e:
                    FanMovieDownload = True
                    self.log('tmdbAPI Failed!') 
                    pass
            else:
                FanMovieDownload = True

            if FanMovieDownload == True:
                ArtType = ArtType.replace('folder', 'poster').replace('fanart', 'moviefanart')
                fan = fanarttv.get_image_list_Movie(id)
                self.log('fan = ' + str(fan))
                try:
                    FallbackFailed = True
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    self.log('fanPath = ' + fanPath) 
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    self.log('fanPath = ' + fanPath)
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    FallbackFailed = False
                    return MovieFilePath
                except Exception,e:
                    self.log('FanMovieDownload Failed!')
                    if ArtType == 'landscape' and FallbackFailed == True:
                        MovieFilePath = self.DownloadArt(type, id, fle, 'fanart.jpg', ART_LOC)
                        return MovieFilePath

                    return setImage
                    pass                
