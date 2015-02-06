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


import os, re, sys, time, zipfile, threading, requests
import urllib, urllib2, base64, fileinput, shutil, socket
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
import urlparse, time, string

from Globals import *  
from FileAccess import FileAccess
from Queue import Queue
from HTMLParser import HTMLParser

socket.setdefaulttimeout(30)

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
      
FreshInstall = False
Error = False
Path = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '720p')) #Path to Default PTVL skin, location of mod file.
fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
VWPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle))
flePath = xbmc.translatePath(os.path.join(Path, fle))
PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))         
DSPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, 'DialogSeekBar.xml'))

###############################
#videowindow
a = '<!-- PATCH START -->'
b = '<!-- PATCH START --> <!--'
c = '<!-- PATCH END -->'
d = '--> <!-- PATCH END -->'
#seekbar
v = ' '
w = '<visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
y = '</defaultcontrol>'
z = '</defaultcontrol>\n    <visible>Window.IsActive(fullscreenvideo) + !Window.IsActive(script.pseudotv.TVOverlay.xml) + !Window.IsActive(script.pseudotv.live.TVOverlay.xml)</visible>'
###############################


def sendGmail(SUBJECT, text):
    log("sendGmail")
    try:
        import smtplib
        import string
         
        HOST = "alt1.gmail-smtp-in.l.google.com"
        TO = "pseudotvlive@gmail.com"
        FROM = "python@mydomain.com"
        BODY = string.join((
                "From: %s" % FROM,
                "To: %s" % TO,
                "Subject: %s" % SUBJECT ,
                "",
                text
                ), "\r\n")
        server = smtplib.SMTP(HOST)
        server.sendmail(FROM, [TO], BODY)
        server.quit()
        return True
    except:
        return False
    

def sorted_nicely(lst): 
    log('sorted_nicely')
    """ Sort the given iterable in the way that humans expect.""" 
    list = set(lst)
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(list, key = alphanum_key)
    
    
def splitall(path):
    log("splitall")
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts
        
        
def infoDialog(str, header=ADDON_NAME):
    try: xbmcgui.Dialog().notification(header, str, THUMB, 3000, sound=False)
    except: xbmc.executebuiltin("Notification(%s,%s, 3000, %s)" % (header, str, THUMB))

    
def okDialog(str1, str2, header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2)

    
def selectDialog(list, header=ADDON_NAME):
    log('selectDialog')
    select = xbmcgui.Dialog().select(header, list)
    return select

    
def yesnoDialog(str1, str2, header=ADDON_NAME, str3='', str4=''):
    answer = xbmcgui.Dialog().yesno(header, str1, str2, '', str4, str3)
    return answer

    
def getProperty(str):
    property = xbmcgui.Window(10000).getProperty(str)
    return property

    
def setProperty(str1, str2):
    xbmcgui.Window(10000).setProperty(str1, str2)

    
def clearProperty(str):
    xbmcgui.Window(10000).clearProperty(str)

    
def addon_status(id):
    check = xbmcaddon.Addon(id=id).getAddonInfo("name")
    if not check == ADDON_NAME: return True

    
def ClearPlaylists():
    log('ClearPlaylists')
    for i in range(999):
        try:
            xbmcvfs.delete(CHANNELS_LOC + 'channel_' + str(i) + '.m3u')
        except:
            pass
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", 'Channel Playlists Cleared', 1000, THUMB) )
    return
    

# Compare git version with local version.
def VersionCompare():
    log('VersionCompare')
    curver = xbmc.translatePath(os.path.join(ADDON_PATH,'addon.xml'))    
    source = open(curver, mode = 'r')
    link = source.read()
    source.close()
    match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
    
    for vernum in match:
        log("Current Version = " + str(vernum))
    try:
        link = Request_URL('https://raw.githubusercontent.com/Lunatixz/XBMC_Addons/master/script.pseudotv.live/addon.xml')               
    except:
        link='nill'
    
    link = link.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
    match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
 
    if len(match) > 0:
        print vernum, str(match)[0]
        if vernum != str(match[0]):
            dialog = xbmcgui.Dialog()
            confirm = xbmcgui.Dialog().yesno('[B]PseudoTV Live Update Available![/B]', "Your version is outdated." ,'The current available version is '+str(match[0]),'Would you like to install the PseudoTV Live repository to stay updated?',"Cancel","Install")
            if confirm:
                UpdateFiles()       
    return
    
    
#autoupdate modified from Blazetamer code.
def UpdateFiles():
    log('UpdateFiles')
    url='https://github.com/Lunatixz/XBMC_Addons/raw/master/zips/repository.lunatixz/repository.lunatixz-1.0.zip'
    name = 'repository.lunatixz.zip' 
    MSG = 'Lunatixz Repository Installed'    
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
        
    try:
        download(url, lib, '')
        log('downloaded new package')
        all(lib,addonpath,'')
        log('extracted new package')
    except: 
        MSG = 'Failed to install Lunatixz Repository, Try Again Later'
        pass
    xbmc.executebuiltin("XBMC.UpdateLocalAddons()"); 
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSG, 1000, THUMB) )
    return

    
def VideoWindow():
    log("VideoWindow, VWPath = " + str(VWPath))
    #Copy VideoWindow Patch file
    try:
        if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
            if not xbmcvfs.exists(VWPath):
                log("VideoWindow, VWPath not found")
                FreshInstall = True
                xbmcvfs.copy(flePath, VWPath)
                if xbmcvfs.exists(VWPath):
                    log('custom_script.pseudotv.live_9506.xml Copied')
                    VideoWindowPatch()         
                else:
                    raise
            else:
                log("VideoWindow, VWPath found")
                VideoWindowPatch()
    except Exception:
        VideoWindowUninstall()
        VideoWindowUnpatch()
        Error = True
        pass

        
def VideoWindowPatch():
    log("VideoWindowPatch")
    #Patch Videowindow/Seekbar
    try:
        f = open(PTVL_SKIN_SELECT_FLE, "r")
        linesLST = f.readlines()  
        f.close()
        
        for i in range(len(linesLST)):
            lines = linesLST[i]
            if b in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,b,a)        
                log('script.pseudotv.live.EPG.xml Patched b,a')
            elif d in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,d,c)           
                log('script.pseudotv.live.EPG.xml Patched d,c') 

        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        
        for i in range(len(lineLST)):
            line = lineLST[i]
            if y in line:
                replaceAll(DSPath,y,z)
            log('dialogseekbar.xml Patched y,z')
    except Exception:
        VideoWindowUninstall()
        pass
                            
        
def VideoWindowUnpatch():
    log("VideoWindowUnpatch")
    #unpatch videowindow
    try:
        f = open(PTVL_SKIN_SELECT_FLE, "r")
        linesLST = f.readlines()    
        f.close()
        for i in range(len(linesLST)):
            lines = linesLST[i]
            if a in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,a,b)
                log('script.pseudotv.live.EPG.xml UnPatched a,b')
            elif c in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,c,d)          
                log('script.pseudotv.live.EPG.xml UnPatched c,d')
                
        #unpatch seekbar
        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        for i in range(len(lineLST)):
            line = lineLST[i]
            if w in line:
                replaceAll(DSPath,w,v)
                log('dialogseekbar.xml UnPatched w,v')
    except Exception:
        Error = True
        pass
      

def VideoWindowUninstall():
    log('VideoWindowUninstall')
    try:
        xbmcvfs.delete(VWPath)
        if not xbmcvfs.exists(VWPath):
            log('custom_script.pseudotv.live_9506.xml Removed')
    except Exception:
        Error = True
        pass


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
       

def requestDownload(url, fle):
    log('requestDownload')
    # requests = requests.Session()
    response = requests.get(url, stream=True)
    with open(fle, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    
    
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
        result = daily.cacheFunction(Open_URL_UP_NEW, url, userpass)
    except:
        result = Open_URL_UP_NEW(url, userpass)
        pass
    if not result:
        result = []
    return result                 
                
                
def Open_URL_UP_NEW(url, userpass):
    print 'Open_URL_UP_NEW'
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


class FileCache:
	'''Caches the contents of a set of files.
	Avoids reading files repeatedly from disk by holding onto the
	contents of each file as a list of strings.
	'''

	def __init__(self):
		self.filecache = {}
		
	def grabFile(self, filename):
		'''Return the contents of a file as a list of strings.
		New line characters are removed.
		'''
		if not self.filecache.has_key(filename):
			f = open(filename, "r")
			self.filecache[filename] = string.split(f.read(), '\n')
			f.close()
		return self.filecache[filename]