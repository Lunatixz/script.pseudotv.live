import os, re, sys
import json, socket, urllib, urllib2
import shutil, random, time
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
socket.setdefaulttimeout(30)
opener = urllib2.build_opener()
userAgent = "Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0"
opener.addheaders = [('User-Agent', userAgent)]

path = "D:/XBMC/portable_data/userdata/addon_data/plugin.video.my_music_tv/plist"
channel = '1'
fle = "Channel_" + channel +".xml.PlistDir"

if os.path.exists(os.path.join(path,fle)):
    f = open(os.path.join(path,fle),'r')
    lineLST = f.readlines()

    for n in range(len(lineLST)):
        line = lineLST[n].replace("['",'').replace("']",'').replace('["','').replace("\n",'')
        line = line.split(", ")
        title = line[0]
        link = line[1]

        try:
            id = str(os.path.split(link)[1]).split('?url=')[1]
            source = str(id).split('&mode=')[1]
            id = str(id).split('&mode=')[0]
        except:
            pass

        print title, link , source, id
        if source == 'playVevo':
            playVevo()

def playVevo(id):
    content = opener.open("http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc="+id).read()
    content = str(json.loads(content))
    print content

