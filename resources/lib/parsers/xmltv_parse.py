#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, xmltv

from operator import itemgetter
from collections import namedtuple

filename = "tv.xml"

Channel = namedtuple('Channel', [
    'id', 'name', 'icon'
])

def channels():
    channels = {}
    for key in xmltv.read_channels(open(filename, 'r')):
          name = map(itemgetter(0), key['display-name'])
          id   = key['id']
          src  = key['icon'][0]['src']
          name = name[0]

          rec = dict(zip(Channel._fields, [id, name, src]))
          channel = Channel(**rec)
          channels[channel.id] = channel

    return channels 

CHANNELS = channels()

def create_channel(id):
    return CHANNELS[id]

def format_time(timestamp):
    return datetime.datetime.strptime(timestamp[:12], "%Y%m%d%H%M%S")

if __name__ == "__main__":
    for key in xmltv.read_programmes(open(filename, 'r')):
        channel = create_channel(key['channel'])
        titles = map(itemgetter(0), key['title'])
        
        print "%s - %s - %s - %s" % (titles[0], channel.name, format_time(key['start']), format_time(key['stop'])) 
