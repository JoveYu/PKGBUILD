#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
# Copyright (C) 2010 Mehdi Rejraji mehd36@gmail.com
# Copyright (C) 2011 Vadim Rutkovsky roignac@gmail.com
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

try:
    from gi.repository import Gio
except ImportError:
    pass
import os, sys, shutil, tempfile
import gtk, pygtk, gobject
import commands, threading
import appindicator
import logging, logging.handlers
import traceback
import types
import time
import string
from xml.dom.minidom import parseString
import pycwapi
import forecastui
from helpers import *
from pm25 import *
import gettext
from gettext import gettext as _
from gettext import ngettext as __

VERSION = "1.0.5"

# Add project root directory (enable symlink, and trunk execution).
PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

CHN_CITY_LIST_FILE = os.path.join(PROJECT_ROOT_DIRECTORY, 'src/location.txt')

INFO_TYPE            = 'type'
INFO_SETTING         = 'setting'
class Settings:
    db = None
    BASE_KEY             = 'apps.indicators.chinaweather'
    REFRESH_RATE         = 'refresh_rate'
    CITY_KEY             = 'city_id'
    TEMPERATURE_KEY      = 'show_temperature'
    PLACES               = 'places'
    PLACECHOSEN          = 'placechosen'

    INFO = {
        REFRESH_RATE : {
            INFO_TYPE : types.IntType,
            INFO_SETTING : 'refresh-rate'
        },
        CITY_KEY : {
            INFO_TYPE : types.StringType,
            INFO_SETTING : 'city-id'
        },
        TEMPERATURE_KEY : {
            INFO_TYPE : types.BooleanType,
            INFO_SETTING : 'show-temperature'
        },
        PLACES : {
            INFO_TYPE : types.ListType,
            INFO_SETTING: 'places'
        },
        PLACECHOSEN : {
            INFO_TYPE : types.IntType,
            INFO_SETTING: 'placechosen'
        },
    }

    # Open the DB
    def prepare_settings_store(self):
        log.debug("Settings: preparing settings store")
        try:
            self.db = Gio.Settings.new(self.BASE_KEY)
        except Exception as e:
            log.debug("Settings: exception occurred while opening settings:\n %s" % str(e))

    def get_value(self, setting, return_id = False):
        setting_name = Settings.INFO[setting][INFO_SETTING]
        try:
            setting_type = Settings.INFO[setting][INFO_TYPE]
            get_func = {
                types.IntType:     self.db.get_int,
                types.StringType:  self.db.get_string,
                types.BooleanType: self.db.get_boolean,
                types.ListType:    self.db.get_string,
                types.DictType:    self.db.get_string,
                types.NoneType:    self.db.get_value,
            }[setting_type]
            return get_func(setting_name)
        except:
            log.debug("Settings: can't find value for %s" % setting)
            return None

    def set_value(self, setting, value):
        value = '' if value is None else value
        value = str(value) if type(value) is types.ListType else value
        log.debug("Settings: setting '%s'='%s'" % (setting, value))
        setting_name = Settings.INFO[setting][INFO_SETTING]
        try:
            setting_type = Settings.INFO[setting][INFO_TYPE]
            set_func = {
                types.IntType:     self.db.set_int,
                types.StringType:  self.db.set_string,
                types.BooleanType: self.db.set_boolean,
                types.ListType:    self.db.set_string,
                types.DictType:    self.db.set_string,
                types.NoneType:    self.db.set_value,
            }[setting_type]
            set_func(setting_name, value)
        except:
            log.debug( \
                "Settings: schema for '%s' not found, aborting" % setting)

class indicator_weather(threading.Thread):
    """ Indicator class """

    def __init__(self):
        from pycwapi import get_location_from_cityid
        log.debug("Indicator: creating")
        threading.Thread.__init__(self)
        self.main_icon = os.path.join
        self.winder = appindicator.Indicator ("indicator-china-weather", "weather-indicator", appindicator.CATEGORY_OTHER)
        self.winder.set_status (appindicator.STATUS_ACTIVE)
        self.winder.set_attention_icon ("weather-indicator-error")

        self.settings = Settings()
        self.settings.prepare_settings_store()
        self.city_id = self.settings.get_value("city_id")
        self.temp = self.settings.get_value("show_temperature")
        self.rate = self.settings.get_value("refresh_rate")
        self.city_change_flag = False
        if self.rate in (False, None):
            default_value = 15
            self.settings.set_value("refresh_rate", default_value)
            self.rate = default_value

        self.aboutdialog = None
        self.weather_data={}
        self.forecast_data={}
        self.icon = None
        self.menu = None
        self.place = None
        self.pm = {}
        self.places = str(self.settings.get_value("places"))
        self.placechosen = self.settings.get_value("placechosen")
        self.actualization_time = 0        

        #(LP: #1153468)
        if self.city_id not in (False, None, '', '[]', "['']") and self.places in (False, None, '', '[]', "['']"):
            #self.city_id = ''
            #self.settings.set_value("city_id", self.city_id)
            locations = get_location_from_cityid(self.city_id)
            self.places = [[self.city_id, locations]]
            self.settings.set_value("places", str(self.places))
            self.places = str(self.settings.get_value("places"))

        self.weather_icons={
            'd0.gif':'weather-clear',
            'd1.gif':'weather-few-clouds',
            'd2.gif':'weather-few-clouds',
            'd3.gif':'weather-showers',
            'd4.gif':'weather-showers',
            'd5.gif':'weather-showers',
            'd6.gif':'weather-snow',
            'd7.gif':'weather-showers',
            'd8.gif':'weather-showers',
            'd9.gif':'weather-showers',
            'd10.gif':'weather-showers',
            'd11.gif':'weather-showers',
            'd12.gif':'weather-showers',
            'd13.gif':'weather-snow',
            'd14.gif':'weather-snow',
            'd15.gif':'weather-snow',
            'd16.gif':'weather-snow',
            'd17.gif':'weather-snow',
            'd18.gif':'weather-fog',
            'd19.gif':'weather-snow',
            'd20.gif':'weather-fog',
            'd21.gif':'weather-showers',
            'd22.gif':'weather-showers',
            'd23.gif':'weather-showers',
            'd24.gif':'weather-showers',
            'd25.gif':'weather-showers',
            'd26.gif':'weather-snow',
            'd27.gif':'weather-snow',
            'd28.gif':'weather-snow',
            'd29.gif':'weather-fog',
            'd30.gif':'weather-fog',
            'd31.gif':'weather-fog',
            'd53.gif':'weather-fog',
            'n0.gif':'weather-clear-night',
            'n1.gif':'weather-few-clouds-night',
            'n2.gif':'weather-few-clouds-night',
            'n3.gif':'weather-showers',
            'n4.gif':'weather-showers',
            'n5.gif':'weather-showers',
            'n6.gif':'weather-snow',
            'n7.gif':'weather-showers',
            'n8.gif':'weather-showers',
            'n9.gif':'weather-showers',
            'n10.gif':'weather-showers',
            'n11.gif':'weather-showers',
            'n12.gif':'weather-showers',
            'n13.gif':'weather-snow',
            'n14.gif':'weather-snow',
            'n15.gif':'weather-snow',
            'n16.gif':'weather-snow',
            'n17.gif':'weather-snow',
            'n18.gif':'weather-fog',
            'n19.gif':'weather-showers',
            'n20.gif':'weather-fog',
            'n21.gif':'weather-showers',
            'n22.gif':'weather-showers',
            'n23.gif':'weather-showers',
            'n24.gif':'weather-showers',
            'n25.gif':'weather-showers',
            'n26.gif':'weather-snow',
            'n27.gif':'weather-snow',
            'n28.gif':'weather-snow',
            'n29.gif':'weather-fog',
            'n30.gif':'weather-fog',
            'n31.gif':'weather-fog',
            'n53.gif':'weather-fog'
        }

        if self.city_id in (False, None, '[]', ''):
            self.menu_noplace()
        else:#(LP: #1153906)
            self.places = eval(self.places)
            if self.placechosen >= len(self.places):
                self.placechosen = 0
            self.place = self.places[self.placechosen]
            self.menu_normal()
            self.update_data()
            #self.place = get_location_from_cityid(self.city_id)
            #self.pm = get_pm_from_city(self.place.split(',')[2])
        # fix bug about update time (LP: #1131556)
        gobject.timeout_add_seconds(60,self.work)

    # Show a menu if no places specified
    def menu_noplace(self):
        log.debug("Indicator: making a menu for no places")
        menu_noplace = gtk.Menu()

        setup = gtk.MenuItem(_("配置地点..."))
        setup.connect("activate", self.prefs)
        menu_noplace.append(setup)
        setup.show()

        about = gtk.MenuItem(_("关于..."))
        about.connect("activate", self.about)
        about.show()
        menu_noplace.append(about)

        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.show()
        menu_noplace.append(quit)

        self.winder.set_menu(menu_noplace)

    # Show menu with data
    def menu_normal(self):
        log.debug("Indicator: menu_normal: filling in a menu for found places")
        self.menu = gtk.Menu()

        ##City
        self.city_show = gtk.MenuItem(_("城市:N/A"))
        self.city_show.set_sensitive(True)
        self.city_show.show()
        self.menu.append(self.city_show)

        ##Weather
        self.weather_show = gtk.MenuItem(_("天气:N/A"))
        self.weather_show.set_sensitive(True)
        self.weather_show.show()
        self.menu.append(self.weather_show)
        
        ##Temperature
        self.temp_show = gtk.MenuItem(_("当前气温:N/A"))
        self.temp_show.set_sensitive(True)
        self.temp_show.show()
        self.menu.append(self.temp_show)

        ##HighTemp
        #self.temp1_show = gtk.MenuItem()
        #self.temp1_show.set_sensitive(True)
        #self.temp1_show.show()
        #self.menu.append(self.temp1_show)

        ##LowTemp
        #self.temp2_show = gtk.MenuItem()
        #self.temp2_show.set_sensitive(True)
        #self.temp2_show.show()
        #self.menu.append(self.temp2_show)
        
        ##Humidity
        self.SD_show = gtk.MenuItem(_("湿度:N/A"))
        self.SD_show.set_sensitive(True)
        self.SD_show.show()
        self.menu.append(self.SD_show)

        ##Wind Direction
        self.WD_show = gtk.MenuItem(_("风向:N/A"))
        self.WD_show.set_sensitive(True)
        self.WD_show.show()
        self.menu.append(self.WD_show)

        ##Wind Strength
        self.WS_show = gtk.MenuItem(_("风力:N/A"))
        self.WS_show.set_sensitive(True)
        self.WS_show.show()
        self.menu.append(self.WS_show)
        
        ##Update Time
        self.time_show = gtk.MenuItem(_("更新时间:N/A"))
        self.time_show.set_sensitive(True)
        self.time_show.show()
        self.menu.append(self.time_show)

        self.pm_show = gtk.MenuItem(_("PM2.5:N/A"))
        self.pm_show.set_sensitive(True)
        self.pm_show.show()
        self.menu.append(self.pm_show)

        ##Update Button
        #self.refresh_show = gtk.MenuItem()
        #self.refresh_show.connect("activate", self.update_data)
        #self.refresh_show.show()
        #self.menu.append(self.refresh_show)

        ##Breaker
        breaker = gtk.SeparatorMenuItem()
        breaker.show()
        self.menu.append(breaker)

        ##Cities
        if len(self.places) != 1:
            log.debug("Indicator: menu_normal: adding first location menu item '%s'" % self.places[0][1])
            loco1 = gtk.RadioMenuItem(None, self.places[0][1])
            if self.placechosen == 0:
                loco1.set_active(True)
            loco1.connect("toggled", self.on_city_changed)
            loco1.show()
            self.menu.append(loco1)
            for place in self.places[1:]:
                log.debug("Indicator: menu_normal: adding location menu item '%s'" % place[1])
                loco = gtk.RadioMenuItem(loco1, place[1])
                if self.places.index(place) == self.placechosen:
                    loco.set_active(True)
                loco.connect("toggled", self.on_city_changed)
                loco.show()
                self.menu.append(loco)
            breaker = gtk.SeparatorMenuItem()
            breaker.show()
            self.menu.append(breaker)

        ext_show = gtk.MenuItem(_("天气预报"))
        ext_show.connect("activate", self.forecast)
        ext_show.show()
        self.menu.append(ext_show)    

        ##Update Button
        self.refresh_show = gtk.MenuItem(_("更新"))
        self.refresh_show.connect("activate", self.update_data)
        self.refresh_show.show()
        self.menu.append(self.refresh_show)

        ##Preferences
        prefs_show = gtk.MenuItem(_("配置..."))
        prefs_show.connect("activate", self.prefs)
        prefs_show.show()
        self.menu.append(prefs_show)

        ##About
        about_show = gtk.MenuItem(_("关于..."))
        about_show.connect("activate", self.about)
        about_show.show()
        self.menu.append(about_show)

        ##Quit
        quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.show()
        self.menu.append(quit)

        self.winder.set_menu(self.menu)
        self.update_label(" ")
        self.work()

    def on_city_changed(self,widget):
        if widget.get_active():
            for place in self.places:
                if (place[1] == widget.get_label()):
                    log.debug("Indicator: new location selected: %s" % self.places.index(place))
                    self.placechosen = self.places.index(place)
                    break

            if self.placechosen >= len(self.places):
                self.placechosen = 0
            self.place = self.places[self.placechosen]
            self.settings.set_value("placechosen", self.placechosen)
            self.city_id = self.places[self.placechosen][0]
            self.settings.set_value("city_id", self.city_id)
            self.update_data()

    # Set a label of indicator
    def update_label(self, label):
        if (hasattr(self.winder, 'set_label')):
            log.debug("Indicator: update_label: setting label to '%s'" % label)
            self.previous_label_value = label
            self.winder.set_label(label)
            self.winder.set_status(appindicator.STATUS_ATTENTION)
            self.winder.set_status(appindicator.STATUS_ACTIVE)

    # Quit the applet
    def quit(self, widget, data=None):
        log.debug("Indicator: Quitting")
        gtk.main_quit()

    # Get forecast
    def get_forecast(self):
        log.debug("Indicator: getForecast: getting forecast for %s" % self.city_id)
        try:
            self.forecast_data = pycwapi.get_weather_from_nmc(self.city_id, 1)
        except Exception, e:
            log.error(e)
            log.debug(traceback.format_exc(e))

    # Get and set weather
    def get_set_weather(self):
        log.debug("Indicator: updateWeather: updating weather for %s" % self.city_id)
        try:
            self.weather_data = pycwapi.get_weather_from_nmc(self.city_id, 0)
            if self.weather_data is not None:
                log.debug("Indicator: loading weather from cache for %s" % self.city_id)
            
                self.ptime = self.weather_data['ptime']
                pint = string.atoi(self.ptime.split(':')[0])
                if pint > 7 or pint < 20:
                    self.icon = self.weather_icons[self.weather_data['img1']]
                else :
                    self.icon = self.weather_icons[self.weather_data['img2']]
                self.menu_normal()
                self.winder.set_icon(self.icon)
                self.city_show.set_label(self.weather_data['city'])
                self.weather_show.set_label(_('天气:') + self.weather_data['weather'])
                self.temp_show.set_label(_('当前气温:') + self.weather_data['temp'] + '℃')
                #self.temp1_show.set_label(_('最高气温:') + self.weather_data['temp1'])
                #self.temp2_show.set_label(_('最低气温:') + self.weather_data['temp2'])
                self.SD_show.set_label(_('湿度:') + self.weather_data['SD'])
                self.WD_show.set_label(_('风向:') + self.weather_data['WD'])
                self.WS_show.set_label(_('风力:') + self.weather_data['WS'])
                self.time_show.set_label(_('发布时间:') + self.weather_data['time'])
                #self.refresh_show.set_label(_('更新'))

                #city = self.place.split(',')[2]
                #self.pm = get_pm_from_city(city)
                if self.pm in (False, None, '', '[]', "['']"):#(LP: #1152853)
                    self.pm = {}
                pm_flag = False
                if self.pm.has_key('aqi') and self.pm.has_key('quality'):
                    pm_flag = True
                if not pm_flag:
                    self.pm_show.set_label(_('PM2.5:') + 'N/A')
                else:
                    if self.pm.has_key('error'):
                        self.pm_show.set_label(_('PM2.5:') + 'N/A')
                    else:
                        self.pm_show.set_label(_('PM2.5:') + self.pm['quality'] + ' ' +  str(self.pm['aqi']))

                if self.temp:
                    self.update_label(self.weather_data['temp'] + '℃')
                self.winder.set_status(appindicator.STATUS_ATTENTION)
                self.winder.set_status(appindicator.STATUS_ACTIVE)
        except Exception, e:
            log.error(e)
            log.debug(traceback.format_exc(e))
        self.schedule_weather_update()

    # Get PM2.5 information from website
    def get_pm_info(self):
        from pycwapi import get_location_from_cityid
        try:
            #self.place = get_location_from_cityid(self.city_id)
            self.pm = get_pm(self.place[1].split(',')[2])
            if self.pm.has_key('error'):
                self.pm_show.set_label(_('PM2.5:') + 'N/A')
            else:
                self.pm_show.set_label(_('PM2.5:') + self.pm['quality'] + ' ' +  str(self.pm['aqi']))
        except Exception, e:
            log.error(e)
            log.debug(traceback.format_exc(e))
    
    # update time
    def work(self):
        ut = int(round((time.time()-self.actualization_time)/60.0,0))
        if self.actualization_time == 0 or ut == 0:
            msg = '刚刚'
        else:
            msg = str(ut)+'分钟之前'
        self.refresh_show.set_label('更新'+' ('+msg+')')
        if (time.time()-self.actualization_time) > self.rate*60:
            self.actualization_time = time.time()
        return True

    # Update weather and forecast
    def update_data(self, widget = None):
        threading.Thread(target=self.get_set_weather, name='Weather').start()
        threading.Thread(target=self.get_forecast, name='Forecast').start()
        threading.Thread(target=self.get_pm_info, name='PM25').start()
        self.actualization_time = 0
        self.work()


    # Menu callbacks
    # Open Preferences dialog
    def prefs(self, widget):
        log.debug("Indicator: open Preferences")
        if ((not hasattr(self, 'prefswindow')) or (not self.prefswindow.get_visible())):
            self.prefswindow = PreferencesDialog()
            self.prefswindow.show()

    def about(self, widget):
        log.debug("Indicator: open About dialog")
        if self.aboutdialog == None:#(LP: #1154085)
            self.aboutdialog = gtk.AboutDialog()
            self.aboutdialog.set_name(_("Indicator China Weather"))
            self.aboutdialog.set_version(VERSION)
            self.aboutdialog.set_copyright('Copyright (C) 2013 UbuntuKylin Team kobe24_lixiang@126.com')

            self.aboutdialog.set_comments(_('天气插件：提供来自于中国气象局的六天天气预报信息，添加\n人们日益关注的PM2.5指数，支持多城市切换和数据自动更新,\n分享每日生活指数和建议，为用户日常起居和旅行提供参考。'))

            ifile = open(os.path.join(PROJECT_ROOT_DIRECTORY, "COPYING"), "r")
            self.aboutdialog.set_license(ifile.read().replace('\x0c', ''))
            ifile.close()

            self.aboutdialog.set_website("https://launchpad.net/indicator-china-weather")
            self.aboutdialog.set_documenters(['Zhang Zhao <vaguedream@hotmail.com>', 'yanwang <yiwuhehe@163.com>', 'binghe <kylinhebing@163.com>'])
            self.aboutdialog.set_artists(['Ou Yangyu'])
            logo_path = os.path.join(PROJECT_ROOT_DIRECTORY, "data/media/chinaweather.png")
            self.aboutdialog.set_logo(gtk.gdk.pixbuf_new_from_file(logo_path))

            self.aboutdialog.connect("response", self.about_close)
            self.aboutdialog.show()

    def about_close(self, widget, event=None):
        log.debug("Indicator: closing About dialog")
        self.aboutdialog.destroy()
        self.aboutdialog = None

    # Schedule weather update
    def schedule_weather_update(self, rate_override = None):
        if hasattr(self, "rate_id"):
            gobject.source_remove(self.rate_id)
        if rate_override:
            self.rate_id = gobject.timeout_add(
                int(rate_override) * 60000, self.update_data)
        else:
            self.rate_id = gobject.timeout_add(
                int(self.rate) * 60000, self.update_data)

    def forecast(self, widget):
        #self.get_forecast()
        self.forecastwd = forecastui.ExtendedForecast(self.forecast_data)

class PreferencesDialog(gtk.Dialog):
    """ Class for preferences dialog """
    __gtype_name__ = "PreferencesDialog"

    # Creating a new preferences dialog
    def __new__(cls):
        builder = get_builder('PreferencesDialog')
        new_object = builder.get_object("preferences_dialog")
        new_object.finish_initializing(builder)
        return new_object

	# Fill in preferences dialog with currect data
    def finish_initializing(self, builder):
        from pycwapi import get_location_from_cityid
        self.builder = builder
        self.builder.get_object('rate').set_value(float(iw.rate))
        self.show_label = self.builder.get_object('show_label') #display temperature
        self.show_label.set_active(iw.temp)
        self.spinbutton_rate = self.builder.get_object('spinbutton_rate') #update_time
        self.spinbutton_rate.set_value(float(iw.rate))

        if iw.places != None:
            for place in iw.places:
                if len(place)>1:
                    log.debug("Preferences: Places: got (%s, %s)" % (place[1], place[0]))
                    newplace = list()
                    newplace.append(place[1])
                    newplace.append(place[0])
                    newplace.append(place[0])
                    self.builder.get_object('citieslist').append(newplace)
                    self.builder.get_object('ok_button').set_sensitive(True)

        self.builder.connect_signals(self)

    # 'Remove' clicked - remove location from list
    #TODO: Update settings object
    def on_remove_location(self, widget):
        selection = self.builder.get_object('location_list').get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            model.remove(iter)
            iw.city_id = ''

        if (self.builder.get_object('citieslist').get_iter_first() == None):
            self.builder.get_object('ok_button').set_sensitive(False)

    # 'Add' clicked - create a new Assistant
    def on_add_location(self, widget):
        if ((not hasattr(self, 'assistant')) or (not self.assistant.get_visible())):
		    self.assistant = Assistant()
		    self.assistant.show()

	# 'OK' clicked - save settings
    def ok(self, widget, data=None):
        need_to_update = False
        #City id
        if iw.city_change_flag:
            iw.city_change_flag = False
            need_to_update = True

        #Show temperature
        new_show_label = self.builder.get_object('show_label').get_active()
        if (iw.temp != new_show_label):
            iw.temp = new_show_label
            iw.settings.set_value("show_temperature", new_show_label)
            need_to_update = True

        #Update time
        rate_value = self.spinbutton_rate.get_text()
        if int(rate_value) != iw.rate:
            iw.settings.set_value("refresh_rate", int(rate_value))
            iw.rate = int(rate_value)
            need_to_update = True

        # Get places from location list
        newplaces = list()
        item = self.builder.get_object('citieslist').get_iter_first()
        while (item != None):
            newplace = list()
            newplace.append(self.builder.get_object('citieslist').get_value (item, 1))
            newplace.append(self.builder.get_object('citieslist').get_value (item, 0))
            newplaces.append(newplace)
            item = self.builder.get_object('citieslist').iter_next(item)
        # If places have changed - update weather data
        if newplaces != iw.places:
            iw.places = newplaces
            log.debug("Preferences: Places changed to '%s'" % str(iw.places))
            iw.settings.set_value("places", str(iw.places))
            if (type(iw.place) != None) and (iw.place in iw.places):
                iw.placechosen = iw.places.index(iw.place)
                iw.city_id = iw.place[0]
            else:
                iw.placechosen = 0
                iw.settings.set_value("placechosen", str(iw.placechosen))
                iw.place = iw.places[0]
                iw.city_id = iw.places[0][0]
            log.debug("Preferences: Place Chosen changed to '%s'" % iw.placechosen)
            iw.settings.set_value("city_id", str(iw.city_id))
            iw.settings.set_value("placechosen", iw.placechosen)
            iw.menu_normal()
            need_to_update = True

        if need_to_update:
            iw.update_data()
        self.destroy()

    # 'Cancel' click - forget all changes
    def cancel(self, widget, data=None):
        self.destroy()

class Assistant(gtk.Assistant):
    """ Class for a wizard, which helps to add a new location in location list """
    __gtype_name__ = "Assistant"

    # Create new object
    def __new__(cls):
        builder = get_builder('Assistant')
        new_object = builder.get_object("assistant")
        new_object.finish_initializing(builder)
        return new_object

    # Finish UI initialization - prepare combobox
    def finish_initializing(self, builder):
        self.builder = builder
        self.builder.connect_signals(self)
        self.assistant = self.builder.get_object("assistant")
        self.assistant.set_page_complete(self.builder.get_object("label"),True)
        self.assistant.set_page_complete(self.builder.get_object("review"),True)

        # Set up combobox
        self.store = gtk.ListStore(str)
        self.location_input_combo = self.builder.get_object("combolocations")
        self.location_input_combo.set_model(self.store)
        self.location_input_combo.set_text_column(0)
        self.location_entry = self.builder.get_object("entrylocation")
        self.place_selected = None
        self.location = None
        self.cityid = ''
        self.dict = {}

        self.assistant.set_forward_page_func(self.next_page)

    # 'Get cities' button clicked - get suggested cities list
    def on_get_city_names(self, widget):
        new_text = self.location_entry.get_text()
        new_text = new_text.lower().replace(' ', '')
        self.store.clear()
        f = open(CHN_CITY_LIST_FILE, 'r')
        self.dist = {}
        for line in f.readlines():
            if new_text in line:
                keys = line.split(':')[0]
                values = line.split(':')[1]
                self.store.append([keys])
                self.dict[keys] = values
                self.location_input_combo.popup()

    # A city is selected from suggested list
    def on_select_city(self, entry):
        if self.location_input_combo.get_active() != -1:
            self.place_selected = self.store[self.location_input_combo.get_active()]
            self.assistant.set_page_complete(self.builder.get_object("placeinput"),True)
            self.context = self.location_entry.get_text()
            for key in self.dict:
                if key == self.context:
                    self.cityid = self.dict[key]
                    break
        else:
            self.place_selected = None
            self.location = None
            self.assistant.set_page_complete(self.builder.get_object("placeinput"), False)

    # Create a location object out of a selected location
    def next_page(self, current_page):
        if (self.assistant.get_current_page() == 0) and not self.location and self.place_selected:
            text = self.place_selected[0]
            self.builder.get_object("entrylbl").set_text(text)
        elif self.assistant.get_current_page() == 1:
            # Confirmation page
            lbl = self.builder.get_object("entrylbl").get_text()
            # If empty label was input, set label to short city name
            if lbl == '':
                lbl = self.place_selected[0]
            self.builder.get_object("lbl3").set_label(_('标签:'))
            self.builder.get_object("labellbl").set_label('<b>%s</b>' % lbl)
            self.builder.get_object("placelbl").set_label('<b>%s</b>' % self.place_selected[0])
        return self.assistant.get_current_page() + 1

    # 'Cancel' clicked
    def on_cancel(self,widget):
        self.destroy()

    # 'Apply' clicked - save location details, add an entry in a location list
    def on_apply(self,widget):
        if self.cityid != iw.city_id:
            iw.city_change_flag = True
        else:
            iw.city_change_flag = False
        iw.city_id = self.cityid
        iw.place = [self.cityid,self.context]
        iw.settings.set_value("city_id", self.cityid)

        if iw.places not in (False, None, '', '[]', "['']") and iw.place in iw.places and iw.prefswindow.builder.get_object('citieslist').get_iter_first() != None:
            iw.placechosen = iw.places.index(iw.place)
        else:
            newplace = list()
            newplace.append(self.context)#Label
            newplace.append(self.cityid)#City
            newplace.append(self.cityid)#details
            #iw.pm = get_pm_from_city(iw.place.split(',')[2])
            item = iw.prefswindow.builder.get_object('citieslist').get_iter_first()
            #iw.prefswindow.builder.get_object('citieslist').clear()
            iw.prefswindow.builder.get_object('citieslist').append(newplace)

        # Enable 'OK' button in Preferences
        iw.prefswindow.builder.get_object('ok_button').set_sensitive(True)
        self.hide()

#ensure that single instance of applet is running for each user
class SingleInstance(object):
    
    #Initialize, specifying a path to store pids
    def __init__(self,pidPath):
        
        self.pidPath = pidPath
        if os.path.exists(pidPath):
            log.debug("SingleInstance: pid file %s exists" % pidPath)
            # Make sure it is not a "stale" pidFile
            pid = open(pidPath, 'r').read().strip()
            # Check list of running pids, if not running it is stale so overwrite

            pidRunning = commands.getoutput('ls -1 /proc | grep ^%s$' % pid)
            log.debug("SingleInstance: pid running %s" % pidRunning)
            self.lasterror = True if pidRunning else False
        else:
            self.lasterror = False

        if not self.lasterror:
            log.debug("SingleInstance: writing new pid %s" % str(os.getpid()))
            # Create a temp file, copy it to pidPath and remove temporary file
            (fp, temp_path) = tempfile.mkstemp()
            try:
                os.fdopen(fp, "w+b").write(str(os.getpid()))
                shutil.copy(temp_path, pidPath)
                os.unlink(temp_path)
            except Exception as e:
                log.error("SingleInstance: exception while renaming '%s' to '%s':\n %s" % (temp_path, pidPath, str(e)))
    def is_already_running(self):
         return self.lasterror

    def __del__(self):
         if not self.lasterror:
            log.debug("SingleInstance: deleting %s" % self.pidPath)
            os.unlink(self.pidPath)


def main():

    gtk.main()
    return 0

if __name__ == "__main__":
    # Enable and configure logs
    global log
    cachedir = os.environ.get('XDG_CACHE_HOME','').strip()
    if not cachedir:
        cachedir = os.path.expanduser("~/.cache")
    log_filename = os.path.join(cachedir, "indicator-china-weather.log")
    log = logging.getLogger('IndicatorChinaWeather')
    log.propagate = False
    log.setLevel(logging.DEBUG)
    log_handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=1024*1024, backupCount=5)
    log_formatter = logging.Formatter("[%(threadName)s] %(asctime)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)

    log.info("------------------------------")
    #log.info("Started Weather Indicator from %s" % PROJECT_ROOT_DIRECTORY)
    #log.info("Weather Indicator version %s" % VERSION)

    # Single instance stuff for weather indicator
    myapp = SingleInstance("/tmp/indicator-china-weather-%d.pid" % os.getuid())
    # check is another instance of same program running
    if myapp.is_already_running():
        log.info("Another instance of this program is already running")
        sys.exit(_("Another instance of this program is already running"))

    # Set http proxy support
    ProxyMonitor.monitor_proxy(log)
    # Use date-time format as in indicator-datetime
    TimeFormatter.monitor_indicator_datetime(log)
    # not running, safe to continue...
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()

    iw = indicator_weather()
    main()
    gtk.gdk.threads_leave()
