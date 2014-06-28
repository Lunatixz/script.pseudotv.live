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
import time
import datetime
import sys, re
import random, traceback
import urllib, urllib2
import fanarttv
import socket
socket.setdefaulttimeout(5)

from ChannelList import ChannelList
from Globals import *
from FileAccess import FileLock, FileAccess
from xml.etree import ElementTree as ET
from tvdb import *
from tmdb import *
from urllib import unquote
from metahandler import metahandlers

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
    
    
    def JsonArtwork(self, path, media='video'):
        self.log('JsonArtwork')
        chanlist = ChannelList()
        json_query = uni('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "%s", "properties":["art"]}, "id": 1}' % ((path), media))
        json_folder_detail = chanlist.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        self.log('JsonArtwork - return')
        return file_detail

    
    def LocalArtwork(self, path, type, arttype):
        if Cache_Enabled:
            self.log("LocalArtwork Cache")
            try:
                result = artwork.cacheFunction(self.LocalArtwork_NEW, path, type, arttype)
            except:
                self.log("LocalArtwork Cache Failed Forwarding to LocalArtwork_NEW")
                result = self.LocalArtwork_NEW(path, type, arttype)
                pass
        else:
            self.log("LocalArtwork Cache Disabled")
            result = self.LocalArtwork_NEW(path, type, arttype)
        if not result:
            result = 0
        return result
        
        
    def LocalArtwork_NEW(self, path, type, arttype):
        self.log('LocalArtwork_NEW')
        arttype = arttype.replace('folder','poster').replace('character','characterart').replace('logo','clearlogo').replace('disc','discart')#correct search names
        results = self.JsonArtwork(path)
        arttype = ((type + '.' + arttype if type == 'tvshow' else arttype))
        fletype = ''

        for f in results:
            arttypes = re.search(('"%s" *: *"(.*?)"' % arttype), f)

            if arttypes:
                fletype = unquote((arttypes.group(1).split(','))[0]).replace('image://','').replace('.jpg/','.jpg').replace('.png/','.png')

            if fletype:
                break
        self.log('LocalArtwork_NEW - return')  
        return fletype
  
     
    def FindArtwork(self, type, chtype, id, mediapath, arttypeEXT):
        if Cache_Enabled:
            self.log("FindArtwork Cache")
            chtype = int(chtype)
            try: #stagger artwork cache by chtype
                if chtype <= 3:
                    result = artwork1.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
                elif chtype > 3 and chtype <= 6:
                    result = artwork2.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
                elif chtype > 6 and chtype <= 9:
                    result = artwork3.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
                elif chtype > 9 and chtype <= 12:
                    result = artwork4.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
                elif chtype > 9 and chtype <= 15:
                    result = artwork5.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
                else:
                    result = artwork6.cacheFunction(self.FindArtwork_NEW, type, chtype, id, mediapath, arttypeEXT)
            except:
                self.log("FindArtwork Cache Failed Forwarding to FindArtwork_NEW")
                result = self.FindArtwork_NEW(type, chtype, id, mediapath, arttypeEXT)
                pass
        else:
            self.log("FindArtwork Cache Disabled")
            result = self.FindArtwork_NEW(type, chtype, id, mediapath, arttypeEXT)
        if not result:
            result = 0
        return result
         

    def FindArtwork_NEW(self, type, chtype, id, mediapath, arttypeEXT):
        self.log('FindArtwork_NEW')
        chtype = int(chtype)
        setImage = ''
        arttype = arttypeEXT.split(".")[0]
        fle = str(id) + '-' + arttypeEXT
        ArtCache = os.path.join(ART_LOC, fle)
        MediaImage = os.path.join(MEDIA_LOC, (arttype + '.png'))
        DefaultImage = os.path.join(DEFAULT_MEDIA_LOC, (arttype + '.png'))

        if chtype <= 6:
            self.log('FindArtwork, Local')
            #XBMC Artwork
            setImage = self.LocalArtwork(mediapath, type, arttype)
            
            if not setImage:
                #XBMC Artwork - Fallback
                self.log('FindArtwork, Local - Local - Fallback')
                arttype_fallback = arttype.replace('landscape','fanart')
                setImage = self.LocalArtwork(mediapath, type, arttype_fallback)
                
            if not setImage:
                if (id != 0 or id != '0') and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':
                    #PseudoTV Artwork Cache
                    if FileAccess.exists(ArtCache):
                        setImage = ArtCache
                    else:
                        #Download Artwork
                        self.log('FindArtwork, Local - Download')
                        setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)

                    if not setImage:
                        #Download Artwork - Fallback
                        self.log('FindArtwork, Local - Download - Fallback')
                        arttype_fallback = arttypeEXT.replace('landscape','fanart')
                        setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)
       
            if not setImage:    
                self.log('FindArtwork, Local - Default')
                #Default fallbacks
                if FileAccess.exists(MediaImage):
                    #Skin media
                    setImage = MediaImage
                elif FileAccess.exists(DefaultImage):
                    #Default Skin media
                    setImage = DefaultImage
        
        elif chtype == 7:
            self.log('FindArtwork, Local - Directory')
            folderArt = os.path.join(path, 'folder.jpg')
            
            if FileAccess.exists(folderArt):
                setImage = folderArt
            else:      
                self.log('FindArtwork, Local - Directory - Default')
                #Default fallbacks
                if FileAccess.exists(MediaImage):
                    #Skin media
                    setImage = MediaImage
                elif FileAccess.exists(DefaultImage):
                    #Default Skin media
                    setImage = DefaultImage
        
        else:
            self.log('FindArtwork, NonLocal')
            addon = ''
            
            try:
                addon = mediapath.split('/')[2]
            except Exception,e:
                try:
                    addon = (mediapath.split('/'))
                    addon = ([x for x in addon if x != ''])
                    addon = str(addon[1])
                except:
                    pass
            
            icon = 'special://home/addons/'+ str(addon) + '/icon.png'
            fanart = 'special://home/addons/'+ str(addon) + '/fanart.jpg'
            
            if (id != 0 or id != '0') and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':
                #PseudoTV Artwork Cache
                if FileAccess.exists(ArtCache):
                    setImage = ArtCache
                else:
                    #Download Artwork
                    self.log('FindArtwork, NonLocal - Download')
                    setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)

                if not setImage:
                    self.log('FindArtwork, NonLocal - Download - Fallback')
                    #Download Artwork - Fallback
                    arttype_fallback = arttypeEXT.replace('landscape','fanart')
                    setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)

            if not setImage:
                if FileAccess.exists(icon):
                    setImage = icon
                
                    # if arttype == 'landscape' or arttype == 'fanart':
                        # if FileAccess.exists(fanart):
                            # setImage = fanart
                else:      
                    #if chtype watermark setimage
                    self.log('FindArtwork, NonLocal - Default')
                    #Default fallbacks
                    if FileAccess.exists(MediaImage):
                        #Skin media
                        setImage = MediaImage
                    elif FileAccess.exists(DefaultImage):
                        #Default Skin media
                        setImage = DefaultImage            
                        
        self.log('FindArtwork - return')  
        return setImage
        
                
    def DownloadMetaArt(self, type, fle, id, typeEXT, ART_LOC):
        self.log('DownloadMetaArt')
        ArtPath = os.path.join(ART_LOC, fle)
        
        if type == 'tvshow':
            Tid = id
            Mid = ''
        else:
            Mid = id
            Tid = ''
            
        typeEXT = typeEXT.split('.')[0]
        typeEXT = typeEXT.replace('landscape','backdrop_url').replace('fanart','backdrop_url').replace('logo','backdrop_url').replace('clearart','backdrop_url').replace('poster','cover_url').replace('banner','banner_url')
        
        # try:
        print 'metahander'
        self.metaget = metahandlers.MetaData(preparezip=False)
        ImageURL = str(self.metaget.get_meta(type, '', imdb_id=str(Mid), tmdb_id=str(Tid)))[typeEXT]
        resource = urllib.urlopen(ImageURL)
        output = FileAccess.open(ArtPath, 'w')
        output.write(resource.read())
        output.close()
        setImage = ArtPath
        # except:
            # pass
            
        return setImage
        
            
    def DownloadArt(self, type, id, fle, typeEXT, ART_LOC):
        self.log('DownloadArt')
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
                    return TVFilePath
                except Exception,e:
                    self.log('FanTVDownload Failed!')    
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
                    return MovieFilePath
                except Exception,e:
                    self.log('FanMovieDownload Failed!')
                    pass                
