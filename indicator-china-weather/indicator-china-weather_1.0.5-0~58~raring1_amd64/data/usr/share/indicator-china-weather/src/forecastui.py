#!/usr/bin/python
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

import os, sys
import gtk
import pycwapi
import time

PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

class ExtendedForecast():
    def __init__(self, forecast_data):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'data/ui/ExtendedForecast.ui'))
        self.img_ct = self.builder.get_object("img_ct")
        self.img_uv = self.builder.get_object("img_uv")
        self.img_xc = self.builder.get_object("img_xc")
        self.img_tr = self.builder.get_object("img_tr")
        self.img_cl = self.builder.get_object("img_cl")
        self.img_ls = self.builder.get_object("img_ls")
        self.img_ag = self.builder.get_object("img_ag")
        self.img_ct.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/ct1.gif'))
        self.img_uv.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/uv1.gif'))
        self.img_xc.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/xc1.gif'))
        self.img_tr.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/tr1.gif'))
        self.img_cl.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/cl1.gif'))
        self.img_ls.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/ls1.gif'))
        self.img_ag.set_from_file(os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/ag.jpg'))

        self.window = self.builder.get_object("window")
        self.builder.connect_signals(self)
        self.window.show()
        self.forecast_data = forecast_data
        #print('forecastdate->')
        #print(self.forecast_data)

        self.builder.get_object("img1").set_from_file(self.get_weather_icon('img1'))
        self.builder.get_object("img2").set_from_file(self.get_weather_icon('img2'))
        self.builder.get_object("img3").set_from_file(self.get_weather_icon('img3'))
        self.builder.get_object("img4").set_from_file(self.get_weather_icon('img4'))
        self.builder.get_object("img5").set_from_file(self.get_weather_icon('img5'))
        self.builder.get_object("img6").set_from_file(self.get_weather_icon('img6'))
        self.builder.get_object("img7").set_from_file(self.get_weather_icon('img7'))
        self.builder.get_object("img8").set_from_file(self.get_weather_icon('img8'))
        self.builder.get_object("img9").set_from_file(self.get_weather_icon('img9'))
        self.builder.get_object("img10").set_from_file(self.get_weather_icon('img10'))
        self.builder.get_object("img11").set_from_file(self.get_weather_icon('img11'))
        self.builder.get_object("img12").set_from_file(self.get_weather_icon('img12'))

        self.builder.get_object("weather1").set_text(self.forecast_data['weather1'])
        self.builder.get_object("weather2").set_text(self.forecast_data['weather2'])
        self.builder.get_object("weather3").set_text(self.forecast_data['weather3'])
        self.builder.get_object("weather4").set_text(self.forecast_data['weather4'])
        self.builder.get_object("weather5").set_text(self.forecast_data['weather5'])
        self.builder.get_object("weather6").set_text(self.forecast_data['weather6'])

        self.builder.get_object("temp1").set_text(self.forecast_data['temp1'])
        self.builder.get_object("temp2").set_text(self.forecast_data['temp2'])
        self.builder.get_object("temp3").set_text(self.forecast_data['temp3'])
        self.builder.get_object("temp4").set_text(self.forecast_data['temp4'])
        self.builder.get_object("temp5").set_text(self.forecast_data['temp5'])
        self.builder.get_object("temp6").set_text(self.forecast_data['temp6'])
        
        self.builder.get_object("wind1").set_text(self.forecast_data['wind1'])
        self.builder.get_object("wind2").set_text(self.forecast_data['wind2'])
        self.builder.get_object("wind3").set_text(self.forecast_data['wind3'])
        self.builder.get_object("wind4").set_text(self.forecast_data['wind4'])
        self.builder.get_object("wind5").set_text(self.forecast_data['wind5'])
        self.builder.get_object("wind6").set_text(self.forecast_data['wind6'])

        self.time = time.strftime('%w', time.localtime(time.time()))
        #self.time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        #print('today is :')
        #print(self.time)
        labelofweek = ["week1", "week2", "week3", "week4", "week5", "week6"]
        dayofweek = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]
        for i in range(0,6):
            weektime = int(self.time) + i
            if weektime > 7:
                weektime -= 7
            if i == 0:
                self.builder.get_object(labelofweek[i]).set_text("今天  " + dayofweek[int(self.time)-1])
            else:
                self.builder.get_object(labelofweek[i]).set_text(dayofweek[weektime-1])

        self.img_ct.set_tooltip_text(u'24小时穿衣指数: %s\n%s\n48小时穿衣指数：%s\n%s' % (forecast_data['index'], forecast_data['index_d'], forecast_data['index48'], forecast_data['index48_d']))
        self.img_uv.set_tooltip_text(u'紫外线指数: %s' % (forecast_data['index_uv']))
        self.img_xc.set_tooltip_text(u'洗车指数: %s' % (forecast_data['index_xc']))
        self.img_tr.set_tooltip_text(u'旅游指数: %s' % (forecast_data['index_tr']))
        self.img_cl.set_tooltip_text(u'晨练指数: %s' % (forecast_data['index_cl']))
        self.img_ls.set_tooltip_text(u'晾晒指数: %s' % (forecast_data['index_ls']))
        self.img_ag.set_tooltip_text(u'过敏气象指数: %s' % (forecast_data['index_ag']))

    def get_weather_icon(self, img):
        fchh = int(self.forecast_data['fchh'])
        if 6 <= fchh < 18:
            icons_day = ('img1', 'img3', 'img5', 'img7', 'img9', 'img11')
            icons_night = ('img2', 'img4', 'img6', 'img8', 'img10', 'img12')
        else:
            icons_day = ('img2', 'img4', 'img6', 'img8', 'img10', 'img12')
            icons_night = ('img1', 'img3', 'img5', 'img7', 'img9', 'img11')
        if img in icons_day:
            if self.forecast_data[img] == '99':
                return os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/d') + self.forecast_data[icons_night[icons_day.index(img)]] + '.gif'
            else:
                return os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/d') + self.forecast_data[img] + '.gif'
        elif img in icons_night:
            if self.forecast_data[img] == '99':
                return os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/n') + self.forecast_data[icons_day[icons_night.index(img)]] + '.gif'
            else:
                return os.path.join(PROJECT_ROOT_DIRECTORY, 'icons/n') + self.forecast_data[img] + '.gif'

if __name__ == "__main__":
    forecast_data = pycwapi.get_weather_from_nmc(sys.argv[1], 1)
    forecastpage = ExtendedForecast(forecast_data)
    forecastpage.window.show()
    gtk.main()
