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

import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
import simplejson

from Globals import * 
from FileAccess import *  

# Code sampling from Phil65 (http://forum.kodi.tv/showthread.php?tid=160558)
def get_db_movies(filter_string="", limit=10):
    props = '"properties": ["title", "originaltitle", "votes", "playcount", "year", "genre", "studio", "country", "tagline", "plot", "runtime", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume", "art", "streamdetails", "mpaa", "director", "writer", "cast", "dateadded"]'
    json_response = get_Kodi_JSON('"method": "VideoLibrary.GetMovies", "params": {%s, %s, "limits": {"end": %d}}' % (props, filter_string, limit))
    if "result" in json_response and "movies" in json_response["result"]:
        movies = []
        for item in json_response["result"]["movies"]:
            movies.append(HandleDBMovieResult(item))
        return movies

def media_streamdetails(filename, streamdetails):
    info = {}
    video = streamdetails['video']
    audio = streamdetails['audio']
    info['VideoCodec'] = ''
    info['VideoAspect'] = ''
    info['VideoResolution'] = ''
    info['AudioCodec'] = ''
    info['AudioChannels'] = ''
    if video:
        if (video[0]['width'] <= 720 and video[0]['height'] <= 480):
            info['VideoResolution'] = "480"
        elif (video[0]['width'] <= 768 and video[0]['height'] <= 576):
            info['VideoResolution'] = "576"
        elif (video[0]['width'] <= 960 and video[0]['height'] <= 544):
            info['VideoResolution'] = "540"
        elif (video[0]['width'] <= 1280 and video[0]['height'] <= 720):
            info['VideoResolution'] = "720"
        elif (video[0]['width'] >= 1281 or video[0]['height'] >= 721):
            info['VideoResolution'] = "1080"
        else:
            info['videoresolution'] = ""
        info['VideoCodec'] = str(video[0]['codec'])
        if (video[0]['aspect'] < 1.4859):
            info['VideoAspect'] = "1.33"
        elif (video[0]['aspect'] < 1.7190):
            info['VideoAspect'] = "1.66"
        elif (video[0]['aspect'] < 1.8147):
            info['VideoAspect'] = "1.78"
        elif (video[0]['aspect'] < 2.0174):
            info['VideoAspect'] = "1.85"
        elif (video[0]['aspect'] < 2.2738):
            info['VideoAspect'] = "2.20"
        else:
            info['VideoAspect'] = "2.35"
    elif (('dvd') in filename and not ('hddvd' or 'hd-dvd') in filename) or (filename.endswith('.vob' or '.ifo')):
        info['VideoResolution'] = '576'
    elif (('bluray' or 'blu-ray' or 'brrip' or 'bdrip' or 'hddvd' or 'hd-dvd') in filename):
        info['VideoResolution'] = '1080'
    if audio:
        info['AudioCodec'] = audio[0]['codec']
        info['AudioChannels'] = audio[0]['channels']
    return info
    
def get_Kodi_JSON(params):
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", %s, "id": 1}' % params)
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    return simplejson.loads(json_query)

def HandleDBMovieResult(movie):
    trailer = "plugin://script.extendedinfo/?info=playtrailer&&dbid=%s" % str(movie['movieid'])
    # if ADDON.getSetting("infodialog_onclick") != "false":
        # path = 'plugin://script.extendedinfo/?info=action&&id=RunScript(script.extendedinfo,info=extendedinfo,dbid=%s)' % str(movie['movieid'])
    # else:
    path = trailer
    if (movie['resume']['position'] and movie['resume']['total']) > 0:
        resume = "true"
        played = '%s' % int((float(movie['resume']['position']) / float(movie['resume']['total'])) * 100)
    else:
        resume = "false"
        played = '0'
    streaminfo = media_streamdetails(movie['file'].encode('utf-8').lower(), movie['streamdetails'])
    db_movie = {'Art(fanart)': movie["art"].get('fanart', ""),
                'Art(poster)': movie["art"].get('poster', ""),
                'Fanart': movie["art"].get('fanart', ""),
                'Poster': movie["art"].get('poster', ""),
                'Banner': movie["art"].get('banner', ""),
                'DiscArt': movie["art"].get('discart', ""),
                'Title': movie.get('label', ""),
                'File': movie.get('file', ""),
                'Writer': " / ".join(movie['writer']),
                'Logo': movie['art'].get("clearlogo", ""),
                'OriginalTitle': movie.get('originaltitle', ""),
                'ID': movie.get('imdbnumber', ""),
                'Path': path,
                'PercentPlayed': played,
                'Resume': resume,
                # 'SubtitleLanguage': " / ".join(subs),
                # 'AudioLanguage': " / ".join(streams),
                'Play': "",
                'DBID': str(movie['movieid']),
                'Rating': str(round(float(movie['rating']), 1)),
                'Premiered': movie.get('year', "")}
    streams = []
    for i, item in enumerate(movie['streamdetails']['audio']):
        language = item['language']
        if language not in streams and language != "und":
            streams.append(language)
            db_movie['AudioLanguage.%d' % (i + 1)] = language
            db_movie['AudioCodec.%d' % (i + 1)] = item['codec']
            db_movie['AudioChannels.%d' % (i + 1)] = str(item['channels'])
    subs = []
    for i, item in enumerate(movie['streamdetails']['subtitle']):
        language = item['language']
        if language not in subs and language != "und":
            subs.append(language)
            db_movie['SubtitleLanguage.%d' % (i + 1)] = language
    db_movie.update(streaminfo)
    return db_movie
    
def GetMovieFromDB(movieid):
    json_response = get_Kodi_JSON('"method": "VideoLibrary.GetMovieDetails", "params": {"properties": ["title", "originaltitle", "votes", "playcount", "year", "genre", "studio", "country", "tagline", "plot", "runtime", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume", "art", "streamdetails", "mpaa", "director", "writer", "cast", "dateadded", "imdbnumber"], "movieid":%s }' % str(movieid))
    return HandleDBMovieResult(json_response["result"]["moviedetails"])

def GetSimilarFromOwnLibrary(dbid):
    log('script.pseudotv.live-utils: GetSimilarFromOwnLibrary')
    movie_response = get_Kodi_JSON('"method": "VideoLibrary.GetMovieDetails", "params": {"properties": ["genre","director","country","year","mpaa"], "movieid":%s }' % dbid)
    if "moviedetails" not in movie_response['result']:
        return []
    comp_movie = movie_response['result']['moviedetails']
    genres = comp_movie['genre']
    json_response = get_Kodi_JSON('"method": "VideoLibrary.GetMovies", "params": {"properties": ["genre","director","mpaa","country","year"], "sort": { "method": "random" } }')
    if "movies" not in json_response['result']:
        return []
    quotalist = []
    for item in json_response['result']['movies']:
        difference = abs(int(item['year']) - int(comp_movie['year']))
        hit = 0.0
        miss = 0.0
        quota = 0.0
        for genre in genres:
            if genre in item['genre']:
                hit += 1.0
            else:
                miss += 1.0
        miss += 0.00001
        if hit > 0.0:
            quota = float(hit) / float(hit + miss)
        if genres and item['genre'] and genres[0] == item['genre'][0]:
            quota += 0.3
        if difference < 3:
            quota += 0.3
        elif difference < 6:
            quota += 0.15
        if comp_movie['country'] and item['country'] and comp_movie['country'][0] == item['country'][0]:
            quota += 0.4
        if comp_movie['mpaa'] and item['mpaa'] and comp_movie['mpaa'] == item['mpaa']:
            quota += 0.4
        if comp_movie['director'] and item['director'] and comp_movie['director'][0] == item['director'][0]:
            quota += 0.6
        quotalist.append((quota, item["movieid"]))
    quotalist = sorted(quotalist, key=lambda quota: quota[0], reverse=True)
    movies = []
    for i, list_movie in enumerate(quotalist):
        if comp_movie['movieid'] is not list_movie[1]:
            newmovie = GetMovieFromDB(list_movie[1])
            movies.append(newmovie)
            if i == 20:
                break
    return movies
#################################################################################################################