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
import urlparse, time, string, datetime, ftplib, hashlib

from Globals import * 
from FileAccess import *  
from Queue import Queue
from HTMLParser import HTMLParser

socket.setdefaulttimeout(30)

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
      
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

def convert(s):
    log('convert')       
    try:
        return s.group(0).encode('latin1').decode('utf8')
    except:
        return s.group(0)
                      
                      
def makeSTRM(mediapath):
    log('makeSTRM')            
    if not FileAccess.exists(STRM_CACHE_LOC):
        FileAccess.makedirs(STRM_CACHE_LOC)
    path = (mediapath.encode('base64'))[:16] + '.strm'
    filepath = os.path.join(STRM_CACHE_LOC,path)
    if FileAccess.exists(filepath):
        return filepath
    else:
        fle = FileAccess.open(filepath, "w")
        fle.write("%s" % mediapath)
        fle.close()
        return filepath
   
   
def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()
    
    
def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output

    
def EXTtype(arttype): 
    log('EXTtype')
    JPG = ['banner', 'fanart', 'folder', 'landscape', 'poster']
    PNG = ['character', 'clearart', 'logo', 'disc']
    
    if arttype in JPG:
        arttypeEXT = (arttype + '.jpg')
    else:
        arttypeEXT = (arttype + '.png')
    log('EXTtype = ' + str(arttypeEXT))
    return arttypeEXT
        

def anonFTPDownload(filename, DL_LOC):
    log('anonFTPDownload, ' + filename + ' - ' + DL_LOC)
    try:
        ftp = ftplib.FTP("ftp.pseudotvlive.com", "anonymous@pseudotvlive.com", "anonymous@pseudotvlive.com")
        ftp.cwd("/ptvl")
        file = FileAccess.open(DL_LOC, 'w')
        ftp.retrbinary('RETR %s' % filename, file.write)
        file.close()
        ftp.quit()
    except Exception, e:
        print str(e)
        pass
        
def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

    
def getSize(file):
    if FileAccess.exists(file):
        fileobject = FileAccess.open(file, "r")
        fileobject.seek(0,2) # move the cursor to the end of the file
        size = fileobject.tell()
        fileobject.close()
        return size
    
           
def Backup(org, bak):
    log('Backup ' + str(org) + ' - ' + str(bak))
    if FileAccess.exists(org):
        if FileAccess.exists(bak):
            try:
                xbmcvfs.delete(bak)
            except:
                pass
        xbmcvfs.copy(org, bak)
    
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Backup Complete", 1000, THUMB) )
        
            
def Restore(bak, org):
    log('Restore ' + str(bak) + ' - ' + str(org))
    if FileAccess.exists(bak):
        if FileAccess.exists(org):
            try:
                xbmcvfs.delete(org)
            except:
                pass
        xbmcvfs.rename(bak, org)
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Restore Complete, Restarting...", 1000, THUMB) )


def Error(header, line1= '', line2= '', line3= ''):
    dlg = xbmcgui.Dialog()
    dlg.ok(header, line1, line2, line3)
    del dlg
    
    
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
     

def showText(heading, text):
    log("showText")
    id = 10147
    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)
    win = xbmcgui.Window(id)
    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            return
        except:
            pass

            
def infoDialog(str, header=ADDON_NAME):
    try: xbmcgui.Dialog().notification(header, str, THUMB, 3000, sound=False)
    except: xbmc.executebuiltin("Notification(%s,%s, 3000, %s)" % (header, str, THUMB))

    
def okDialog(str1, str2='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2)

    
def selectDialog(list, header=ADDON_NAME):
    log('selectDialog')
    if len(list) > 0:
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
    xbmcgui.Window(10000).setProperty("PseudoTVOutdated", "False")
    
    for vernum in match:
        log("Current Version = " + str(vernum))
    try:
        link = Request_URL('https://raw.githubusercontent.com/Lunatixz/XBMC_Addons/master/script.pseudotv.live/addon.xml')  
        link = link.replace('\r','').replace('\n','').replace('\t','').replace('&nbsp;','')
        match = re.compile('" version="(.+?)" name="PseudoTV Live"').findall(link)
    except:
        pass   
        
    if len(match) > 0:
        print vernum, str(match)[0]
        if vernum != str(match[0]):
            xbmcgui.Window(10000).setProperty("PseudoTVOutdated", "True")
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
    FreshInstall = False
    #Copy VideoWindow Patch file
    try:
        if xbmcgui.Window(10000).getProperty("PseudoTVRunning") != "True":
            if not FileAccess.exists(VWPath):
                log("VideoWindow, VWPath not found")
                FreshInstall = True
                xbmcvfs.copy(flePath, VWPath)
                if FileAccess.exists(VWPath):
                    log('custom_script.pseudotv.live_9506.xml Copied')
                    VideoWindowPatch()   
                    if FreshInstall == True:
                        xbmc.executebuiltin("ReloadSkin()")
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
        
        Ypatch = True
        for i in range(len(lineLST)):
            line = lineLST[i]
            if z in line:
                Ypatch = False
                break
            
        if Ypatch:
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
        if not FileAccess.exists(VWPath):
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
           
           
def Open_URL_CACHE(url):
    try:
        result = daily.cacheFunction(Open_URL, url)
    except:
        result = Open_URL(url)
        pass
    if not result:
        result = []
    return result                 
                
                  
def Open_URL(url):        
    try:
        f = urllib2.urlopen(url)
        return f
    except urllib2.URLError as e:
        pass
    
    
def Read_URL(url):        
    try:
        f = urllib2.urlopen(url)
        return f.readlines()
    except urllib2.URLError as e:
        pass

        
def Force_URL(url):
    Con = True
    Count = 0
    while Con:
        if Count > 3:
            Con = False
        try:
            req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
            return urllib2.urlopen(req)
            Con = False
        except URLError, e:
            print "Oops, timed out?"
            Con = True
        except socket.timeout:
            print "Timed out!"
            Con = True
            pass 
        Count += 1
            
            
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
    
    if FileAccess.exists(_out):
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
     
     
def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise
           
            
def SyncXMLTV():
    log('SyncXMLTV') 
    if xbmcgui.Window(10000).getProperty("SyncXMLTV_Running") != "True":
        xbmcgui.Window(10000).setProperty("SyncXMLTV_Running", "True")
        
        if FileAccess.exists(XMLTV_CACHE_LOC) == False:
            try:
                xbmcvfs.mkdir(XMLTV_CACHE_LOC)
            except:
                return           
        SyncPTVL()
    xbmcgui.Window(10000).setProperty("SyncXMLTV_Running", "False")
    return
    
                           
def SyncPTVL(force=False):
    log('SyncPTVL')
    now  = datetime.datetime.today()  
    try:
        SyncPTV_LastRun = REAL_SETTINGS.getSetting('SyncPTV_NextRun')
        if not SyncPTV_LastRun or FileAccess.exists(PTVLXML) == False or force == True:
            raise
    except:
        SyncPTV_LastRun = "1970-01-01 23:59:00.000000"
        REAL_SETTINGS.setSetting("SyncPTV_NextRun",SyncPTV_LastRun)
    try:
        SyncPTV = datetime.datetime.strptime(SyncPTV_LastRun, "%Y-%m-%d %H:%M:%S.%f")
    except:
        SyncPTV_LastRun = "1970-01-01 23:59:00.000000"
        SyncPTV = datetime.datetime.strptime(SyncPTV_LastRun, "%Y-%m-%d %H:%M:%S.%f")
        
    log('SyncPTVL, Now = ' + str(now) + ', SyncPTV_LastRun = ' + str(SyncPTV_LastRun))
    
    if now > SyncPTV:         
        #Remove old file before download
        if FileAccess.exists(PTVLXML):
            try:
                xbmcvfs.delete(PTVLXML)
                log('SyncPTVL, Removed old PTVLXML')
            except:
                log('SyncPTVL, Removing old PTVLXML Failed!')

        #Download new file from ftp, then http backup.
        try:
            anonFTPDownload('ptvlguide.zip', PTVLXMLZIP)
        except:
            return
            
        if FileAccess.exists(PTVLXMLZIP):
            all(PTVLXMLZIP,XMLTV_CACHE_LOC,'')
            try:
                xbmcvfs.delete(PTVLXMLZIP)
                log('SyncPTVL, Removed old PTVLXMLZIP')
            except:
                log('SyncPTVL, Removing old PTVLXMLZIP Failed!')
                
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","External Guide-data Update Complete", 1000, THUMB) )      
        SyncPTV_NextRun = ((now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S.%f"))
        log('SyncPTVL, Now = ' + str(now) + ', SyncPTV_NextRun = ' + str(SyncPTV_NextRun))
        REAL_SETTINGS.setSetting("SyncPTV_NextRun",str(SyncPTV_NextRun))     
    return 