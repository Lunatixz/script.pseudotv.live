# Copyright 2011-2014 Blazetamer, Jason Anderson, Kevin, Lunatixz,
# Martijn Kaijser, Tommy Winther & Tristan Fischer.
#
# This file is part of PseudoTV Live. <https://github.com/Lunatixz/script.pseudotv.live>
#
# PseudoTV Live is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV Live is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live. If not, see <http://www.gnu.org/licenses/>.

import os, re, sys, time, zipfile, threading
import urllib, urllib2
import xbmc, xbmcgui, xbmcplugin

# from functools import wraps
from addon.common.addon import Addon       
from resources.lib.Globals import *  
from Queue import Queue

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
    
#Downloader
def download(url, dest, dp = None):
    if not dp:
        dp = xbmcgui.DialogProgress()
        dp.create("PseudoTV Live","Downloading & Installing Files", ' ', ' ')
    dp.update(0)
    start_time=time.time()
    urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time))
     
     
def _pbhook(numblocks, blocksize, filesize, dp, start_time):
    try: 
        percent = min(numblocks * blocksize * 100 / filesize, 100) 
        currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
        kbps_speed = numblocks * blocksize / (time.time() - start_time) 
        if kbps_speed > 0: 
            eta = (filesize - numblocks * blocksize) / kbps_speed 
        else: 
            eta = 0 
        kbps_speed = kbps_speed / 1024 
        total = float(filesize) / (1024 * 1024) 
        mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total) 
        e = 'Speed: %.02f Kb/s ' % kbps_speed 
        e += 'ETA: %02d:%02d' % divmod(eta, 60) 
        dp.update(percent, mbs, e)
    except: 
        percent = 100 
        dp.update(percent) 
    if dp.iscanceled(): 
        dp.close() 
       
       
def Request_URL(url):
    try:
        req=urllib2.Request(url)
        req.add_header('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response=urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link
    except:
        pass
           
    
def Open_URL(url):        
    try:
        f = urllib2.urlopen(url)
        return f
    except:
        pass
        
#Extract
def all(_in, _out, dp=None):
    if dp:
        return allWithProgress(_in, _out, dp)

    return allNoProgress(_in, _out)
        

def allNoProgress(_in, _out):
    try:
        zin = zipfile.ZipFile(_in, 'r')
        zin.extractall(_out)
    except Exception, e:
        print str(e)
        return False

    return True


def allWithProgress(_in, _out, dp):

    zin = zipfile.ZipFile(_in,  'r')

    nFiles = float(len(zin.infolist()))
    count  = 0

    try:
        for item in zin.infolist():
            count += 1
            update = count / nFiles * 100
            dp.update(int(update))
            zin.extract(item, _out)
    except Exception, e:
        print str(e)
        return False

    return True
 
 
#TEXTBOX   
class TextBox:
    # constants
    WINDOW = 10147
    CONTROL_LABEL = 1
    CONTROL_TEXTBOX = 5

    def __init__(self, *args, **kwargs):
        # activate the text viewer window
        xbmc.executebuiltin("ActivateWindow(%d)" % ( self.WINDOW, ))
        # get window
        self.win = xbmcgui.Window(self.WINDOW)
        # give window time to initialize
        xbmc.sleep(4000)
        self.setControls()

    def setControls(self):
        # set heading
        heading = "Changelog - PseudoTV Live v%s" % (ADDON_VERSION)
        self.win.getControl(self.CONTROL_LABEL).setLabel(heading)
        # set text
        faq_path =(os.path.join(ADDON_PATH, 'changelog.txt'))
        f = open(faq_path)
        text = f.read()
        self.win.getControl(self.CONTROL_TEXTBOX).setText(text)
