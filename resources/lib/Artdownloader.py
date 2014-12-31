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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os, buggalo
import time, datetime, random
import datetime
import sys, re
import random, traceback
import urllib, urllib2, urlparse
import fanarttv
import socket

from ChannelList import *
from Globals import *
from FileAccess import FileAccess
from xml.etree import ElementTree as ET
from tvdb import *
from tmdb import *
from urllib import unquote, quote
from metahandler import metahandlers
from utils import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
    
try:
    from PIL import Image
    from PIL import ImageEnhance
except:
    pass
    
socket.setdefaulttimeout(30)

class Artdownloader:

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Artdownloader: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('Artdownloader: ' + msg, level)
    
    
    def JsonArtwork(self, mediapath, type, arttype, media='video'):
        self.log("JsonArtwork")
        arttype = arttype.replace('folder','poster').replace('character','characterart').replace('logo','clearlogo').replace('disc','discart')#correct search names
        arttype = ((type + '.' + arttype if type == 'tvshow' else arttype))
        fletype = ''
        file_detail = []
        
        try:
            chanlist = ChannelList()
            json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"%s","properties":["art"]},"id":10}' % (chanlist.escapeDirJSON(mediapath), media))
            json_folder_detail = chanlist.sendJSON(json_query)
            file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
            
            for f in file_detail:
                arttypes = re.search(('"%s" *: *"(.*?)"' % arttype), f)
                
                if arttypes != None and len(arttypes.group(1)) > 0:
                    fletype = (unquote((arttypes.group(1).split(','))[0])).replace('image://','').replace('.jpg/','.jpg').replace('.png/','.png')
                    break
        except Exception: 
            buggalo.onExceptionRaised()
        self.log("JsonArtwork, fletype = " + fletype)
        return fletype

        
    def JsonThumb(self, mediapath, media='video'):
        self.log("JsonThumb")
        file_detail = []
        thumbnail = ''
        try:
            chanlist = ChannelList()
            json_query = ('{jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["thumbnail"]}, "id": 1}' % (chanlist.escapeDirJSON(mediapath)))
            json_folder_detail = chanlist.sendJSON(json_query)
            file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
            
            for f in file_detail:      
                thumbnails = re.search('"thumbnail" *: *"(.*?)"', f)                               
                if thumbnails != None and len(thumbnails.group(1)) > 0:
                    thumbnail = thumbnails.group(1)
                    break
        except Exception: 
            buggalo.onExceptionRaised()
        self.log("JsonThumb, thumbnail = " + thumbnail)
        return thumbnail
        
        
    #Covert to transparent logo
    def ConvertBug(self, org, mod):
        self.log("ConvertBug")
        try:
            org =  xbmc.translatePath(org)
            original = Image.open(org)                  
            converted_img = original.convert('LA')
            converted_img.save(mod)
        except Exception: 
            buggalo.onExceptionRaised()
        return mod
        
        
    #Find ChannelBug, then Convert if enabled.
    def FindBug(self, chtype, chname, mediapath):
        self.log("FindBug")
        setImage = ''
        BugName = (chname[0:18] + '.png')
        BugCache = os.path.join(LOGO_CACHE_LOC,BugName)
        BugFolder = os.path.join(LOGO_LOC,BugName)
        BugDefault = os.path.join(IMAGES_LOC,'Default.png')
        BugDefault_YT = os.path.join(IMAGES_LOC,'Youtube.png')

        if REAL_SETTINGS.getSetting('UNAlter_ChanBug') == 'false':
            if FileAccess.exists(BugCache):
                print ('Find Local Cache Bug')
                setImage = BugCache                    
            elif FileAccess.exists(BugFolder):
                print ('Find Local Logo Bug')
                BugCache = self.ConvertBug(BugFolder, BugCache)
                setImage = BugCache
            else:
                setImage = BugDefault
        else:
            if FileAccess.exists(BugFolder):
                setImage = BugFolder
            else:
                setImage = BugDefault
        self.log("FindBug, setImage = " + setImage)
        return setImage

        
    def FindLogo(self, chtype, chname, mediapath):
        self.log("FindLogo")
        found = False
        setImage = ''
        LogoName = (chname[0:18] + '.png')
        LogoFolder = os.path.join(LOGO_LOC,LogoName)
        self.logoParser = lsHTMLParser()
        
        if FileAccess.exists(LogoFolder):
            setImage = LogoFolder
        #if chtype 0, 9 check chname to fanart.tv for logo match.
        # elif REAL_SETTINGS.getSetting('FindLogos_Enabled') == 'true':
            # file_detail = str(self.logoParser.retrieve_icons_avail())
            # file_detail = file_detail.replace("{'",'').replace("'}",'').replace("': '","|")
            # file_detail = file_detail.split("', '")
            # orgName = chname

            # for f in range(len(file_detail)):
                # file = (file_detail[f]).replace('HD','')
                # name = file.split('|')[0]
                # link = file.split('|')[1]

                # chname = name.split('_')
                # if len(chname) > 1:
                    # chname1 = (chname[0])
                    # chname2 = (chname[0] + ' ' + chname[1])
                # else:
                    # chname1 = (chname[0])
                    # chname2 = (chname[0])

                # orgName = orgName.replace(' hd','').replace(' tv','').replace('-tv','')
                # orgNameLST = [orgName.lower() +' tv',orgName.lower() +' hd']

                # print chname, chname1, chname2, orgName, orgNameLST

                # if chname2.lower() == orgName.lower():
                    # print chname2
                    # print link
                    # found = True
                    # break
                # elif chname1.lower() == orgName.lower():
                    # print chname1
                    # print link
                    # found = True
                    # break
                # elif chname1.lower() in orgNameLST:
                    # print chname1
                    # print link
                    # found = True
                    # break

            # if found == True:
                # print 'match'
                # resource = urllib.urlopen(link)
                # output = FileAccess.open(LogoFolder, 'w')
                # output.write(resource.read())
                # output.close()
                # setImage = LogoFolder
        else:
            setImage = 'NA.png'
        return setImage
     

    def FindArtwork(self, type, chtype, chname, id, mediapath, arttypeEXT):
        if Cache_Enabled == True: 
            self.log("FindArtwork Cache") 
            try: #stagger artwork cache by chtype
                # chtype = int(chtype)
                if chtype <= 3:
                    result = artwork1.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
                elif chtype > 3 and chtype <= 6:
                    result = artwork2.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
                elif chtype > 6 and chtype <= 9:
                    result = artwork3.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
                elif chtype > 9 and chtype <= 12:
                    result = artwork4.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
                elif chtype > 9 and chtype <= 15:
                    result = artwork5.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
                else:
                    result = artwork6.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, mediapath, arttypeEXT)
            except:
                self.log("FindArtwork Cache Failed Forwarding to FindArtwork_NEW") 
                result = self.FindArtwork_NEW(type, chtype, chname, id, mediapath, arttypeEXT)
                pass
        else:
            self.log("FindArtwork Cache Disabled")
            result = self.FindArtwork_NEW(type, chtype, chname, id, mediapath, arttypeEXT)
        if not result:
            result = 0
        return result
         

    def FindArtwork_NEW(self, type, chtype, chname, id, mediapath, arttypeEXT):
        self.log("FindArtwork_NEW")  
        setImage = ''
        arttype = arttypeEXT.split(".")[0]
        fle = id + '-' + arttypeEXT
        smpath = os.path.dirname(mediapath)
        ArtCache = os.path.join(ART_LOC, fle)
        mediapathSeason, filename = os.path.split(mediapath)
        mediapathSeries = os.path.dirname(mediapathSeason)
        
        if chtype <= 7:
            self.log('FindArtwork, Chtype <= 7')
            self.log('FindArtwork, Infolder Artwork')
            artSeries = xbmc.translatePath(os.path.join(smpath, arttypeEXT))
            artSeason = xbmc.translatePath(os.path.join(mediapath, arttypeEXT))
        
            if FileAccess.exists(artSeries): 
                setImage = artSeries
            elif FileAccess.exists(artSeason):
                setImage = artSeason
            else:
                self.log('FindArtwork, Infolder Artwork - Fallback')
                arttypeEXT_fallback = arttypeEXT.replace('landscape','fanart')
                artSeries_fallback = xbmc.translatePath(os.path.join(smpath, arttypeEXT_fallback))
                artSeason_fallback = xbmc.translatePath(os.path.join(mediapath, arttypeEXT_fallback))

                if FileAccess.exists(artSeries_fallback): 
                    setImage = artSeries_fallback
                elif FileAccess.exists(artSeason_fallback):
                    setImage = artSeason_fallback
                else:
                    self.log('FindArtwork, Json Artwork')
                    arttype_fallback = arttype.replace('landscape','fanart')#add more fallback replacements
                    # setImage = self.JsonArtwork(mediapath, type, arttype) 
                    
                    # if not setImage:
                        # print ('Find Json Artwork - Fallback')
                        # setImage = self.JsonArtwork(mediapath, type, arttype_fallback)
                        
                    if not setImage:   
                        if id != '0' and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':
                            self.log('FindArtwork, Artwork Folder')
                            if FileAccess.exists(ArtCache):
                                setImage = ArtCache
                            else:
                                self.log('FindArtwork, Artwork Download')
                                setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)

                                if not setImage:
                                    self.log('FindArtwork, Artwork Download - Fallback')
                                    setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)
        else:
            self.log('FindArtwork, Chtype > 7')
            if id != '0' and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':  
                self.log('FindArtwork, Artwork Folder')
                if FileAccess.exists(ArtCache):
                    setImage = ArtCache
                else:
                    self.log('FindArtwork, Artwork Download')
                    setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)
                    
                    if not setImage:
                        self.log('FindArtwork, Artwork Download - Fallback')
                        arttype_fallback = arttypeEXT.replace('landscape','fanart')
                        setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)
        #Plugin/UPNP
        if not setImage:     
            if mediapath.startswith('plugin://'):
                self.log('FindArtwork, Plugin Artwork') 
                setImage = self.SetPluginArt(mediapath, arttype) 
            # elif mediapath.startswith('upnp://'):   
                self.log('FindArtwork, UPNP Artwork') 
                # setImage = self.JsonThumb(mediapath) 
        #Default image
        if not setImage:    
            self.log('FindArtwork, Default Artwork')
            setImage = self.SetDefaultArt(chname, arttype)
            
        self.log('FindArtwork, setImage = ' + setImage)
        return setImage
        
        
    def SetDefaultArt(self, chname, arttype):
        self.log('SetDefaultArt')
        setImage = ''
        ChannelLogo = os.path.join(LOGO_LOC,chname[0:18] + '.png')
        MediaImage = os.path.join(MEDIA_LOC, (arttype + '.png'))
        if FileAccess.exists(ChannelLogo):
            setImage = ChannelLogo
        elif FileAccess.exists(MediaImage):
            setImage = MediaImage
        else:
            setImage = THUMB
        return setImage
    
    
    def SetPluginArt(self, mediapath, arttype):
        xbmc.log("SetPluginArt Cache")
        if Cache_Enabled == True:
            try:
                result = artwork.cacheFunction(self.SetPluginArt_NEW, mediapath, arttype)
            except:
                result = self.SetPluginArt_NEW(mediapath, arttype)
                pass
        else:
            result = self.SetPluginArt_NEW(mediapath, arttype)
        if not result:
            result = []
        return result     
             
             
    def SetPluginArt_NEW(self, mediapath, arttype):
        self.log('SetPluginArt_NEW')
        self.log('SetPluginArt, mediapath = ' + mediapath)
        setImage = ''
        try:
            plugin = os.path.split(mediapath.replace('plugin://',''))
            addon = os.path.split(plugin[0])[1]
            YTid = (plugin[1]).replace('?video_id=','').replace('?action=play_video&videoid=','')
            youtube = ['plugin.video.bromix.youtube', 'plugin.video.youtube']
            
            if addon in youtube:
                self.log('SetPluginArt, Youtube')
                setImage = "http://img.youtube.com/vi/"+YTid+"/0.jpg"
            # else:
                # self.log('SetPluginArt, JsonThumb')
                # setImage = self.JsonThumb(mediapath)
            
            if not setImage:
                self.log('SetPluginArt, PluginIcon')
                icon = 'special://home/addons/'+YTid+ '/icon.png'
                fanart = 'special://home/addons/'+YTid+ '/fanart.jpg'
                if FileAccess.exists(xbmc.translatePath(icon)):
                    setImage = icon
        except Exception: 
            buggalo.onExceptionRaised()  
        return setImage  
                                                
                
    def DownloadMetaArt(self, type, fle, id, typeEXT, ART_LOC):
        self.log('DownloadMetaArt')
        ArtPath = os.path.join(ART_LOC, fle)
        setImage = ''
        
        if type == 'tvshow':
            Tid = id
            Mid = ''
        else:
            Mid = id
            Tid = ''
            
        typeEXT = typeEXT.split('.')[0]
        typeEXT = typeEXT.replace('landscape','backdrop_url').replace('fanart','backdrop_url').replace('logo','backdrop_url').replace('clearart','backdrop_url').replace('poster','cover_url').replace('banner','banner_url')
        try:
            self.log('DownloadMetaArt, metahander')
            self.metaget = metahandlers.MetaData(preparezip=False)
            ImageURL = str(self.metaget.get_meta(type, '', imdb_id=str(Mid), tmdb_id=str(Tid)))[typeEXT]
            resource = urllib.urlopen(ImageURL)
            output = FileAccess.open(ArtPath, 'w')
            output.write(resource.read())
            output.close()
            setImage = ArtPath
        except Exception: 
            buggalo.onExceptionRaised()      
        return setImage
        
            
    def DownloadArt(self, type, id, fle, typeEXT, ART_LOC):
        self.log('DownloadArt')
        tvdbAPI = TVDB(TVDB_API_KEY)
        tmdbAPI = TMDB(TMDB_API_KEY)     
        
        if not FileAccess.exists(ART_LOC):
            FileAccess.makedirs(ART_LOC)

        ArtType = typeEXT.split('.')[0]        
        setImage = ''
        
        if type.lower() == 'tvshow':
            self.log('DownloadArt, tvshow')
            FanTVDownload = False
            TVFilePath = os.path.join(ART_LOC, fle) 
            tvdb_Types = ['banner', 'fanart', 'folder', 'poster']
            
            if ArtType in tvdb_Types:
                self.log('DownloadArt, TVDB')
                ArtType = ArtType.replace('banner', 'graphical').replace('folder', 'poster')
                tvdb = str(tvdbAPI.getBannerByID(id, ArtType))
                try:
                    tvdbPath = tvdb.split(', ')[0].replace("[('", "").replace("'", "") 
                    resource = urllib.urlopen(tvdbPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return TVFilePath
                except Exception,e:
                    FanTVDownload = True
                    print ('tvdbAPI Failed!') 
                    pass
            else:
                FanTVDownload = True
            
            if FanTVDownload == True:
                self.log('DownloadArt, Fanart.TV')
                TVFilePath = ''
                ArtType = ArtType.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'landscape')
                fan = str(fanarttv.get_image_list_TV(id))
                file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(fan)
                pref_language = fanarttv.get_abbrev(REAL_SETTINGS.getSetting('limit_preferred_language'))
                
                for f in file_detail:
                    languages = re.search("'language' *: *(.*?),", f)
                    art_types = re.search("'art_type' *: *(.*?),", f)
                    fanPaths = re.search("'url' *: *(.*?),", f)       
        
                    if languages and len(languages.group(1)) > 0:
                        language = (languages.group(1)).replace("u'",'').replace("'",'')

                        if language == pref_language:
                            print language

                            if art_types and len(art_types.group(1)) > 0:
                                art_type = art_types.group(1).replace("u'",'').replace("'",'').replace("[",'').replace("]",'')

                                if art_type.lower() == ArtType.lower():
                                    print art_type

                                    if fanPaths and len(fanPaths.group(1)) > 0:
                                        fanPath = fanPaths.group(1).replace("u'",'').replace("'",'')
                                        print fanPath
                                        
                                        if fanPath.startswith('http'):
                                            resource = urllib.urlopen(fanPath)
                                            output = FileAccess.open(TVFilePath, 'w')
                                            output.write(resource.read())
                                            output.close()
                                            break
                return TVFilePath
                           
        elif type == 'movie':
            self.log('DownloadArt, movie')
            FanMovieDownload = False
            MovieFilePath = os.path.join(ART_LOC, fle)
            tmdb = ['fanart', 'folder', 'poster']
            
            if ArtType in tmdb:
                self.log('DownloadArt, TMDB')
                ArtType = ArtType.replace('folder', 'poster')
                tmdb = tmdbAPI.get_image_list(id)
                try:
                    data = str(tmdb).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    tmdbPath = str([s for s in data if ArtType in s]).split("', 'width: ")[0]
                    match = re.search('url *: *(.*?),', tmdbPath)
                    tmdbPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    resource = urllib.urlopen(tmdbPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return MovieFilePath
                except Exception,e:
                    FanMovieDownload = True
                    print ('tmdbAPI Failed!') 
                    pass
            else:
                FanMovieDownload = True

            if FanMovieDownload == True:
                self.log('DownloadArt, Fanart.TV')
                ArtType = ArtType.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'landscape')
                fan = str(fanarttv.get_image_list_Movie(id))
                file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(fan)
                pref_language = fanarttv.get_abbrev(REAL_SETTINGS.getSetting('limit_preferred_language'))
                
                for f in file_detail:
                    languages = re.search("'language' *: *(.*?),", f)
                    art_types = re.search("'art_type' *: *(.*?),", f)
                    fanPaths = re.search("'url' *: *(.*?),", f)       
        
                    if languages and len(languages.group(1)) > 0:
                        language = (languages.group(1)).replace("u'",'').replace("'",'')

                        if language == pref_language:
                            print language

                            if art_types and len(art_types.group(1)) > 0:
                                art_type = art_types.group(1).replace("u'",'').replace("'",'').replace("[",'').replace("]",'')

                                if art_type.lower() == ArtType.lower():
                                    print art_type

                                    if fanPaths and len(fanPaths.group(1)) > 0:
                                        fanPath = fanPaths.group(1).replace("u'",'').replace("'",'')
                                        print fanPath
                                        
                                        if fanPath.startswith('http'):
                                            resource = urllib.urlopen(fanPath)
                                            output = FileAccess.open(MovieFilePath, 'w')
                                            output.write(resource.read())
                                            output.close()
                                            break
                return MovieFilePath

                    
    def EXTtype(self, arttype): 
        self.log('EXTtype')
        JPG = ['banner', 'fanart', 'folder', 'landscape', 'poster']
        PNG = ['character', 'clearart', 'logo', 'disc']
        
        if arttype in JPG:
            arttypeEXT = (arttype + '.jpg')
        else:
            arttypeEXT = (arttype + '.png')
        print ('EXTtype = ' + str(arttypeEXT))
        return arttypeEXT
      
 
    def PreArtService(self):
        self.log('PreArtService')
        ADDON_SETTINGS.loadSettings()
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
                fle = xbmc.translatePath(os.path.join(LOCK_LOC, ("channel_" + str(i + 1) + '.m3u')))
            except:
                pass
            
            if chtype >= 0:
                try:
                    if FileAccess.exists(fle):
                        f = FileAccess.open(fle, 'r')
                        lineLST = f.readlines()
                        lineLST.pop(0) #Remove unwanted first line '#EXTM3U'
                        for n in range(len(lineLST)):
                            line = lineLST[n]
                            
                            if line[0:7] == '#EXTINF':
                            
                                try:
                                    TV_liveid = (line.split('tvshow|')[1])
                                    TV_liveid =  'tvshow|' + TV_liveid
                                    type = (TV_liveid.split('|'))[0]
                                    id = (TV_liveid.split('|'))[1]
                                except Exception,e:
                                    MO_liveid = line.split('movie|')[1]
                                    MO_liveid = 'movie|' + MO_liveid
                                    type = MO_liveid.split('|')[0]
                                    id = MO_liveid.split('|')[1]
                                except:
                                    pass
                            
                            elif line[0:7] not in exclude:
                                if id != -1:
                                    if line[0:5] == 'stack':
                                        line = (line.split(' , ')[0]).replace('stack://','').replace('rar://','')
                                    mpath = (os.path.split(line)[0])
                                    youtube = ['plugin://plugin.video.bromix.youtube', 'plugin://plugin.video.youtube']
                                    
                                    #Insert Youtube ID for art parsing
                                    if mpath in youtube:
                                        YTid = line.split('id=')[1]
                                        mpath = (mpath + '/' + YTid).replace('/?path=/root','').replace('/play','')
                                        
                                    if type and mpath:
                                        newLST = [type, chtype, id, mpath]
                                        ArtLST.append(newLST)
                except:
                    pass
                        
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
                time.sleep(5)
            try:
                type1EXT = REAL_SETTINGS.getSetting('type1EXT')
            except:
                type1EXT = ''
                pass
            try:
                type2EXT = REAL_SETTINGS.getSetting('type2EXT')
            except:
                type2EXT = ''
                pass
    
            for i in range(len(ArtLst)):
                setImage1 = ''
                setImage2 = ''
                lineLST = ArtLst[i]
                type = lineLST[0]
                chtype = lineLST[1]
                id = lineLST[2]
                mpath = lineLST[3]
                chname = ''
                
                if type1EXT != '':
                    setImage1 = self.FindArtwork(type, chtype, chname, id, mpath, type1EXT)
                
                if type2EXT != '':
                    setImage2 = self.FindArtwork(type, chtype, chname, id, mpath, type2EXT)
                
                if DEBUG == 'true':
                    BUGMSG = ("Artwork Spooler has %d queues left" %(len(ArtLst) - i))
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", BUGMSG, 2000, THUMB) )
                
            stop = datetime.datetime.today()
            finished = stop - start
            MSSG = ("Artwork Spooled in %d seconds" %finished.seconds)                
            REAL_SETTINGS.setSetting("ArtService_Primed","true")              
            REAL_SETTINGS.setSetting("ArtService_Running","false")
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(stop))
            
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 2000, THUMB) )