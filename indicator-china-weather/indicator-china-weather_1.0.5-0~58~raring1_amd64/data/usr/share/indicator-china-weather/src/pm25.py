#!/usr/bin/env python
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

import json
import os,sys
import urllib2,urllib

beginurl = 'http://pm25.in/api/querys/pm2_5.json?city='
#city = '\xe5\x85\xb0\xe5\xb7\x9e'
token = '&token=X1K1gyCibzqxfvJQnpsi'


class Getpmdata:
	def get_url(self,cityplace):
		url = beginurl + cityplace + token
		return url
	def get_data(self,url):
		request = urllib2.Request(url, headers={'User-Agent ' : 'Magic Browser'})
		f = urllib2.urlopen(request)
		json_data = f.read()
		f.close()
		python_data = json.loads(json_data)
		#print python_data
		if isinstance(python_data,dict):
			python_need_data = python_data
		else:
			python_need_data = python_data[-1]
		return python_need_data

def get_pm(cityplace):
    try:
        ob = Getpmdata()
        url = ob.get_url(cityplace)
        pmdata = ob.get_data(url)
	return pmdata
#        print pmdata
    except Exception as e:
        print(e)
