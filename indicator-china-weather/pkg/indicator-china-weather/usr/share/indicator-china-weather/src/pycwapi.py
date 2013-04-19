#!/usr/bin/python2
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2013 National University of Defense Technology(NUDT) & Kylin Ltd
# Authors: Zhang Zhao vaguedream@hotmail.com
#          Kobe Lee kobe24_lixiang@126.com
#          wyan yiwuhehe@163.com
#          binghe kylinhebing@163.com
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

"""
Fetches weather reports from Chinese Weather
"""

import os, sys
import urllib2, urllib
import json

CHN_WEATHER_URL_SIMPLE1 = 'http://www.weather.com.cn/data/sk/%s.html'
CHN_WEATHER_URL_SIMPLE2 = 'http://www.weather.com.cn/data/cityinfo/%s.html'
CHN_WEATHER_URL_COMPLEX = 'http://m.weather.com.cn/data/%s.html'

CHN_WEATHER_ICON_URL_DAY = 'http://www.weather.com.cn/m/i/weatherpic/29x20/%s'
CHN_WEATHER_ICON_URL_NIGHT = 'http://www.weather.com.cn/m2/i/icon_weather/29x20/%s'

PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

CHN_CITY_LIST_FILE = os.path.join(PROJECT_ROOT_DIRECTORY, 'src/location.txt')

def read_from_url(url):
    # returns weather info by json_string
    request = urllib2.Request(url, headers={'User-Agent' : 'Magic Browser'})
    f = urllib2.urlopen(request)
    json_string = f.read()
    f.close()
    return json_string

def get_weather_from_nmc(location_id, method = 0):
    """
    Fetches weather report from NMC
    
    Parameters:
      location_id: City ID for request weather
      method: 'simple' 0 or 'complex' 1
    
    Returns:
      weather_data: a dictionary of weather data that exists in Json feed.
    """
    weather_data = {}
    if method == 0:
        url1 = CHN_WEATHER_URL_SIMPLE1 % (location_id)
        url2 = CHN_WEATHER_URL_SIMPLE2 % (location_id)
        json_string1 = read_from_url(url1)
        json_string2 = read_from_url(url2)
        parsed_json1 = json.loads(json_string1)
        parsed_json2 = json.loads(json_string2)
        for key in ('city', 'temp', 'SD', 'WD', 'WS', 'time'):
            weather_data[key] = parsed_json1['weatherinfo'][key]
        for key in ('weather', 'temp1', 'temp2', 'img1', 'img2', 'ptime'):
            weather_data[key] = parsed_json2['weatherinfo'][key]
    elif method == 1:
        url = CHN_WEATHER_URL_COMPLEX % (location_id)
        json_string = read_from_url(url)
        parsed_json = json.loads(json_string)
        tp_forecast = ('city', 'date_y', 'fchh', 'temp1', 'temp2', 'temp3', 'temp4', 'temp5', 'temp6', \
        'weather1', 'weather2', 'weather3', 'weather4', 'weather5', 'weather6', \
        'wind1', 'wind2', 'wind3', 'wind4', 'wind5', 'wind6', \
        'img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8', 'img9', 'img10', 'img11', 'img12', 'img_single', \
        'img_title1', 'img_title2', 'img_title3', 'img_title4', 'img_title5', 'img_title6', \
        'img_title7', 'img_title8', 'img_title9', 'img_title10', 'img_title11', 'img_title12', 'img_title_single', \
        'wind1', 'wind2', 'wind3', 'wind4', 'wind5', 'wind6', \
        'fx1', 'fx2', 'fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'fl6', \
        'index', 'index_d', 'index48', 'index48_d', 'index_uv', 'index_xc', 'index_tr', 'index_co', 'index_cl', 'index_ls', 'index_ag')
        for key in tp_forecast:
            weather_data[key] = parsed_json['weatherinfo'][key]
    else:
        print "Error,choose method for 0 or 1"
        exit(1)
    return weather_data

def get_location_from_cityid(cityid):
    """
    returns city location by search cityid, added by kobe
    """
    location = ''
    f = open(CHN_CITY_LIST_FILE, 'r')
    for line in f.readlines():
        if cityid in line:
            location = line.split(':')[0]
            break
    return location

if __name__ == "__main__":
    weatherinfo = get_weather_from_nmc('101281601', 0)
    cities = get_cities_from_localfile('长沙')
    print cities
    print weatherinfo
    download_icon_from_nmc('d0.gif', 'd')


