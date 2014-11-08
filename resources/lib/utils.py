import os, re, sys, time, zipfile, threading
import urllib, urllib2, base64
import xbmc, xbmcgui, xbmcplugin, xbmcvfs
import urlparse, time

# from functools import wraps
from addon.common.addon import Addon       
from Globals import *  
from FileAccess import FileLock, FileAccess
from Queue import Queue
from HTMLParser import HTMLParser

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

        
def Open_URL_CACHE(url):
    print ("Open_URL_CACHE Cache")
    if Cache_Enabled:
        try:
            result = daily.cacheFunction(Open_URL_CACHE_NEW, url)
        except:
            result = Open_URL_CACHE_NEW(url)
            pass
    else:
        result = Open_URL_CACHE_NEW(url)
    
    if not result:
        result = 'Empty'
    return result   
    
    
def Open_URL_CACHE_NEW(url):  
    print ("Open_URL_CACHE_NEW")      
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
        
        if dlg.yesno("PseudoTV Live", "Restart required after update, Exit XBMC?"):
            xbmc.executebuiltin("Quit")
        
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