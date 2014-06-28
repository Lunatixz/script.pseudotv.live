#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2011-2014 Tommy Winther, Lunatixz, Martijn Kaijser
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

#import modules
import sys
import urllib
from operator import itemgetter
from Globals import *

#import modules
import socket
import xbmc
import xbmcgui
import unicodedata
import urllib2

# Use json instead of simplejson when python v2.7 or greater
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

# import libraries
from urllib2 import HTTPError, URLError
from language import *

# Cache bool
CACHE_ON = True

API_KEY = FANARTTV_API_KEY
API_URL_TV = 'http://api.fanart.tv/webservice/series/%s/%s/json/all/1/2'
API_URL_MOVIE = 'http://api.fanart.tv/webservice/movie/%s/%s/json/all/1/2/'

IMAGE_TYPES = ['clearlogo',
               'hdtvlogo',
               'clearart',
               'hdclearart',
               'tvthumb',
               'characterart',
               'tvbanner',
               'movielogo',
               'hdmovielogo',
               'movieart',
               'moviedisc',
               'hdmovieclearart',
               'moviethumb',
               'moviebanner']

               
# Retrieve JSON data from cache function
def get_data(url, data_type ='json'):
    xbmc.log('script.pseudotv.live-fanarttv: get_data')
    #log('API: %s'% url)
    if CACHE_ON:
        result = parsers.cacheFunction(get_data_new, url, data_type)
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


def get_image_list_TV(media_id):
    xbmc.log('script.pseudotv.live-fanarttv: get_image_list_TV')
    try:
        data = get_data(API_URL_TV%(API_KEY,media_id), 'json')
        image_list = []
        if data == 'Empty' or not data:
            return image_list
        else:
            # split 'name' and 'data'
            for title, value in data.iteritems():
                for art in IMAGE_TYPES:
                    if value.has_key(art):
                        for item in value[art]:
                            # Check on what type and use the general tag
                            arttypes = {'clearlogo': 'clearlogo',
                                        'hdtvlogo': 'clearlogo',
                                        'clearart': 'clearart',
                                        'hdclearart': 'clearart',
                                        'tvthumb': 'landscape',
                                        'characterart': 'characterart',
                                        'tvbanner': 'banner',
                                        }
                            if art in ['hdtvlogo', 'hdclearart']:
                                size = 'HD'
                            elif art in ['clearlogo', 'clearart']:
                                size = 'SD'
                            else:
                                size = ''
                            generalinfo = '%s: %s  |  ' %( 'Language', get_language(item.get('lang')).capitalize())
                            # Fill list
                            image_list.append({'url': urllib.quote(item.get('url'), ':/'),
                                               'preview': item.get('url') + '/preview',
                                               'id': item.get('id'),
                                               'art_type': [arttypes[art]],
                                               'size': size,
                                               'language': item.get('lang','en'),
                                               'votes': int(item.get('likes')),
                                               'generalinfo': generalinfo})
            if image_list == []:
                raise
            else:
                # Sort the list before return. Last sort method is primary
                image_list = sorted(image_list, key=itemgetter('votes'), reverse=True)
                image_list = sorted(image_list, key=itemgetter('size'), reverse=False)
                image_list = sorted(image_list, key=itemgetter('language'))
                return image_list
    except:
        pass

def get_image_list_Movie( media_id):
    xbmc.log('script.pseudotv.live-fanarttv: get_image_list_Movie')
    try:
        data = get_data(API_URL_MOVIE%(API_KEY, media_id), 'json')
        image_list = []
        if data == 'Empty' or not data:
            return image_list
        else:
            # split 'name' and 'data'
            for title, value in data.iteritems():
                for art in IMAGE_TYPES:
                    if value.has_key(art):
                        for item in value[art]:
                            # Check on what type and use the general tag
                            arttypes = {'movielogo': 'clearlogo',
                                        'moviedisc': 'discart',
                                        'movieart': 'clearart',
                                        'hdmovielogo': 'clearlogo',
                                        'hdmovieclearart': 'clearart',
                                        'moviebanner': 'banner',
                                        'moviethumb': 'landscape'}
                            if art in ['hdmovielogo', 'hdmovieclearart']:
                                size = 'HD'
                            elif art in ['movielogo', 'movieart']:
                                size = 'SD'
                            else:
                                size = ''
                            generalinfo = '%s: %s  |  ' %( 'Language', get_language(item.get('lang')).capitalize())
                            # Fill list
                            image_list.append({'url': urllib.quote(item.get('url'), ':/'),
                                               'preview': item.get('url') + '/preview',
                                               'id': item.get('id'),
                                               'art_type': [arttypes[art]],
                                               'size': size,
                                               'language': item.get('lang','en'),
                                               'votes': int(item.get('likes')),
                                               'disctype': item.get('disc_type','n/a'),
                                               'discnumber': item.get('disc','n/a'),
                                               'generalinfo': generalinfo})
            if image_list == []:
                raise
            else:
                # Sort the list before return. Last sort method is primary
                image_list = sorted(image_list, key=itemgetter('votes'), reverse=True)
                image_list = sorted(image_list, key=itemgetter('size'), reverse=False)
                image_list = sorted(image_list, key=itemgetter('language'))
                return image_list
    except:
        pass