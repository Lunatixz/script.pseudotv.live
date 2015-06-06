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

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, datetime, random
import threading
import sys, re
import random, traceback
import urllib, urllib2, urlparse
import socket

from apis.fanarttv import *
from ChannelList import *
from Globals import *
from FileAccess import FileAccess
from xml.etree import ElementTree as ET
from apis import tvdb
from apis import tmdb
from urllib import unquote, quote
from utils import *
from HTMLParser import HTMLParser

try:
    from metahandler import metahandlers
except Exception,e:  
    xbmc.log("script.pseudotv.live-ChannelList: metahandler Import Failed" + str(e))

try:
    import buggalo
    buggalo.SUBMIT_URL = 'http://pseudotvlive.com/buggalo-web/submit.php'
except:
    pass
    
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

    def __init__(self):
        self.chanlist = ChannelList()
        self.fanarttv = fanarttv()
        self.tvdbAPI = tvdb.TVDB(TVDB_API_KEY)
        self.tmdbAPI = tmdb.TMDB(TMDB_API_KEY)  
        
        
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Artdownloader: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('Artdownloader: ' + msg, level)
    
    
    def dbidArt(self, type, chname, mpath, dbid, arttypeEXT):
        self.log("dbidArt")
        # Set image place-holder
        thumbnail = self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
        
        if type == 'tvshow':
            json_query = ('{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShowDetails","params":{"tvshowid":%s,"properties":["art"]},"id":1}' % dbid)
        elif type == 'movie':
            json_query = ('{"jsonrpc":"2.0","method":"VideoLibrary.GetMovieDetails","params":{"movieid":%s,"properties":["art"]},"id":1}' % dbid)
        else:
            return thumbnail
            
        arttype = (arttypeEXT.split(".")[0]).replace('landscape','fanart')
        json_folder_detail = self.chanlist.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        
        for f in file_detail:
            arttypes = re.search(('"%s" *: *"(.*?)"' % arttype), f)
            if arttypes != None and len(arttypes.group(1)) > 0:
                thumbnail = (unquote(xbmc.translatePath((arttypes.group(1).split(','))[0]))).replace('image://','').replace('.jpg/','.jpg').replace('.png/','.png')
                break   
        self.log("dbidArt, thumbnail = " + thumbnail)    
        return thumbnail

        
    def JsonThumb(self, chname, arttypeEXT, mediapath, media='video'):
        self.log("JsonThumb")
        file_detail = []
        # Set image place-holder
        thumbnail = self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
        json_query = ('{jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["thumbnail"]}, "id": 1}' % (self.chanlist.escapeDirJSON(mediapath)))
        json_folder_detail = self.chanlist.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        
        for f in file_detail:      
            thumbnails = re.search('"thumbnail" *: *"(.*?)"', f)                               
            if thumbnails != None and len(thumbnails.group(1)) > 0:
                thumbnail = (unquote(xbmc.translatePath((thumbnails.group(1).split(','))[0]))).replace('image://','').replace('.jpg/','.jpg').replace('.png/','.png')
                break

        self.log("JsonThumb, thumbnail = " + thumbnail)
        return thumbnail
    
    
    def AlphaLogo(self, org, mod):
        self.log("AlphaLogo")
        img = Image.open(org)
        img = img.convert("RGBA")
        datas = img.getdata()
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        img.putdata(newData)
        img.save(mod, "PNG")
                
        
    #Covert to transparent logo
    def ConvertBug(self, org, mod):
        self.log("ConvertBug")
        drive, path = os.path.splitdrive(mod)
        path, filename = os.path.split(path)
        try:
            if not FileAccess.exists(path):
                FileAccess.makedirs(path)
            org =  xbmc.translatePath(org)
            original = Image.open(org)                  
            converted_img = original.convert('LA')  
            img_bright = ImageEnhance.Brightness(converted_img)
            converted_img = img_bright.enhance(1.0)     
            converted_img.save(mod)
            return mod
        except Exception,e:
            self.log("ConvertBug Failed! " + str(e))
            pass
        
        
    #Find ChannelBug, then Convert if enabled.
    def FindBug(self, chtype, chname):
        self.logDebug("FindBug, chname = " + chname)
        setImage = ''
        BugName = (chname[0:18] + '.png')
        DefaultBug = os.path.join(IMAGES_LOC,'Default.png')
        BugFLE = xbmc.translatePath(os.path.join(LOGO_LOC,BugName))
        cachedthumb = xbmc.getCacheThumbName(BugFLE)
        cachefile = xbmc.translatePath(os.path.join(ART_LOC, cachedthumb[0], cachedthumb[:-4] + ".png")).replace("\\", "/")
        if REAL_SETTINGS.getSetting('UNAlter_ChanBug') == 'true':
            if not FileAccess.exists(BugFLE):
                BugFLE = DefaultBug
            return BugFLE
        else:
            if FileAccess.exists(cachefile):
                return cachefile
            else:
                if not FileAccess.exists(BugFLE):
                    return DefaultBug
                else:
                    return self.ConvertBug(BugFLE, cachefile)
    
    
    def FindLogo(self, chtype, chname, mpath):
        self.logDebug("FindLogo Cache")
        if Cache_Enabled == True: 
            try:
                result = artwork.cacheFunction(self.FindLogo_NEW, chtype, chname, mpath)
            except:
                result = self.FindLogo_NEW(chtype, chname, mpath)
                pass
        else:
            result = self.FindLogo_NEW(chtype, chname, mpath)
        if not result:
            result = THUMB
        return result  


    def FindLogo_NEW(self, chtype, chname, mpath):
        self.logDebug("FindLogo_NEW")
        found = False
        setImage = ''
        LogoName = (chname[0:18] + '.png')
        LogoFolder = os.path.join(LOGO_LOC,LogoName)
        
        if FileAccess.exists(LogoFolder):
            return LogoFolder
        else:
            if chtype == 6 or chtype == 7:
                smpath = mpath.rsplit('/',2)[0] #Path Above mpath ie Series folder
                artSeries = xbmc.translatePath(os.path.join(smpath, 'logo.png'))
                artSeason = xbmc.translatePath(os.path.join(mpath, 'logo.png'))
                if FileAccess.exists(artSeries): 
                    return artSeries
                elif FileAccess.exists(artSeason): 
                    return artSeason
                else:
                    return 'NA.png'
            else:
                return 'NA.png'
                # else:
                    # if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true': 
                        # self.Fanart_Download('tvshow', 'logo', id, LogoFolder)
                        
            # if setImage.startswith('http'):
                # requestDownload(setImage, LogoFolder)
            # else:
                # FileAccess.copy(setImage, LogoFolder)
            # return LogoFolder

        # if chtype == 1:
            # setImage = self.logoParser.retrieve_icon(chname)
        #if chtype 0, 9 check chname to fanart.tv for logo match.
        # elif REAL_SETTINGS.getSetting('FindLogos_Enabled') == 'true':
            # self.logoParser = lsHTMLParser()
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
        # else:
            # setImage = 'NA.png'
        # return setImage
        
    def FindArtwork(self, type, chtype, chname, id, dbid, mpath, arttypeEXT):
        if Cache_Enabled == True: 
            self.log("FindArtwork Cache") 
            try: #stagger artwork cache by chtype
                if chtype <= 3:
                    result = artwork1.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
                elif chtype > 3 and chtype <= 6:
                    result = artwork2.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
                elif chtype > 6 and chtype <= 9:
                    result = artwork3.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
                elif chtype > 9 and chtype <= 12:
                    result = artwork4.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
                elif chtype > 9 and chtype <= 15:
                    result = artwork5.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
                else:
                    result = artwork6.cacheFunction(self.FindArtwork_NEW, type, chtype, chname, id, dbid, mpath, arttypeEXT)
            except:
                self.log("FindArtwork Cache Failed Forwarding to FindArtwork_NEW") 
                result = self.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, arttypeEXT)
                pass
        else:
            self.log("FindArtwork Cache Disabled")
            result = self.FindArtwork_NEW(type, chtype, chname, id, dbid, mpath, arttypeEXT)
        if not result:
            result = self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
        return result

        
    def FindArtwork_NEW(self, type, chtype, chname, id, dbid, mpath, arttypeEXT):
        self.logDebug("FindArtwork_NEW, type = " + type + ', chtype = ' + str(chtype) + ', chname = ' + chname + ', id = ' + str(id) + ', dbid = ' + str(dbid) + ', arttypeEXT = ' + arttypeEXT)
        setImage = THUMB
        CacheArt = False
        DefaultArt = False
        arttype = arttypeEXT.split(".")[0]
        arttypeEXT_fallback = arttypeEXT.replace('landscape','fanart').replace('clearart','logo').replace('character','logo').replace('folder','poster')
        arttype_fallback = arttypeEXT_fallback.split(".")[0]
        
        if chtype <= 7:
            self.logDebug('FindArtwork_NEW, Infolder Artwork')
            smpath = mpath.rsplit('/',2)[0] #Path Above mpath ie Series folder
            artSeries = xbmc.translatePath(os.path.join(smpath, arttypeEXT))
            artSeason = xbmc.translatePath(os.path.join(mpath, arttypeEXT))
            artSeries_fallback = xbmc.translatePath(os.path.join(smpath, arttypeEXT_fallback))
            artSeason_fallback = xbmc.translatePath(os.path.join(mpath, arttypeEXT_fallback))

            if FileAccess.exists(artSeries): 
                return artSeries
            elif FileAccess.exists(artSeason):
                return artSeason
            elif FileAccess.exists(artSeries_fallback): 
                return artSeries_fallback
            elif FileAccess.exists(artSeason_fallback):
                return artSeason_fallback
            elif dbid != '0':
                return self.dbidArt(type, chname, mpath, dbid, arttypeEXT)
        else:
            if id == '0':
                if type == 'youtube':
                    self.logDebug('FindArtwork_NEW, Youtube')
                    return "http://i.ytimg.com/vi/"+dbid+"/mqdefault.jpg"
                elif type == 'rss':
                    self.logDebug('FindArtwork_NEW, RSS')
                    if dbid != '0':
                        return dbid.decode('base64')
                    else:
                        return self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
                # elif mpath[0:4] == 'upnp':
                    # self.logDebug('FindArtwork_NEW, UPNP Thumb')
                    # return self.JsonThumb(chname, arttypeEXT, mediapath) 
                else:
                    return self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
            else:
                self.logDebug('FindArtwork_NEW, Artwork Cache')
                fle = id + '-' + arttypeEXT
                ext = arttypeEXT.split('.')[1]
                url = os.path.join(mpath, fle)
                cachedthumb = xbmc.getCacheThumbName(url)
                cachefile = xbmc.translatePath(os.path.join(ART_LOC, cachedthumb[0], cachedthumb[:-4] + "." + ext)).replace("\\", "/")
                
                if FileAccess.exists(cachefile) == True:
                    return cachefile
                else:
                    if REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true': 
                        self.logDebug('FindArtwork_NEW, Artwork Download')
                        self.DownloadArt(type, id, arttype, arttype_fallback, cachefile, chname, mpath, arttypeEXT)
                        # return cachefile
                
                
    def SetDefaultArt(self, chname, mpath, arttypeEXT):
        self.logDebug("SetDefaultArt Cache")
        if Cache_Enabled == True: 
            try:
                result = artwork.cacheFunction(self.SetDefaultArt_NEW, chname, mpath, arttypeEXT)
            except:
                result = self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
                pass
        else:
            result = self.SetDefaultArt_NEW(chname, mpath, arttypeEXT)
        if not result:
            result = THUMB
        return result  

        
    def SetDefaultArt_NEW(self, chname, mpath, arttypeEXT):
        self.logDebug('SetDefaultArt_NEW, chname = ' + chname + ', arttypeEXT = ' + arttypeEXT)
        setImage = ''
        arttype = arttypeEXT.split(".")[0]
        MediaImage = os.path.join(MEDIA_LOC, (arttype + '.png'))
        StockImage = os.path.join(IMAGES_LOC, (arttype + '.png'))
        ChannelLogo = os.path.join(LOGO_LOC,chname[0:18] + '.png')
        
        if FileAccess.exists(ChannelLogo):
            self.logDebug('SetDefaultArt, Channel Logo')
            return ChannelLogo
        elif mpath[0:6] == 'plugin':
            self.logDebug('SetDefaultArt, Plugin Icon')
            icon = 'special://home/addons/'+(mpath.replace('plugin://',''))+ '/icon.png'
            return icon
        elif FileAccess.exists(MediaImage):
            self.logDebug('SetDefaultArt, Media Image')
            return MediaImage
        elif FileAccess.exists(StockImage):
            self.logDebug('SetDefaultArt, Stock Image')
            return StockImage
        else:
            self.logDebug('SetDefaultArt, THUMB')
            return THUMB
    
              
    def DownloadArt(self, type, id, arttype, arttype_fallback, cachefile, chname, mpath, arttypeEXT):
        self.log('DownloadArt')
        data = [type, id, arttype, arttype_fallback, cachefile, chname, mpath, arttypeEXT]
        try:
            if self.DownloadArtTimer.isAlive():
                self.DownloadArtTimer.cancel()
                self.DownloadArtTimer.join()
        except:
            pass
        try:
            self.DownloadArtTimer = threading.Timer(1.0, self.DownloadArt_Thread, [data])
            self.DownloadArtTimer.name = "DownloadArtTimer"
            self.DownloadArtTimer.start()
            # Sleep between Download, keeps cpu usage down and reduces the number of simultaneous threads.
            # xbmc.sleep(15000)
            xbmc.sleep(100)
        except:
            pass
            
                       
    def DownloadArt_Thread(self, data):
        self.log('DownloadArt_Thread')
        if getProperty("PseudoTVRunning") == "True":   
            type = data[0]
            id = data[1]
            arttype = data[2]
            arttype_fallback = data[3]
            cachefile = data[4]
            chname = data[5]
            mpath = data[6]
            arttypeEXT = data[7]
            
            # print cachefile
            drive, Dpath = os.path.splitdrive(cachefile)
            path, filename = os.path.split(Dpath)
            # print drive, Dpath, path, filename

            if not FileAccess.exists(os.path.join(drive,path)):
                FileAccess.makedirs(os.path.join(drive,path))   
                    
            if type == 'tvshow':
                self.logDebug('DownloadArt_Thread, tvshow')
                FanTVDownload = True
                TVFilePath = cachefile
                tvdb_Types = ['banner', 'fanart', 'folder', 'poster']
                    
                try:
                    if arttype in tvdb_Types:
                        self.logDebug('DownloadArt_Thread, TVDB')
                        arttype = arttype.replace('banner', 'graphical').replace('folder', 'poster')
                        tvdb = str(self.tvdbAPI.getBannerByID(id, arttype))
                        tvdbPath = tvdb.split(', ')[0].replace("[('", "").replace("'", "") 
                        if tvdbPath.startswith('http'):
                            requestDownload(tvdbPath,TVFilePath)
                            FanTVDownload = False
                except Exception,e:
                    self.log('DownloadArt_Thread, self.tvdbAPI Failed!')
                    pass
                    
                if FanTVDownload == True:
                    self.logDebug('DownloadArt_Thread, Fanart.TV')
                    try:
                        arttype = arttype.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'landscape')
                        fan = str(self.fanarttv.get_image_list_TV(id))
                        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(fan)
                        pref_language = self.fanarttv.get_abbrev(REAL_SETTINGS.getSetting('limit_preferred_language'))
                        
                        for f in file_detail:
                            languages = re.search("'language' *: *(.*?),", f)
                            art_types = re.search("'art_type' *: *(.*?),", f)
                            fanPaths = re.search("'url' *: *(.*?),", f)       
                            if languages and len(languages.group(1)) > 0:
                                language = (languages.group(1)).replace("u'",'').replace("'",'')
                                if language == pref_language:
                                    if art_types and len(art_types.group(1)) > 0:
                                        art_type = art_types.group(1).replace("u'",'').replace("'",'').replace("[",'').replace("]",'')
                                        if art_type.lower() == arttype.lower():
                                            if fanPaths and len(fanPaths.group(1)) > 0:
                                                fanPath = fanPaths.group(1).replace("u'",'').replace("'",'')
                                                if fanPath.startswith('http'):
                                                    requestDownload(fanPath,TVFilePath)
                                                    break 
                    except:
                        pass
                    
            elif type == 'movie':
                self.logDebug('DownloadArt_Thread, movie')
                FanMovieDownload = True
                MovieFilePath = cachefile
                tmdb_Types = ['fanart', 'folder', 'poster']
                
                try:
                    if arttype in tmdb_Types:
                        self.logDebug('DownloadArt_Thread, TMDB')
                        arttype = arttype.replace('folder', 'poster')
                        tmdb = self.tmdbAPI.get_image_list(id)
                        data = str(tmdb).replace("[", "").replace("]", "").replace("'", "")
                        data = data.split('}, {')
                        tmdbPath = str([s for s in data if arttype in s]).split("', 'width: ")[0]
                        match = re.search('url *: *(.*?),', tmdbPath)
                        tmdbPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                        if tmdbPath.startswith('http'):
                            requestDownload(tmdbPath,MovieFilePath)
                            FanMovieDownload = False
                except Exception,e:
                    self.logDebug('DownloadArt_Thread, self.tmdbAPI Failed!')
                    pass

                if FanMovieDownload == True:
                    self.logDebug('DownloadArt_Thread, Fanart.TV')
                    try:
                        arttype = arttype.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'landscape')
                        fan = str(self.fanarttv.get_image_list_Movie(id))
                        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(fan)
                        # print file_detail
                        pref_language = self.fanarttv.get_abbrev(REAL_SETTINGS.getSetting('limit_preferred_language'))
                        
                        for f in file_detail:
                            languages = re.search("'language' *: *(.*?),", f)
                            art_types = re.search("'art_type' *: *(.*?),", f)
                            fanPaths = re.search("'url' *: *(.*?),", f)    
                            if languages and len(languages.group(1)) > 0:
                                language = (languages.group(1)).replace("u'",'').replace("'",'')
                                if language == pref_language:
                                    if art_types and len(art_types.group(1)) > 0:
                                        art_type = art_types.group(1).replace("u'",'').replace("'",'').replace("[",'').replace("]",'')
                                        if art_type.lower() == arttype.lower():
                                            if fanPaths and len(fanPaths.group(1)) > 0:
                                                fanPath = fanPaths.group(1).replace("u'",'').replace("'",'')
                                                # print fanPath
                                                if fanPath.startswith('http'):
                                                    requestDownload(fanPath,MovieFilePath)
                                                    break                            
                    except:
                        pass
            try:
                if not FileAccess.exists(cachefile):    
                    if arttype == arttype_fallback:
                        print 'No Art Downloaded'
                        # FileAccess.copy(self.SetDefaultArt_NEW(chname, mpath, arttypeEXT), cachefile)
                    else:
                        self.DownloadArt(type, id, arttype_fallback, arttype_fallback, cachefile, chname, mpath, arttypeEXT)
            except:
                pass

            
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
        

    def Fanart_Download(self, type, arttype, id, FilePath):
        try:
            if type == 'tvshow':
                arttype = arttype.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'landscape')
                fan = str(self.fanarttv.get_image_list_TV(id))
                file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(fan)
                pref_language = self.fanarttv.get_abbrev(REAL_SETTINGS.getSetting('limit_preferred_language'))
                
                for f in file_detail:
                    languages = re.search("'language' *: *(.*?),", f)
                    art_types = re.search("'art_type' *: *(.*?),", f)
                    fanPaths = re.search("'url' *: *(.*?),", f)       
                    if languages and len(languages.group(1)) > 0:
                        language = (languages.group(1)).replace("u'",'').replace("'",'')
                        if language == pref_language:
                            if art_types and len(art_types.group(1)) > 0:
                                art_type = art_types.group(1).replace("u'",'').replace("'",'').replace("[",'').replace("]",'')
                                if art_type.lower() == arttype.lower():
                                    if fanPaths and len(fanPaths.group(1)) > 0:
                                        fanPath = fanPaths.group(1).replace("u'",'').replace("'",'')
                                        if fanPath.startswith('http'):
                                            requestDownload(fanPath,FilePath)
                                            break 
        except:
            pass 

            
#logo parser
class lsHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.icon_rel_url_list=[]
 
    def handle_starttag(self, tag, attrs):
        if tag == "img":
            for pair in attrs:
                if pair[0]=="src" and pair[1].find("/logo/")!=-1:
                    self.icon_rel_url_list.append(pair[1])
        
    def retrieve_icons_avail(self, region):
        if Cache_Enabled:
            print ("retrieve_icons_avail Cache")
            try:
                result = parsers.cacheFunction(self.retrieve_icons_avail_NEW, region)
            except:
                print ("retrieve_icons_avail Cache Failed Forwarding to retrieve_icons_avail_NEW")
                result = self.retrieve_icons_avail_NEW(region)
                pass
        else:
            print ("retrieve_icons_avail Cache Disabled")
            result = self.retrieve_icons_avail_NEW(region)
        if not result:
            result = []
        return result
        
    def retrieve_icons_avail_NEW(self, region):
        print 'retrieve_icons_avail'
        lyngsat_sub_page="http://www.lyngsat-logo.com/tvcountry/%s_%d.html"
        results={}
        URL = 'http://www.lyngsat-logo.com/tvcountry/%s.html' % region
        opener = urllib.FancyURLopener({})
        f = opener.open(URL)
        page_contents=f.read()
        f.close()
        parser=lsHTMLParser()
        parser.feed(page_contents)
        for icon_rel_url in parser.icon_rel_url_list:
                icon_abs_url=urlparse.urljoin(lyngsat_sub_page, icon_rel_url)
                icon_name=os.path.splitext(os.path.basename(icon_abs_url))[0].upper()
                results[icon_name]=icon_abs_url
        return results

    def retrieve_icon(self, chname, region='us'):
        print 'retrieve_icon'
        try:
            file_detail = str(self.retrieve_icons_avail(region))
            file_detail = file_detail.replace("{'",'').replace("'}",'').replace("': '","|")
            file_detail = file_detail.split("', '")

            for f in range(len(file_detail)):
                file = (file_detail[f]).replace('HD','')
                name = file.split('|')[0]
                link = file.split('|')[1]
                match = (name.replace('_',' '))
                match1 = (name.replace('_',' ')).rsplit(' ',1)[0].replace(' TV','').replace(' US','').replace(' HD','')
                match2 = (name.replace('_',' ')).rsplit(' ',2)[0].replace(' TV','').replace(' US','').replace(' HD','')
                match3 = (name.replace('_',' ')).rsplit(' ',3)[0].replace(' TV','').replace(' US','').replace(' HD','')
                match4 = (name.replace('_',' ')).rsplit(' ',3)[0].replace(' TV','').replace(' US','').replace(' HD','')+'-TV'
                match5 = 'W'+(name.replace('_',' ')).rsplit(' ',1)[0].replace(' TV','').replace(' US','').replace(' HD','')

                print match, match1, match2, match3, match4, match5

                if chname.lower() == match.lower():
                    return link
                elif chname.lower() == match1.lower():
                    return link
                elif chname.lower() == match2.lower():
                    return link
                elif chname.lower() == match3.lower():
                    return link
                elif chname.lower() == match4.lower():
                    return link
                elif chname.lower() == match5.lower():
                    return link
        except:
            pass