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
import time, datetime, random
import datetime
import sys, re
import random, traceback
import urllib, urllib2, urlparse
import fanarttv
import socket
socket.setdefaulttimeout(30)

from ChannelList import *
from Globals import *
from FileAccess import FileLock, FileAccess
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
    

class Artdownloader:

    def log(self, msg, level = xbmc.LOGDEBUG):
        log('Artdownloader: ' + msg, level)

    
    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if DEBUG == 'true':
            log('Artdownloader: ' + msg, level)
    
    
    def JsonArtwork(self, mpath, media='video'):
        print ('JsonArtwork')
        file_detail = []
        try:
            chanlist = ChannelList()
            json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"%s","properties":["art"]},"id":10}' % (chanlist.escapeDirJSON(mpath), media))
            json_folder_detail = chanlist.sendJSON(json_query)
            file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
            print ('JsonArtwork - return')
        except:
            pass
        return file_detail

        
    def LocalArtwork(self, path, type, arttype):
        print ('LocalArtwork')
        arttype = arttype.replace('folder','poster').replace('character','characterart').replace('logo','clearlogo').replace('disc','discart')#correct search names
        results = self.JsonArtwork(path)
        arttype = ((type + '.' + arttype if type == 'tvshow' else arttype))
        fletype = ''

        for f in results:
            arttypes = re.search(('"%s" *: *"(.*?)"' % arttype), f)

            if arttypes:
                fletype = (unquote((arttypes.group(1).split(','))[0])).replace('image://','').replace('.jpg/','.jpg').replace('.png/','.png')

            if fletype:
                break 
                
        return fletype
  
  
    def ConvertBug(self, org, mod):
        print 'ConvertBug' 
        org =  xbmc.translatePath(org)
        original = Image.open(org)                  
        converted_img = original.convert('LA')
        converted_img.save(mod)
        return mod
        
        
    def FindBug(self, chtype, chname, mediapath):
        print 'FindBug' 
        print chtype, chname, mediapath
        setImage = ''
        BugName = (chname + '.png')
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

        print 'FindBug return', setImage
        return setImage

        
    def FindLogo(self, chtype, chname, mediapath):
        print 'FindLogo'
        print chtype, chname, mediapath
        found = False
        setImage = ''
        LogoName = (chname + '.png')
        LogoFolder = os.path.join(LOGO_LOC,LogoName)
        self.logoParser = lsHTMLParser()
        
        if FileAccess.exists(LogoFolder):
            print ('Find Local Folder Logo')
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
            print ("FindArtwork Cache")
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
                print ("FindArtwork Cache Failed Forwarding to FindArtwork_NEW")
                result = self.FindArtwork_NEW(type, chtype, chname, id, mediapath, arttypeEXT)
                pass
        else:
            print ("FindArtwork Cache Disabled")
            result = self.FindArtwork_NEW(type, chtype, chname, id, mediapath, arttypeEXT)
        if not result:
            result = 0
        return result
         

    def FindArtwork_NEW(self, type, chtype, chname, id, mediapath, arttypeEXT):
        print ('FindArtwork_NEW')       
        setImage = ''
        arttype = arttypeEXT.split(".")[0]
        fle = id + '-' + arttypeEXT
        smpath = os.path.dirname(mediapath)
        ArtCache = os.path.join(ART_LOC, fle)
        ChannelLogo = os.path.join(LOGO_LOC,chname + '.png')  
        MediaImage = os.path.join(MEDIA_LOC, (arttype + '.png'))
        mediapathSeason, filename = os.path.split(mediapath)
        mediapathSeries = os.path.dirname(mediapathSeason)
        
        if chtype <= 7:
            print ('FindArtwork, Chtype <= 7')
            ###############################
            print ('Find Infolder Artwork')                        
            artSeries = xbmc.translatePath(os.path.join(smpath, arttypeEXT))
            artSeason = xbmc.translatePath(os.path.join(mediapath, arttypeEXT))
        
            if FileAccess.exists(artSeries): 
                setImage = artSeries
            elif FileAccess.exists(artSeason):
                setImage = artSeason
            else:
                print ('Find Infolder Artwork - Fallback')
                arttypeEXT_fallback = arttypeEXT.replace('landscape','fanart')
                artSeries_fallback = xbmc.translatePath(os.path.join(smpath, arttypeEXT_fallback))
                artSeason_fallback = xbmc.translatePath(os.path.join(mediapath, arttypeEXT_fallback))

                if FileAccess.exists(artSeries_fallback): 
                    setImage = artSeries_fallback
                elif FileAccess.exists(artSeason_fallback):
                    setImage = artSeason_fallback
                else:
                    ###########################
                    # print ('Find Json Artwork')
                    arttype_fallback = arttype.replace('landscape','fanart')#add more fallback replacements
                    
                    # setImage = self.LocalArtwork(mediapath, type, arttype)
                    
                    # if not setImage:
                        # print ('Find Json Artwork - Fallback')
                        # setImage = self.LocalArtwork(mediapath, type, arttype_fallback)
                        
                    if not setImage:   
                        if id != '0' and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':
                            print ('Find Artwork Cache')
                            if FileAccess.exists(ArtCache):
                                setImage = ArtCache
                            else:
                                ###########################
                                print ('Find Download Artwork')
                                setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)

                                if not setImage:
                                    print ('Find Download Artwork - Fallback')
                                    setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)

        else:
            print ('FindArtwork, Chtype > 7')
            if id != '0' and REAL_SETTINGS.getSetting('EnhancedGuideData') == 'true':  
                #PseudoTV Artwork Cache
                ###########################
                print ('Find Artwork Cache')
                if FileAccess.exists(ArtCache):
                    setImage = ArtCache
                else:
                    #Download Artwork
                    ###########################
                    print ('Find Artwork Download')
                    setImage = self.DownloadArt(type, id, fle, arttypeEXT, ART_LOC)

                    if not setImage:
                        print ('Find Artwork Download - Fallback')
                        #Download Artwork - Fallback
                        arttype_fallback = arttypeEXT.replace('landscape','fanart')
                        setImage = self.DownloadArt(type, id, fle, arttype_fallback, ART_LOC)
            

        #Plugin/Youtube image, add thumb json todo
        if not setImage:      
            if mediapath.startswith('plugin://'):
                ###########################
                print ('Find Plugin Artwork')
                try:
                    addon = ''
                    plugin = os.path.split(mediapath)
                    addon = os.path.split(plugin[0])[1]
                    YTid = plugin[1]
                    icon = 'special://home/addons/'+YTid+ '/icon.png'
                    fanart = 'special://home/addons/'+YTid+ '/fanart.jpg'
                    youtube = ['plugin.video.bromix.youtube', 'plugin.video.youtube']
                    
                    if addon in youtube:
                        ###########################
                        print ('Find Plugin Artwork - Youtube')
                        setImage = "http://img.youtube.com/vi/"+YTid+"/0.jpg"

                    else:
                        ###########################
                        print ('Find Plugin Artwork - Other')
                        if FileAccess.exists(xbmc.translatePath(icon)):
                            setImage = icon  
                except:
                    pass   
            # elif mediapath.startswith('upnp://') and id == '0':
            # {"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["thumbnail"]},"id":4}

        
        #Default image
        if not setImage:    
            print ('Find Channel Logo Artwork')
            if FileAccess.exists(ChannelLogo):
                setImage = ChannelLogo
            else:
                setImage = THUMB
        
        print 'setImage', setImage
        return setImage
        
                
    def DownloadMetaArt(self, type, fle, id, typeEXT, ART_LOC):
        print ('DownloadMetaArt')
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
        print ('DownloadArt')
        tvdbAPI = TVDB(TVDB_API_KEY)
        tmdbAPI = TMDB(TMDB_API_KEY)     
        
        if not FileAccess.exists(ART_LOC):
            FileAccess.makedirs(ART_LOC)

        ArtType = typeEXT.split('.')[0]        
        setImage = ''
        
        if type.lower() == 'tvshow':
            FanTVDownload = False
            TVFilePath = os.path.join(ART_LOC, fle) 
            tvdb_Types = ['banner', 'fanart', 'folder', 'poster']
            
            if ArtType in tvdb_Types:
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
                ArtType = ArtType.replace('graphical', 'banner').replace('folder', 'poster').replace('fanart', 'tvfanart')
                fan = fanarttv.get_image_list_TV(id)
                try:
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(TVFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return TVFilePath
                except Exception,e:
                    print ('FanTVDownload Failed!') 
                    return ''   

        elif type == 'movie':
            FanMovieDownload = False
            MovieFilePath = os.path.join(ART_LOC, fle)
            tmdb = ['fanart', 'folder', 'poster']
            
            if ArtType in tmdb:
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
                ArtType = ArtType.replace('folder', 'poster').replace('fanart', 'moviefanart')
                fan = fanarttv.get_image_list_Movie(id)
                try:
                    data = str(fan).replace("[", "").replace("]", "").replace("'", "")
                    data = data.split('}, {')
                    fanPath = str([s for s in data if ArtType in s]).split("', 'art_type: ")[0]
                    match = re.search("url *: *(.*?),", fanPath)
                    fanPath = match.group().replace(",", "").replace("url: u", "").replace("url: ", "")
                    resource = urllib.urlopen(fanPath)
                    output = FileAccess.open(MovieFilePath, 'w')
                    output.write(resource.read())
                    output.close()
                    return MovieFilePath
                except Exception,e:
                    print ('FanMovieDownload Failed!')
                    return ''     

                    
    def EXTtype(self, arttype): 
        print ('EXTtype')               
        JPG = ['banner', 'fanart', 'folder', 'landscape', 'poster']
        PNG = ['character', 'clearart', 'logo', 'disc']
        
        if arttype in JPG:
            arttypeEXT = (arttype + '.jpg')
        else:
            arttypeEXT = (arttype + '.png')
        print ('EXTtype = ' + str(arttypeEXT))
        return arttypeEXT
      
 
    def PreArtService(self):
        print 'PreArtService'
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
                                    youtube = ['plugin://plugin.video.bromix.youtube', 'plugin://plugin.video.youtube/?path=/root']
                                    
                                    #Insert Youtube ID for art parsing
                                    if mpath in youtube:
                                        YTid = line.split('id=')[1]
                                        mpath = (mpath + '/' + YTid).replace('/?path=/root','')
                                        
                                    if type and mpath:
                                        newLST = [type, chtype, id, mpath]
                                        ArtLST.append(newLST)
                except:
                    pass
                        
        random.shuffle(ArtLST)
        print 'PreArtService - Total Count - ' + str(len(ArtLST))
        return ArtLST

    
    def ArtService(self):
        print 'ArtService'         
        if REAL_SETTINGS.getSetting("ArtService_Running") == "false":
            REAL_SETTINGS.setSetting('ArtService_Running', "true")
            
            type1EXT = ''
            type2EXT = ''
            start = datetime.datetime.today()
            print 'ArtService_Start = ' + str(start)
            ArtLst = self.PreArtService()
            # self.logoParser = lsHTMLParser()
            # self.logoParser.retrieve_icons_avail()   
            
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
                time.sleep(5)
                
                xbmc.log('script.pseudotv.live-ArtService: ArtCache Purged!')
                REAL_SETTINGS.setSetting('ClearLiveArtCache', "false")
     
                if NOTIFY == 'true':
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Cache Cleared", 4000, THUMB) )
                
            try:
                type1EXT = REAL_SETTINGS.getSetting('type1EXT')
            except:
                pass
            
            try:
                type2EXT = REAL_SETTINGS.getSetting('type2EXT')
            except:
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
            
            stop = datetime.datetime.today()
            finished = stop - start
            MSSG = ("Artwork Spooled in %d seconds" %finished.seconds)
            print str(MSSG)
            
            REAL_SETTINGS.setSetting("ArtService_Running","false")
            REAL_SETTINGS.setSetting("ArtService_LastRun",str(stop))
            
            if NOTIFY == 'true':
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 2000, THUMB) )
    


        