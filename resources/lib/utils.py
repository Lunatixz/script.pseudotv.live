#   Copyright (C) 2014 Kevin S. Graer
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


import os, re, sys, time, zipfile, threading
import urllib, urllib2, base64, fileinput
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
import urlparse, time

from Globals import *  
from FileAccess import FileAccess
from Queue import Queue
from HTMLParser import HTMLParser


# Compare git version with local version.
def VersionCompare():
    log('VersionCompare')
    try:
        log("CheckVersion mode = " + str(REAL_SETTINGS.getSetting("Auto_Version")))
        curver = xbmc.translatePath(os.path.join(ADDON_PATH,'addon.xml'))    
        source = open(curver, mode = 'r')
        link = source.read()
        source.close()
        match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
        
        for vernum in match:
            log("Original Version = " + str(vernum))
            
        #Master - Stable
        if REAL_SETTINGS.getSetting("Auto_Version") == "1":
            link = Request_URL('https://raw.githubusercontent.com/Lunatixz/XBMC_Addons/master/script.pseudotv.live/addon.xml')
        #Development - Latest
        elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
            link = Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/development/addon.xml')
                
        link = link.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
        match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
        
        if len(match) > 0:
            if vernum != str(match[0]):
                dialog = xbmcgui.Dialog()

                if REAL_SETTINGS.getSetting("Auto_Version") == "1":
                    confirm = xbmcgui.Dialog().yesno('[B]PseudoTV Live Update Available![/B]', "Your version is outdated." ,'The current available version is '+str(match[0]),'Would you like to install the PseudoTV Live repository to stay updated?',"Cancel","Update")
                elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
                    confirm = xbmcgui.Dialog().yesno('[B]PseudoTV Live Update Available![/B]', "Your version is outdated." ,'The current available version is '+str(match[0]),'Would you like to update now?',"Cancel","Update")

                if confirm:
                    UpdateFiles()       
    except Exception: 
        pass
    return
    
    
#autoupdate modified from Blazetamer code.
def UpdateFiles():
    log('UpdateFiles')
    
    if REAL_SETTINGS.getSetting("Auto_Version") == "1":
        url='https://github.com/Lunatixz/XBMC_Addons/raw/master/zips/repository.lunatixz/repository.lunatixz-1.0.zip'
        name = 'repository.lunatixz.zip' 
        MSG = 'Repository Install Complete'    
    elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
        url='https://github.com/Lunatixz/script.pseudotv.live/archive/development.zip'
        name = 'script.pseudotv.live.zip' 
        MSG = 'Development Build Updated'
        
    path = xbmc.translatePath(os.path.join('special://home/addons','packages'))
    addonpath = xbmc.translatePath(os.path.join('special://','home/addons'))
    lib = os.path.join(path,name)
    log('URL = ' + url)
    
    # Delete old install package
    try: 
        xbmcvfs.delete(lib)
        log('deleted old package')
    except: 
        pass
    
    # Delete old install folders  
    try: 
        xbmcvfs.delete(xbmc.translatePath(os.path.join('special://home/addons','script.pseudotv.live')))
    except: 
        pass
    try: 
        xbmcvfs.delete(xbmc.translatePath(os.path.join('special://home/addons','script.pseudotv.live-master')))
    except: 
        pass
    try: 
        xbmcvfs.delete(xbmc.translatePath(os.path.join('special://home/addons','script.pseudotv.live-development')))
    except: 
        pass
     
    try:
        download(url, lib, '')
        log('downloaded new package')
        all(lib,addonpath,'')
        log('extracted new package')
    except: 
        MSG = 'Update Failed, Try Again Later'
        pass
        
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 4000, THUMB) )
    return

    
#String replace
def replaceAll(file,searchExp,replaceExp):
    xbmc.log('script.pseudotv.live-utils: replaceAll')
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
    
    
#Downloader
def download(url, dest, dp = None):
    if not dp:
        dp = xbmcgui.DialogProgress()
        dp.create("PseudoTV Live","Downloading & Installing Files", ' ', ' ')
    dp.update(0)
    start_time=time.time()
    try:
        urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time))
    except:
        pass
        
        
def download_silent(url, dest):
    print 'download_silent'
    try:
        urllib.urlretrieve(url, dest)
    except:
        pass
     
     
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
    except urllib2.URLError as e:
        pass


def Open_URL_UP(url, userpass):
    try:
        userpass = userpass.split(':')
        username = userpass[0]
        password = userpass[1]
        request = urllib2.Request(url)
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = Open_URL(request)
        return result.readlines()
    except:
        pass
        
        
def Open_URL_Request(url):
    try:
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
        f = urllib2.urlopen(req)
        return f
    except:
        pass
        
        
def Download_URL(_in, _out): 
    Finished = False    
    
    if xbmcvfs.exists(_out):
        try:
            os.remove(_out)
        except:
            pass
    try:
        resource = urllib.urlopen(_in)
        output = FileAccess.open(_out, 'w')
        output.write(resource.read())
        Finished = True    
        output.close()
    except:
        pass
        
    return Finished
        
        
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
        heading = "Changelog - PseudoTV Live"
        self.win.getControl(self.CONTROL_LABEL).setLabel(heading)
        
        # set text
        faq_path =(os.path.join(ADDON_PATH, 'changelog.txt'))
        f = open(faq_path)
        text = f.read()
        self.win.getControl(self.CONTROL_TEXTBOX).setText(text)
        
        # if REAL_SETTINGS.getSetting("Auto_Version") == "1":
            # link=Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/master/changelog.txt')
        # elif REAL_SETTINGS.getSetting("Auto_Version") == "2":
            # link=Request_URL('https://raw.githubusercontent.com/Lunatixz/script.pseudotv.live/development/changelog.txt')
        
        # try:
            # f = urllib2.urlopen(link)
            # text = f.read()
            # self.win.getControl(self.CONTROL_TEXTBOX).setText(text)
        # except:
            # pass
            
        
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
                    
    def retrieve_icons_avail(self, region='us'):
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
            result = 0
        return result
         
            
    def retrieve_icons_avail_NEW(self, region='us'):
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
       