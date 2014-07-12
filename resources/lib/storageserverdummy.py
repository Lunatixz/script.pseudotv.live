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

'''
     StorageServer override.
     Version: 1.0
'''

class StorageServer:
    def __init__(self, table, timeout=24):
        return None

    def cacheFunction(self, funct=False, *args):
        return funct(*args)

    def set(self, name, data):
        return ""

    def get(self, name):
        return ""

    def setMulti(self, name, data):
        return ""

    def getMulti(self, name, items):
        return ""

    def lock(self, name):
        return False

    def unlock(self, name):
        return False
