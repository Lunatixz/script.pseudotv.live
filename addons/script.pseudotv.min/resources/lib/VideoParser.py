#   Copyright (C) 2015 Jason Anderson, Kevin S. Graer
#
#
# This file is part of PseudoTV Min.
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

import xbmc
import os, platform
import subprocess

try:
    import parsers.MP4Parser as MP4Parser
    import parsers.AVIParser as AVIParser
    import parsers.MKVParser as MKVParser
    import parsers.FLVParser as FLVParser
    import parsers.TSParser  as TSParser
except:
    xbmc.log("FATAL - Failed to import video parsers", xbmc.LOGFATAL)
    
#import parsers.STRMParser  as STRMParser

from Globals import *
from FileAccess import FileAccess

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer
    
class VideoParser:
    def __init__(self):
        self.AVIExts = ['.avi']
        self.MP4Exts = ['.mp4', '.m4v', '.3gp', '.3g2', '.f4v', '.mov']
        self.MKVExts = ['.mkv']
        self.FLVExts = ['.flv']
        self.TSExts  = ['.ts', '.m2ts']
        self.MasterExts = self.AVIExts + self.MP4Exts + self.MKVExts + self.FLVExts + self.TSExts


    def log(self, msg, level = xbmc.LOGNOTICE):
        logGlob('VideoParser: ' + msg, level)
    
    def logDebug(self, msg):
        logGlob('VideoParser: ' + msg)
    
    def logError(self, msg):
        logGlob('VideoParser: ' + msg, xbmc.LOGERROR)
    
    
    def extCheck(self, sFile):
        sExt = ''
        if sFile[-5] == '.':
            sExt = sFile[len(sFile)-5:len(sFile)]
        elif sFile[-4] == '.':
            sExt = sFile[len(sFile)-4:len(sFile)]
        elif sFile[-3] == '.':
            sExt = sFile[len(sFile)-3:len(sFile)]
        else:
            self.logError('Failed to get extension for: %s' %sFile)
            return False
        
        for i in self.MasterExts:
            if i == sExt:
                return True
        
        self.log('Extension not supported: [%s]' %sExt)
        return False
        
    def getVideoLength(self, filename):
        self.log("getVideoLength: %s" %filename)
        
        if not self.extCheck(filename):
            return 0
        
        if Cache_Enabled == True:  
            try:
                result = parsers.cacheFunction(self.getVideoLength_NEW, filename)
            except:
                result = self.getVideoLength_NEW(filename)
                pass
        else:
            result = self.getVideoLength_NEW(filename)
        if not result:
            result = 0
        return result 

        
    def getVideoLength_NEW(self, filename):
        self.log("getVideoLength_NEW " + filename)
        if len(filename) == 0:
            self.log("No file name specified")
            return 0

        if FileAccess.exists(filename) == False:
            self.log("Unable to find the file")
            return 0
            
        if not self.extCheck(filename):
            return 0

        base, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext in self.AVIExts:
            self.parser = AVIParser.AVIParser()
        elif ext in self.MP4Exts:
            self.parser = MP4Parser.MP4Parser()
        elif ext in self.MKVExts:
            self.parser = MKVParser.MKVParser()
        elif ext in self.FLVExts:
            self.parser = FLVParser.FLVParser()
        elif ext in self.TSExts:
            self.parser = TSParser.TSParser()
        else:
            self.logError("No parser found for extension " + ext)
            return 0

        return self.parser.determineLength(filename)