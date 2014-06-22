def main():
    pass

if __name__ == '__main__':
    main()

import os, sys, re, shutil
import xbmc, xbmcgui, xbmcaddon, xbmcvfs

from resources.lib.Globals import *
from resources.lib.FileAccess import *

settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
nsettingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'new_settings2.xml'))

OpnFil = FileAccess.open(settingsFile, "r")
WrtFil = FileAccess.open(settingsFile, "w")
WrtFil.write('<settings> \n')

# Number of total lines in Settings2.xml file
nr_of_lines = len(OpnFil.readlines())

# Procedure to get the total number of channels for this Settings2.xml file
# High_Chan_Num variable will be the highest channel for the user
# ChanNum variable is used to compare the current input channel with the
# current highest channel (High_Chan_Num)

High_Chan_Num = 0
OpnFil.seek(0, 2)  # Start file at the first line

for line in range(1, nr_of_lines): # Equal length of file
    Xstring = str(OpnFil.readlines()) #Input line as string from Settings2.xml file
    ins = Xstring.split("_")    # Split the line into parts using "_" delimeter
        # If the first part <> this string, then get next line
    if ins[0] == "    <setting id=" + chr(34) + "Channel":
        n=ins[1]    # assign variable to channel # string
        ChanNum=int(n)  # convert Channel Number to integer
        if ChanNum > High_Chan_Num:     #If > High_Chan_Num then
            High_Chan_Num=ChanNum       # assign to High_Chan_Num

High_Chan_Num = High_Chan_Num + 1    #Add 1 for following procedures.

for Num_Pos_Chan in range(1, High_Chan_Num): # Equal number of possible channels

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_type"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)  # Start file at the first line
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_1"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
           WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_2"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_3"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_4"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_rule"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_changed"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_time"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_SetResetTime"
        Xstring = OpnFil.readlines()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0, 2)
    for line in range(1, nr_of_lines): # Equal length of file
        #Search_Item_A = "LastExitTime"
        #Search_Item_B = "LastResetTime"
        Xstring = str(OpnFil.readlines())
        if re.search("LastExitTime", Xstring, re.I):
            WrtFil.write (Xstring)
        elif re.search("LastResetTime", Xstring, re.I):
            WrtFil.write (Xstring)

WrtFil.write('</settings> \n')

OpnFil.close()
WrtFil.close()

# try:
os.remove(settingsFile)
FileAccess.rename(nsettingsFile, settingsFile)
# except:
    # pass