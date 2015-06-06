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
import smtplib

from Globals import * 
from FileAccess import *  
from Queue import Queue
from HTMLParser import HTMLParser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from xml.dom.minidom import parse, parseString
socket.setdefaulttimeout(30)

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
    
# Paths    
Error = False
Path = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'skins', 'Default', '1080i')) #Path to Default PTVL skin, location of mod file.
fle = 'custom_script.pseudotv.live_9506.xml' #mod file, copy to xbmc skin folder
VWPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, fle))
flePath = xbmc.translatePath(os.path.join(Path, fle))
PTVL_SKIN_SELECT_FLE = xbmc.translatePath(os.path.join(PTVL_SKIN_SELECT, 'script.pseudotv.live.EPG.xml'))         
DSPath = xbmc.translatePath(os.path.join(XBMC_SKIN_LOC, 'DialogSeekBar.xml'))

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

def closest(list, Number):
    aux = []
    for valor in list:
        aux.append(abs(Number-int(valor)))

    return aux.index(min(aux))   
    
def removeEmptyElem(lst):
    return ([x for x in lst if x != ''])
    
def removeStringElem(lst,string):
    return ([x for x in lst if x != string])
           
def ChkSettings2():   
    log('script.pseudotv.live-utils: ChkSettings2')
    #Back/Restore Settings2
    settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
    nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.bak.xml'))
    atsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.pretune.xml'))
    bksettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'backups', 'settings2.' + str(datetime.datetime.now()).split('.')[0] + '.xml'))
    
    try:
        Normal_Shutdown = REAL_SETTINGS.getSetting('Normal_Shutdown') == "true"
    except:
        REAL_SETTINGS.setSetting('Normal_Shutdown', "true")
        Normal_Shutdown = REAL_SETTINGS.getSetting('Normal_Shutdown') == "true"
            
    if REAL_SETTINGS.getSetting("ATRestore") == "true" and REAL_SETTINGS.getSetting("Warning2") == "true":
        log('script.pseudotv.live-utils: ChkSettings2, Setting2 ATRestore')
        if getSize(atsettingsFile) > 100:
            REAL_SETTINGS.setSetting("ATRestore","false")
            REAL_SETTINGS.setSetting("Warning2","false")
            REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
            Restore(atsettingsFile, settingsFile) 
    elif Normal_Shutdown == False:
        log('script.pseudotv.live-utils: ChkSettings2, Setting2 Restore') 
        if getSize(settingsFile) < 100 and getSize(nsettingsFile) > 100:
            Restore(nsettingsFile, settingsFile)
    else:
        log('script.pseudotv.live-utils: ChkSettings2, Setting2 Backup') 
        if getSize(settingsFile) > 100:
            Backup(settingsFile, nsettingsFile)
            Backup(settingsFile, bksettingsFile)
                
def show_busy_dialog():
    xbmc.executebuiltin('ActivateWindow(busydialog)')

def hide_busy_dialog():
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    while xbmc.getCondVisibility('Window.IsActive(busydialog)'):
        time.sleep(.1)
        
def GetXBMCVersion():
    version = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
    version = version.split('.')
    log('script.pseudotv.live-utils: GetXBMCVersion = ' + str(version[0]))
    return int(version[0]) #major

def sorted_nicely(lst): 
    log('script.pseudotv.live-utils: sorted_nicely')
    list = set(lst)
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(list, key = alphanum_key)
       
def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]
    
def ClearCache(type):
    log('script.pseudotv.live-utils: ClearCache ' + type)  
    if type == 'Filelist':
        quarterly.delete("%") 
        bidaily.delete("%") 
        daily.delete("%") 
        weekly.delete("%")
        seasonal.delete("%") 
        monthly.delete("%")
        localTV.delete("%")
        liveTV.delete("%")
        YoutubeTV.delete("%")
        RSSTV.delete("%")
        pluginTV.delete("%")
        upnpTV.delete("%")
        lastfm.delete("%")
        REAL_SETTINGS.setSetting('ClearCache', "false")
    elif type == 'BCT':
        bumpers.delete("%")
        ratings.delete("%")
        commercials.delete("%")
        trailers.delete("%")
        REAL_SETTINGS.setSetting('ClearBCT', "false")
    elif type == 'Art':
        try:    
            shutil.rmtree(ART_LOC)
            log('script.pseudotv.live-utils: Removed ART_LOC')  
            REAL_SETTINGS.setSetting('ClearLiveArtCache', "true") 
            xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Folder Cleared", 1000, THUMB) )
        except:
            pass
        REAL_SETTINGS.setSetting('ClearLiveArt', "false")
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", type + " Cache Cleared", 1000, THUMB) )


def makeSTRM(mediapath):
    log('script.pseudotv.live-utils: makeSTRM')            
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
    JPG = ['banner', 'fanart', 'folder', 'landscape', 'poster']
    PNG = ['character', 'clearart', 'logo', 'disc']
    
    if arttype in JPG:
        arttypeEXT = (arttype + '.jpg')
    else:
        arttypeEXT = (arttype + '.png')
    log('script.pseudotv.live-utils: EXTtype = ' + str(arttypeEXT))
    return arttypeEXT
    
def getSize(file):
    if FileAccess.exists(file):
        fileobject = FileAccess.open(file, "r")
        fileobject.seek(0,2) # move the cursor to the end of the file
        size = fileobject.tell()
        fileobject.close()
        return size
        
def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)
    
def addon_status(id):
    check = xbmcaddon.Addon(id=id).getAddonInfo("name")
    if not check == ADDON_NAME: return True
    
def Backup(org, bak):
    log('script.pseudotv.live-utils: Backup ' + str(org) + ' - ' + str(bak))
    if FileAccess.exists(org):
        if FileAccess.exists(bak):
            try:
                FileAccess.delete(bak)
            except:
                pass
        FileAccess.copy(org, bak)
    
    if NOTIFY == 'true':
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Backup Complete", 1000, THUMB) )
       
def Restore(bak, org):
    log('script.pseudotv.live-utils: Restore ' + str(bak) + ' - ' + str(org))
    if FileAccess.exists(bak):
        if FileAccess.exists(org):
            try:
                xbmcvfs.delete(org)
            except:
                pass
        xbmcvfs.rename(bak, org)
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Restore Complete, Restarting...", 1000, THUMB) )

def replaceAll(file,searchExp,replaceExp):
    log('script.pseudotv.live-utils: script.pseudotv.live-utils: replaceAll')
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

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
    
def replaceXmlEntities(link):
    log('script.pseudotv.live-utils: replaceXmlEntities')   
    entities = (
        ("%3A",":"),("%2F","/"),("%3D","="),("%3F","?"),("%26","&"),("%22","\""),("%7B","{"),("%7D",")"),("%2C",","),("%24","$"),("%23","#"),("%40","@")
      );
    for entity in entities:
       link = link.replace(entity[0],entity[1]);
    return link;

def sorted_nicely(lst): 
    log('script.pseudotv.live-utils: sorted_nicely')
    list = set(lst)
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(list, key = alphanum_key)
    
def convert(s):
    log('script.pseudotv.live-utils: convert')       
    try:
        return s.group(0).encode('latin1').decode('utf8')
    except:
        return s.group(0)
        
def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

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
    log('script.pseudotv.live-utils: requestDownload')
    # requests = requests.Session()
    response = requests.get(url, stream=True)
    with open(fle, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
        
def Request_URL_CACHE(url):
    try:
        result = daily.cacheFunction(Request_URL, url)
    except:
        result = Request_URL(url)
        pass
    if not result:
        result = []
    return result     
        
def Request_URL(url):
    try:
        req=urllib2.Request(url)
        req.add_header('User-Agent','Magic Browser')
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
     
def sendGmail(subject, body, attach):
    GAuser = REAL_SETTINGS.getSetting('Visitor_GA')
    recipient = 'pseudotvlive@gmail.com'
    sender = 'pseudotvsubmit@gmail.com'
    password = 'pseudotvsubmit1'
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    
    if attach:
        log("sendGmail w/Attachment")
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject + ", From:" + GAuser
        msg.attach(MIMEText(body))
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition',
               'attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)
        mailServer = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(sender, password)
        mailServer.sendmail(sender, recipient, msg.as_string())
        # Should be mailServer.quit(), but that crashes...
        mailServer.close()
    else:
        log("sendGmail")
        body = "" + body + ""
        subject = subject + ", From:" + GAuser
        headers = ["From: " + sender,
                   "Subject: " + subject,
                   "To: " + recipient,
                   "MIME-Version: 1.0",
                   "Content-Type: text/html"]
        headers = "\r\n".join(headers)
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)        
        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(sender, password)
        session.sendmail(sender, recipient, headers + "\r\n\r\n" + body)
        session.quit()
def ClearPlaylists():
    log('script.pseudotv.live-utils: ClearPlaylists')
    for i in range(999):
        try:
            xbmcvfs.delete(CHANNELS_LOC + 'channel_' + str(i) + '.m3u')
        except:
            pass
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", 'Channel Playlists Cleared', 1000, THUMB) )
    return   

def CHKAutoplay():
    log('script.pseudotv.live-utils: CHKAutoplay')
    fle = xbmc.translatePath("special://profile/guisettings.xml")
    try:
        xml = FileAccess.open(fle, "r")
        dom = parse(xml)
        autoplaynextitem = dom.getElementsByTagName('autoplaynextitem')
        Videoautoplaynextitem  = (autoplaynextitem[0].childNodes[0].nodeValue.lower() == 'true')
        Musicautoplaynextitem  = (autoplaynextitem[1].childNodes[0].nodeValue.lower() == 'true')
        xml.close()
        log('script.pseudotv.live-utils: CHKAutoplay, Videoautoplaynextitem is ' + str(Videoautoplaynextitem)) 
        log('script.pseudotv.live-utils: CHKAutoplay, Musicautoplaynextitem is ' + str(Musicautoplaynextitem)) 
        totcnt = Videoautoplaynextitem + Musicautoplaynextitem
        if totcnt > 0:
            okDialog("Its recommended you disable Kodi's"+' "Play the next video/song automatically" ' + "feature found under Kodi's video/playback and music/playback settings.")
    except Exception,e:
        print str(e)
        return False
  
def VersionCompare():
    log('script.pseudotv.live-utils: VersionCompare')
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

def UpdateFiles():
    log('script.pseudotv.live-utils: UpdateFiles')
    url='https://github.com/Lunatixz/XBMC_Addons/raw/master/zips/repository.lunatixz/repository.lunatixz-1.0.zip'
    name = 'repository.lunatixz.zip' 
    MSG = 'Lunatixz Repository Installed'    
    path = xbmc.translatePath(os.path.join('special://home/addons','packages'))
    addonpath = xbmc.translatePath(os.path.join('special://','home/addons'))
    lib = os.path.join(path,name)
    log('script.pseudotv.live-utils: URL = ' + url)
    
    # Delete old install package
    try: 
        xbmcvfs.delete(lib)
        log('script.pseudotv.live-utils: deleted old package')
    except: 
        pass
        
    try:
        download(url, lib, '')
        log('script.pseudotv.live-utils: downloaded new package')
        all(lib,addonpath,'')
        log('script.pseudotv.live-utils: extracted new package')
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
            if GetXBMCVersion() == 15:
                raise
                
            if not FileAccess.exists(VWPath):
                log("VideoWindow, VWPath not found")
                FreshInstall = True
                xbmcvfs.copy(flePath, VWPath)
                if FileAccess.exists(VWPath):
                    log('script.pseudotv.live-utils: custom_script.pseudotv.live_9506.xml Copied')
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
                log('script.pseudotv.live-utils: script.pseudotv.live.EPG.xml Patched b,a')
            elif d in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,d,c)           
                log('script.pseudotv.live-utils: script.pseudotv.live.EPG.xml Patched d,c') 

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
                log('script.pseudotv.live-utils: dialogseekbar.xml Patched y,z')
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
                log('script.pseudotv.live-utils: script.pseudotv.live.EPG.xml UnPatched a,b')
            elif c in lines:
                replaceAll(PTVL_SKIN_SELECT_FLE,c,d)          
                log('script.pseudotv.live-utils: script.pseudotv.live.EPG.xml UnPatched c,d')
                
        #unpatch seekbar
        f = open(DSPath, "r")
        lineLST = f.readlines()            
        f.close()
        for i in range(len(lineLST)):
            line = lineLST[i]
            if w in line:
                replaceAll(DSPath,w,v)
                log('script.pseudotv.live-utils: dialogseekbar.xml UnPatched w,v')
    except Exception:
        Error = True
        pass

def VideoWindowUninstall():
    log('script.pseudotv.live-utils: VideoWindowUninstall')
    try:
        xbmcvfs.delete(VWPath)
        if not FileAccess.exists(VWPath):
            log('script.pseudotv.live-utils: custom_script.pseudotv.live_9506.xml Removed')
    except Exception:
        Error = True
        pass

def anonFTPDownload(filename, DL_LOC):
    log('script.pseudotv.live-utils: anonFTPDownload, ' + filename + ' - ' + DL_LOC)
    try:
        ftp = ftplib.FTP("ftp.pseudotvlive.com", "PTVLuser@pseudotvlive.com", "PTVLuser")
        ftp.cwd("/")
        file = FileAccess.open(DL_LOC, 'w')
        ftp.retrbinary('RETR %s' % filename, file.write)
        file.close()
        ftp.quit()
        return True
    except Exception, e:
        log('script.pseudotv.live-utils: anonFTPDownload, Failed!! ' + str(e))
        return False
        
def SyncXMLTV(force=False):
    log('script.pseudotv.live-utils: SyncXMLTV')
    now  = datetime.datetime.today()  
    try:
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
        log('script.pseudotv.live-utils: SyncPTVL, Now = ' + str(now) + ', SyncPTV_LastRun = ' + str(SyncPTV_LastRun))
        
        if now > SyncPTV:         
            #Remove old file before download
            if FileAccess.exists(PTVLXML):
                try:
                    xbmcvfs.delete(PTVLXML)
                    log('script.pseudotv.live-utils: SyncPTVL, Removed old PTVLXML')
                except:
                    log('script.pseudotv.live-utils: SyncPTVL, Removing old PTVLXML Failed!')

            #Download new file from ftp, then http backup.
            if anonFTPDownload('ptvlguide.zip', PTVLXMLZIP) == True:
                if FileAccess.exists(PTVLXMLZIP):
                    all(PTVLXMLZIP,XMLTV_CACHE_LOC,'')
                    try:
                        xbmcvfs.delete(PTVLXMLZIP)
                        log('script.pseudotv.live-utils: SyncPTVL, Removed PTVLXMLZIP')
                    except:
                        log('script.pseudotv.live-utils: SyncPTVL, Removing PTVLXMLZIP Failed!')
                
                if FileAccess.exists(os.path.join(XMLTV_CACHE_LOC,'ptvlguide.xml')):
                    log('script.pseudotv.live-utils: SyncPTVL, ptvlguide.xml download successful!')  
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live","Guidedata Update Complete", 1000, THUMB) )  
                    SyncPTV_NextRun = ((now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S.%f"))
                    log('script.pseudotv.live-utils: SyncPTVL, Now = ' + str(now) + ', SyncPTV_NextRun = ' + str(SyncPTV_NextRun))
                    REAL_SETTINGS.setSetting("SyncPTV_NextRun",str(SyncPTV_NextRun))   
            else:
                xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("Guidedata Update Failed!", 1000, THUMB) )  
    except:
        xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("Guidedata Update Failed!", 1000, THUMB) ) 
        pass
    return

def Comingsoon():
    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Coming Soon", 1000, THUMB) )

def Error(header, line1= '', line2= '', line3= ''):
    dlg = xbmcgui.Dialog()
    dlg.ok(header, line1, line2, line3)
    del dlg
    
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

def infoDialog(str, header=ADDON_NAME, time=4000):
    try: xbmcgui.Dialog().notification(header, str, THUMB, time, sound=False)
    except: xbmc.executebuiltin("Notification(%s,%s, %s, %s)" % (header, str, time, THUMB))

def Notify(header=ADDON_NAME, message="", icon=THUMB, time=5000, sound=False):
    xbmcgui.Dialog().notification(heading=header, message=message, icon=icon, time=time, sound=sound)

def get_Kodi_JSON(params):
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", %s, "id": 1}' % params)
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    return simplejson.loads(json_query)

def okDialog(str1, str2='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2)

def selectDialog(list, header=ADDON_NAME, autoclose=0):
    if len(list) > 0:
        select = xbmcgui.Dialog().select(header, list, autoclose)
        return select

def yesnoDialog(str1, str2='', header=ADDON_NAME, str3='', str4=''):
    answer = xbmcgui.Dialog().yesno(header, str1, str2, '', str4, str3)
    return answer

# Kodi Property
def getProperty(str):
    property = xbmcgui.Window(10000).getProperty(str)
    return property

def setProperty(str1, str2):
    xbmcgui.Window(10000).setProperty(str1, str2)

def clearProperty(str):
    xbmcgui.Window(10000).clearProperty(str)

def addon_status(id):
    check = xbmcaddon.Addon(id=id).getAddonInfo("name")
    if not check == addonName: return True

# class ArtService():

    # def PreArtService(self):
        # # ADDON_SETTINGS.loadSettings()
        # exclude = ['#EXTM3U', '#EXTINF']
        # i = 0
        # lineLST = []
        # newLST = []
        # ArtLST = []
        
        # for i in range(999):
            # try:
                # try:
                    # chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i) + '_type'))
                    # chname = (self.channels[i - 1].name)
                    # fle = xbmc.translatePath(os.path.join(LOCK_LOC, ("channel_" + str(i) + '.m3u')))  
                # except Exception,e:
                    # chtype = -1
                    # fle = ''
                    # pass
                
                # if chtype >= 0 and fle != '':
                    # if FileAccess.exists(fle):
                        # f = FileAccess.open(fle, 'r')
                        # lineLST = f.readlines()
                        # lineLST.pop(0) #Remove unwanted first line '#EXTM3U'
                        # for n in range(len(lineLST)):
                            # line = lineLST[n]
                            
                            # if line[0:7] == '#EXTINF':
                                # liveid = line.rsplit('//',1)[1]
                                # type = liveid.split('|')[0]
                                # id = liveid.split('|')[1]
                                # dbid = liveid.split('|')[2]
                                
                            # elif line[0:7] not in exclude:
                                # if id != -1:
                                    # if line[0:5] == 'stack':
                                        # smpath = (line.split(' , ')[0]).replace('stack://','').replace('rar://','')
                                        # mpath = (os.path.split(smpath)[0]) + '/'
                                    # elif line[0:6] == 'plugin':
                                        # mpath = 'plugin://' + line.split('/')[2] + '/'
                                    # elif line[0:4] == 'upnp':
                                        # mpath = 'upnp://' + line.split('/')[2] + '/'
                                    # else:
                                        # mpath = (os.path.split(line)[0]) + '/'

                                    # if type and mpath:
                                        # newLST = [type, chtype, chname, id, dbid, mpath]
                                        # ArtLST.append(newLST)
            # except:
                # pass
        # # shuffle list to evenly distribute queue
        # random.shuffle(ArtLST)
        # self.log('script.pseudotv.live-utils: PreArtService, ArtLST Count = ' + str(len(ArtLST)))
        # return ArtLST

        
    # def ArtService(self):
        # if getProperty("EnableArtwork") == "true" and getProperty("ArtService_Running") == "false":
            # setProperty("ArtService_Running","true")
            # start = datetime.datetime.today()
            # ArtLst = self.PreArtService() 
            # Types = []
            # cnt = 0
            # subcnt = 0
            # totcnt = 0
            # lstcnt = int(len(ArtLst))
            
            # if NOTIFY == True:
                # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Spooler Started", 4000, THUMB) )
            
            # # Clear Artwork Cache Folders
            # if REAL_SETTINGS.getSetting("ClearLiveArtCache") == "true":
                # artwork.delete("%") 
                # artwork1.delete("%")
                # artwork2.delete("%")
                # artwork3.delete("%")
                # artwork4.delete("%")
                # artwork5.delete("%")
                # artwork6.delete("%")
                # self.log('script.pseudotv.live-utils: ArtService, ArtCache Purged!')
                # REAL_SETTINGS.setSetting('ClearLiveArtCache', "false")
                
                # if NOTIFY == True:
                    # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Artwork Cache Cleared", 4000, THUMB) )
                # xbmc.sleep(5)
                
            # if getProperty("type1EXT_Overlay") != '':
                # Types.append(getProperty("type1EXT_Overlay"))
            # if getProperty("type2EXT_Overlay") != '':
                # Types.append(getProperty("type1EXT_Overlay"))
            # if getProperty("type3EXT_Overlay") != '':
                # Types.append(getProperty("type3EXT_Overlay"))    
              
            # try:
                # type1EXT_EPG = REAL_SETTINGS.getSetting('type1EXT_EPG')
                # if type1EXT_EPG != '':
                    # Types.append(type1EXT_EPG)
            # except:
                # pass        
            # try:
                # type2EXT_EPG = REAL_SETTINGS.getSetting('type2EXT_EPG')
                # if type2EXT_EPG != '':
                    # Types.append(type2EXT_EPG)
            # except:
                # pass
                
            # Types = remove_duplicates(Types)
            # self.log('script.pseudotv.live-utils: ArtService, Types = ' + str(Types))  
            
            # for i in range(lstcnt): 
                # if getProperty("PseudoTVRunning") == "True":
                    # setDefault = ''
                    # setImage = ''
                    # setBug = ''
                    # lineLST = ArtLst[i]
                    # type = lineLST[0]
                    # chtype = lineLST[1]
                    # chname = lineLST[2]
                    # id = lineLST[3]
                    # dbid = lineLST[4]
                    # mpath = lineLST[5]
                    # cnt += 1
                    
                    # self.Artdownloader.FindLogo(chtype, chname, mpath)
                    
                    # for n in range(len(Types)):
                        # typeEXT = str(Types[n])
                        # if '.' in typeEXT:
                            # self.Artdownloader.FindArtwork(type, chtype, chname, id, dbid, mpath, typeEXT)
                            
                    # if NOTIFY == True:
                        # if lstcnt > 5000:
                            # quartercnt = int(round(lstcnt / 4))
                        # else:
                            # quartercnt = int(round(lstcnt / 2))
                        # if cnt > quartercnt:
                            # totcnt = cnt + totcnt
                            # subcnt = lstcnt - totcnt
                            # percnt = int(round((float(subcnt) / float(lstcnt)) * 100))
                            # cnt = 0
                            # MSSG = ("Artwork Spooler"+' % '+"%d complete" %percnt) 
                            # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 4000, THUMB) )
                # else:
                    # return
                    
            # stop = datetime.datetime.today()
            # finished = stop - start
            # MSSG = ("Artwork Spooled in %d seconds" %finished.seconds) 
            # self.log('script.pseudotv.live-utils: ArtService, ' + MSSG)  
            # setProperty("ArtService_Running","false")
            # setProperty("EnableArtwork","true")
            # REAL_SETTINGS.setSetting("ArtService_LastRun",str(stop))
            
            # if NOTIFY == True:
                # xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", MSSG, 4000, THUMB) ) 