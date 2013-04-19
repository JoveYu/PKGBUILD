#!/usr/bin/env python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
# Copyright (C) 2010 Mehdi Rejraji mehd36@gmail.com
# Copyright (C) 2011 Vadim Rutkovsky roignac@gmail.com
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

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

import os, sys
try:
    import DistUtilsExtra.auto
except ImportError:
    print >> sys.stderr, 'To build indicator-weather you need https://launchpad.net/python-distutils-extra'
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', 'needs DistUtilsExtra.auto >= 2.18'

def update_data_path(prefix, oldvalue=None):

    try:
        fin = file('indicator_weather/indicator_weatherconfig.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__indicator_weather_data_directory__':
                # update to prefix, store oldvalue
                if not oldvalue:
                    oldvalue = fields[1]
                    line = "%s = '%s'\n" % (fields[0], prefix)
                else: # restore oldvalue
                    line = "%s = %s" % (fields[0], oldvalue)
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find indicator_weather/indicator_weatherconfig.py")
        sys.exit(1)
    return oldvalue


def update_desktop_file(datadir):
    try:
        fin = file('indicator-weather.desktop.in', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            if 'Icon=' in line:
                line = "Icon=%s\n" % (datadir + 'media/icon.png')
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find indicator-weather.desktop.in")
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        previous_value = update_data_path(self.prefix + '/share/indicator-weather/')
        update_desktop_file(self.prefix + '/share/indicator-weather/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_data_path(self.prefix, previous_value)
        
##################################################################################
###################### YOU SHOULD MODIFY ONLY WHAT IS BELOW ######################
##################################################################################

DistUtilsExtra.auto.setup(
    name='indicator-weather',
    version='11.05.31',
    license='GPL-3',
    author='Vadim Rutkovsky | Sebastian MacDonald | Mehdi Rejraji',
    author_email='roignac@gmail.com',
    description="A weather indicator for Ubuntu's Indicator Applet",
    long_description='A weather indicator that displays information for one or multiple places in the world',
    url='https://launchpad.net/weather-indicator',
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )
