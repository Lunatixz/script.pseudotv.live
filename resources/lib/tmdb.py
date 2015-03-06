#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2011-2014 Tommy Winther, Kevin S. Graer, Martijn Kaijser
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
import urllib, urllib2
import xbmc, sys, re
#import modules
import socket
import xbmc
import xbmcgui
import unicodedata

# Use json instead of simplejson when python v2.7 or greater
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

# import libraries
from urllib2 import HTTPError, URLError
from language import *
# import libraries
from operator import itemgetter
from Globals import *

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

### Cache bool
CACHE_ON = True

class TMDB(object):
    def __init__(self, api_key='078845CE15BC08A7'):
        self.apikey = api_key
        self.baseurl = 'http://api.themoviedb.org/3'
        try:
            self.imagebaseurl = self._getPosterBaseUrl()
        except Exception,e:
            pass

    def __repr__(self):
        return 'TMDB(apikey=%s, baseurl=%s, imagebaseurl=%s)' % (self.apikey,self.baseurl,self.imagebaseurl)
        
    def _buildUrl(self, cmd, parms={}):
        # try:
        parmsCopy = parms.copy()
        parmsCopy.update({'api_key' : self.apikey})
        url = '%s/%s?%s' % (self.baseurl, cmd, urllib.urlencode(parmsCopy))
        #self.xbmc.log(url)
        return url
        # except:
            # pass

    # def _getPosterBaseUrl(self):
        # response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('configuration'), headers={"Accept": "application/json"})).read())
        # #self.xbmc.log('Response: \r\n%s' % response)
        # return response['images']['base_url']

    # def getPosterUrl(self, filename):
        # return '%s%s%s' % (self.imagebaseurl, 'w92/', filename)

    def getMovie(self, movieName, year):
        if CACHE_ON:
            try:
                result = parserTMDB.cacheFunction(self.getMovie_NEW, movieName, year)
            except:
                result = self.getMovie_NEW(movieName, year)
                pass                
        else:
            result = self.getMovie_NEW(movieName, year)
        if not result:
            result = 0
        return result 

    def getMovie_NEW(self, movieName, year):
        #self.xbmc.log('movieName: %s' % movieName)
        try:
            response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('search/movie', {'query' : movieName, 'year' : year}), headers={"Accept": "application/json"})).read())
            if response['total_results'] > 0:
                #self.xbmc.log('Response: \r\n%s' % response)
                response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('movie/%s' % (response['results'][0]['id'])), headers={"Accept": "application/json"})).read())
            else:
                #self.xbmc.log('No matches found for %s' % movieName)
                response = json.loads('{"imdb_id":"", "poster_path":""}')
            #print response
        except:
            response = ''
            pass
        return response
        
    def getMPAA(self, imdbid):
        if CACHE_ON:
            try:
                result = parserTMDB.cacheFunction(self.getMPAA_NEW, imdbid)
            except:
                result = self.getMPAA_NEW(imdbid)
                pass               
        else:
            result = self.getMPAA_NEW(imdbid)
        if not result:
            result = 'NA'
        return result 
        
    def getMPAA_NEW(self, imdbid):
        response = str(json.loads(urllib2.urlopen(urllib2.Request('https://api.themoviedb.org/3/movie/'+imdbid+'/releases?api_key='+self.apikey+'&language=en', headers={"Accept": "application/json"})).read()))
        response = response.split("certification': u'")[1]
        response = response.split("'}")[0]
        return response
        
    def getIMDBId(self, movieName, year):
        response = self.getMovie(movieName, year)
        return response['imdb_id']

    def getPlot(self, movieName, year):
        response = self.getMovie(movieName, year)
        return response['overview']

    def getTagline(self, movieName, year):
        response = self.getMovie(movieName, year)
        return response['tagline']

    def getGenre(self, movieName, year):
        response = self.getMovie(movieName, year)
        return response['genres']

    def get_image_list(self, media_id):
        log('Downloader: get_image_list, ' + str(media_id))
        API_KEY = TMDB_API_KEY
        API_URL = 'http://api.themoviedb.org/3/movie/'+media_id+'/images?api_key='+API_KEY
        log('Downloader: API_URL = ' + str(API_URL))
        BASE_IMAGEURL = "http://d3gtl9l2a4fn1j.cloudfront.net/t/p/"

        data = self.get_data(API_URL, 'json')
        log('Downloader: data = ' + str(data))
        image_list = []
        if data == "Empty" or not data:
            return image_list
        else:
            # Get fanart
            try:
                for item in data['backdrops']:
                    if int(item.get('vote_count')) >= 1:
                        rating = float( "%.1f" % float( item.get('vote_average'))) #output string with one decimal
                        votes = item.get('vote_count','n/a')
                    else:
                        rating = 'n/a'
                        votes = 'n/a'
                    image_list.append({'url': BASE_IMAGEURL + 'original' + item['file_path'],
                                       'preview': BASE_IMAGEURL + 'w300' + item['file_path'],
                                       'id': item.get('file_path').lstrip('/').replace('.jpg', ''),
                                       'art_type': ['fanart','extrafanart'],
                                       'height': item.get('height'),
                                       'width': item.get('width'),
                                       'language': item.get('iso_639_1','n/a'),
                                       'rating': rating,
                                       'votes': votes,
                                       'generalinfo': ('%s: %s  |  %s: %s  |  %s: %s  |  %s: %sx%s  |  ' 
                                                        %( "Language", get_language(item.get('iso_639_1','n/a')).capitalize(),
                                                           "Rating", rating,
                                                           "Votes", votes,
                                                           "Size", item.get('width'), item.get('height')))})
            except Exception, e:
                xbmc.log( 'Problem report: %s' %str( e ), xbmc.LOGNOTICE )
            # Get thumbs
            try:
                for item in data['backdrops']:
                    if int(item.get('vote_count')) >= 1:
                        rating = float( "%.1f" % float( item.get('vote_average'))) #output string with one decimal
                        votes = item.get('vote_count','n/a')
                    else:
                        rating = 'n/a'
                        votes = 'n/a'
                    # Fill list
                    image_list.append({'url': BASE_IMAGEURL + 'w780' + item['file_path'],
                                       'preview': BASE_IMAGEURL + 'w300' + item['file_path'],
                                       'id': item.get('file_path').lstrip('/').replace('.jpg', ''),
                                       'art_type': ['extrathumbs'],
                                       'height': item.get('height'),
                                       'width': item.get('width'),
                                       'language': item.get('iso_639_1','n/a'),
                                       'rating': rating,
                                       'votes': votes,
                                       'generalinfo': ('%s: %s  |  %s: %s  |  %s: %s  |  %s: %sx%s  |  ' 
                                                       %( "Language", get_language(item.get('iso_639_1','n/a')).capitalize(),
                                                          "Rating", rating,
                                                          "Votes", votes,
                                                          "Size", item.get('width'), item.get('height')))})
            except Exception, e:
                xbmc.log( 'Problem report: %s' %str( e ), xbmc.LOGNOTICE )
            # Get posters
            try:
                for item in data['posters']:
                    if int(item.get('vote_count')) >= 1:
                        rating = float( "%.1f" % float( item.get('vote_average'))) #output string with one decimal
                        votes = item.get('vote_count','n/a')
                    else:
                        rating = 'n/a'
                        votes = 'n/a'
                    # Fill list
                    image_list.append({'url': BASE_IMAGEURL + 'original' + item['file_path'],
                                       'preview': BASE_IMAGEURL + 'w185' + item['file_path'],
                                       'id': item.get('file_path').lstrip('/').replace('.jpg', ''),
                                       'art_type': ['poster'],
                                       'height': item.get('height'),
                                       'width': item.get('width'),
                                       'language': item.get('iso_639_1','n/a'),
                                       'rating': rating,
                                       'votes': votes,
                                       'generalinfo': ('%s: %s  |  %s: %s  |  %s: %s  |  %s: %sx%s  |  ' 
                                                       %( "Language", get_language(item.get('iso_639_1','n/a')).capitalize(),
                                                          "Rating", rating,
                                                          "Votes", votes,
                                                          "Size", item.get('width'), item.get('height')))})
            except Exception, e:
                xbmc.log( 'Problem report: %s' %str( e ), xbmc.LOGNOTICE )
            if image_list == []:
                pass
            else:
                # Sort the list before return. Last sort method is primary
                image_list = sorted(image_list, key=itemgetter('rating'), reverse=True)
                image_list = sorted(image_list, key=itemgetter('language'))
                return image_list

                
    def _search_movie(medianame,year=''):
        medianame = normalize_string(medianame)
        xbmc.log('TMDB API search criteria: Title[''%s''] | Year[''%s'']' % (medianame,year) )
        illegal_char = ' -<>:"/\|?*%'
        for char in illegal_char:
            medianame = medianame.replace( char , '+' ).replace( '++', '+' ).replace( '+++', '+' )

        search_url = 'http://api.themoviedb.org/3/search/movie?query=%s+%s&api_key=%s' %( medianame, year, API_KEY )
        tmdb_id = ''
        xbmc.log('TMDB API search:   %s ' % search_url)
        try:
            data = get_data(search_url, 'json')
            if data == "Empty":
                tmdb_id = ''
            else:
                for item in data['results']:
                    if item['id']:
                        tmdb_id = item['id']
                        break
        except Exception, e:
            xbmc.log( str( e ), xbmc.LOGERROR )
        if tmdb_id == '':
            xbmc.log('TMDB API search found no ID')
        else:
            xbmc.log('TMDB API search found ID: %s' %tmdb_id)
        return tmdb_id


    # Retrieve JSON data from cache function
    def get_data(self, url, data_type ='json'):
        log('Downloader: get_data - Cache')
        if CACHE_ON:
            try:
                result = parserTMDB.cacheFunction(self.get_data_new, url, data_type)
            except:
                result = self.get_data_new(url, data_type)
                pass
        else:
            result = self.get_data_new(url, data_type)
        if not result:
            result = 'Empty'
            
        log('Downloader: result = ' + str(result))
        return result

    # Retrieve JSON data from site
    def get_data_new(self, url, data_type):
        log('Downloader: get_data_new - Cache expired. Retrieving new data')
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
        except Exception,e:
            data = 'Empty'
            
        log('Downloader: data = ' + str(data))
        return data


