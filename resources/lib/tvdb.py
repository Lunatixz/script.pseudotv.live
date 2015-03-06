#
#      Copyright (C) 2013 Tommy Winther, Kevin S. Graer, Martijn Kaijser
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
#import modules
import sys, re
import urllib, urllib2

#import modules
import socket
import xbmc
import xbmcgui
import unicodedata
# import libraries
from urllib2 import HTTPError, URLError
from language import *
# Use json instead of simplejson when python v2.7 or greater
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json
    
from Globals import *
from xml.etree import ElementTree as ET

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

### Cache bool
CACHE_ON = True

class TVDB(object):
    def __init__(self, api_key='9c47d05a3f5f3a00104f6586412306af'):
        self.apikey = api_key
        self.baseurl = 'http://thetvdb.com'
    
    def __repr__(self):
        return 'TVDB(baseurl=%s, apikey=%s)' % (self.baseurl, self.apikey)

    def _buildUrl(self, cmd, parms={}):
        url = '%s/api/%s?%s' % (self.baseurl, cmd, urllib.urlencode(parms))
        #xbmc.log(url)
        return url

    def getIdByZap2it(self, zap2it_id):
        xbmc.log("getIdByZap2it Cache")
        if CACHE_ON:
            result = parserTVDB.cacheFunction(self.getIdByZap2it_NEW, zap2it_id)
        else:
            result = self.getIdByZap2it_NEW(zap2it_id)
        if not result:
            result = 'Empty'
        return result    

    def getIdByZap2it_NEW(self, zap2it_id):
        xbmc.log("getIdByZap2it Creating Cache")
        try:
            response = urllib2.urlopen(self._buildUrl('GetSeriesByRemoteID.php', {'zap2it' : zap2it_id})).read()
            tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
            match = tvdbidRE.search(response)
            if match:
                return match.group(1)
            else:
                return 'Empty'
        except Exception,e:
            return 'Empty'

    def getIdByIMDB(self, imdb_id):
        xbmc.log("getIdByIMDB Cache")
        if CACHE_ON:
            result = parserTVDB.cacheFunction(self.getIdByIMDB_NEW, imdb_id)
        else:
            result = self.getIdByIMDB_NEW(imdb_id)
        if not result:
            result = 'Empty'
        return result    

    def getIdByIMDB_NEW(self, imdb_id):
        xbmc.log("getIdByIMDB Creating Cache")
        try:
            response = urllib2.urlopen(self._buildUrl('GetSeriesByRemoteID.php', {'apikey' : self.apikey, 'imdbid' : imdb_id})).read()
            imdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
            match = imdbidRE.search(response)

            if match:
                return match.group(1)
            else:
                return 'Empty'
        except Exception,e:
            return 'Empty'

    def getEpisodeByAirdate(self, tvdbid, airdate):
        xbmc.log("getEpisodeByAirdate Cache")
        if CACHE_ON:
            result = parserTVDB.cacheFunction(self.getEpisodeByAirdate_NEW, tvdbid, airdate)
        else:
            result = self.getEpisodeByAirdate_NEW(tvdbid, airdate)
        if not result:
            result = 'Empty'
        return result    

    def getEpisodeByAirdate_NEW(self, tvdbid, airdate):
        xbmc.log("getEpisodeByAirdate Creating Cache")
        try:
            response = urllib2.urlopen(self._buildUrl('GetEpisodeByAirDate.php', {'apikey' : self.apikey, 'seriesid' : tvdbid, 'airdate' : airdate})).read()
            return response
        except Exception,e:
            return ''

    def getEpisodeByID(self, tvdbid):
        xbmc.log("getIdByIMDB Cache")
        if CACHE_ON:
            result = parserTVDB.cacheFunction(self.getEpisodeByID_NEW, tvdbid)
        else:
            result = self.getEpisodeByID_NEW(tvdbid)
        if not result:
            result = 'Empty'
        return result    

    def getEpisodeByID_NEW(self, tvdbid):
        xbmc.log("getEpisodeByID_NEW Creating Cache")
        try:
            response = urllib2.urlopen(self._buildUrl(self.apikey + '/series/' + tvdbid + '/all/en.xml')).read()
            return response
        except Exception,e:
            return ''

    def getIdByShowName(self, showName):
        xbmc.log("getIdByShowName Cache")
        if CACHE_ON:
            try:
                result = parserTVDB.cacheFunction(self.getIdByShowName_NEW, showName)
            except:
                result = self.getIdByShowName_NEW(showName)
                pass
        else:
            result = self.getIdByShowName_NEW(showName)
        if not result:
            result = 'Empty'
        return result    

    def getIdByShowName_NEW(self, showName):
        xbmc.log("getIdByShowName Creating Cache")
        try:
            #NOTE: This assumes an exact match. It is possible to get multiple results though. This could be smarter
            response = urllib2.urlopen(self._buildUrl('GetSeries.php', {'seriesname' : showName})).read()
            tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
            match = tvdbidRE.search(response)
            if match:
                return match.group(1)
            else:
                return 'Empty'
        except Exception,e:
            return 'Empty'

    def getBannerByID(self, tvdbid, type):
        xbmc.log("getIdByZap2it Cache")
        if CACHE_ON:
            result = parserTVDB.cacheFunction(self.getBannerByID_NEW, tvdbid, type)
        else:
            result = self.getBannerByID_NEW(tvdbid, type)
        if not result:
            result = 'Empty'
        return result    

    def getBannerByID_NEW(self, tvdbid, type):
        log('Downloader: getBannerByID')
        try:
            response = urllib2.urlopen(self._buildUrl(self.apikey + '/series/' + tvdbid + '/banners.xml'))
            log('Downloader: response = ' + str(response))
            tree = ET.parse(response)
            images = []
            banner_data = tree.find("Banners")
            banner_nodes = tree.getiterator("Banner")
            for banner in banner_nodes:
                banner_path = banner.findtext("BannerPath")
                banner_type = banner.findtext("BannerType")
                banner_type2 = banner.findtext("BannerType2")
                if banner_type == 'season':
                    banner_season = banner.findtext("Season")
                else:
                    banner_season = ''
                banner_url = "%s/banners/%s" % ('http://www.thetvdb.com', banner_path)
                if type in banner_path:
                    images.append((banner_url, banner_type, banner_type2, banner_season))
                    break
                # else:
                    # images.append((banner_url, banner_type, banner_type2, banner_season))
            return images
        except Exception,e:
            return 'Empty'

    def getIMDBbyShowName(self, showName):
        xbmc.log("getIMDBbyShowName Cache")
        if CACHE_ON:
            try:
                result = parserTVDB.cacheFunction(self.getIMDBbyShowName_NEW, showName)
            except:
                result = self.getIMDBbyShowName_NEW(showName)
                pass
        else:
            result = self.getIMDBbyShowName_NEW(showName)
        if not result:
            result = 'Empty'
        return result    

    def getIMDBbyShowName_NEW(self, showName):
        xbmc.log("getIMDBbyShowName Creating Cache")
        try:
            #NOTE: This assumes an exact match. It is possible to get multiple results though. This could be smarter
            response = urllib2.urlopen(self._buildUrl('GetSeries.php', {'seriesname' : showName})).read()
            tvdbidRE = re.compile('<IMDB_ID>(.+?)</IMDB_ID>', re.DOTALL)
            match = tvdbidRE.search(response)
            if match:
                return match.group(1)
            else:
                return 'Empty'
        except Exception,e:
            return 'Empty'

    def get_image_list(self, media_id, mode):
        image_list = []
        data = get_data(API_URL%(self.api_key, media_id), 'xml')
        try:
            tree = ET.fromstring(data)
            for image in tree.findall('Banner'):
                info = {}
                if image.findtext('BannerPath'):
                    info['url'] = self.url_prefix + image.findtext('BannerPath')
                    if image.findtext('ThumbnailPath'):
                        info['preview'] = self.url_prefix + image.findtext('ThumbnailPath')
                    else:
                        info['preview'] = self.url_prefix + image.findtext('BannerPath')
                    info['language'] = image.findtext('Language')
                    info['id'] = image.findtext('id')
                    # process fanarts
                    if image.findtext('BannerType') == 'fanart':
                        info['art_type'] = ['fanart','extrafanart']
                    # process posters
                    elif image.findtext('BannerType') == 'poster':
                        info['art_type'] = ['poster']
                    # process banners
                    elif image.findtext('BannerType') == 'series' and image.findtext('BannerType2') == 'graphical':
                        info['art_type'] = ['banner']
                    # process seasonposters
                    elif image.findtext('BannerType') == 'season' and image.findtext('BannerType2') == 'season':
                        info['art_type'] = ['seasonposter']
                    # process seasonbanners
                    elif image.findtext('BannerType') == 'season' and image.findtext('BannerType2') == 'seasonwide':
                        info['art_type'] = ['seasonbanner']
                    else:
                        info['art_type'] = ['']
                    # convert image size ...x... in Bannertype2
                    if image.findtext('BannerType2'):
                        try:
                            x,y = image.findtext('BannerType2').split('x')
                            info['width'] = int(x)
                            info['height'] = int(y)
                        except:
                            info['type2'] = image.findtext('BannerType2')

                    # check if fanart has text
                    info['series_name'] = image.findtext('SeriesName') == 'true'

                    # find image ratings
                    if int(image.findtext('RatingCount')) >= 1:
                        info['rating'] = float( "%.1f" % float( image.findtext('Rating')) ) #output string with one decimal
                        info['votes'] = image.findtext('RatingCount')
                    else:
                        info['rating'] = 'n/a'
                        info['votes'] = 'n/a'

                    # find season info
                    if image.findtext('Season'):
                        info['season'] = image.findtext('Season')
                    else:
                        info['season'] = 'n/a'

                    # Create Gui string to display
                    info['generalinfo'] = '%s: %s  |  ' %( 'Language', get_language(info['language']).capitalize())
                    if info['season'] != 'n/a':
                        info['generalinfo'] += '%s: %s  |  ' %( 'Season', info['season'] )
                    if 'height' in info:
                        info['generalinfo'] += '%s: %sx%s  |  ' %( 'Size', info['height'], info['width'] )
                    info['generalinfo'] += '%s: %s  |  %s: %s  |  ' %( 'Rating', info['rating'], 'Votes', info['votes'] )

                if info:
                    image_list.append(info)
        except:
            raise NoFanartError(media_id)
        if image_list == []:
            raise NoFanartError(media_id)
        else:
            # Sort the list before return. Last sort method is primary
            image_list = sorted(image_list, key=itemgetter('rating'), reverse=True)
            image_list = sorted(image_list, key=itemgetter('season'))
            image_list = sorted(image_list, key=itemgetter('language'))
            return image_list
            
    # Retrieve JSON data from cache function
    def get_data(url, data_type ='json'):
        xbmc.log('script.pseudotv.live-fanarttv: get_data')
        if CACHE_ON:
            result = parserFANTV.cacheFunction(get_data_new, url, data_type)
        else:
            result = get_data_new(url, data_type)
        if not result:
            result = 'Empty'
        return result


    # Retrieve JSON data from site
    def get_data_new(url, data_type):
        #log('Cache expired. Retrieving new data')
        data = []
        try:
            request = urllib2.Request(url)
            # TMDB needs a header to be able to read the data
            if url.startswith("http://api.themoviedb.org"):
                request.add_header("Accept", "application/json")
            req = urllib2.urlopen(request)
            if data_type == 'json':
                data = json.loads(req.read())
                if not data:
                    data = 'Empty'
            else:
                data = req.read()
            req.close()
        except HTTPError, e:
            if e.code == 400:
                raise HTTP400Error(url)
            elif e.code == 404:
                raise HTTP404Error(url)
            elif e.code == 503:
                raise HTTP503Error(url)
            else:
                raise DownloadError(str(e))
        except URLError:
            raise HTTPTimeout(url)
        except socket.timeout, e:
            raise HTTPTimeout(url)
        except:
            data = 'Empty'
        return data