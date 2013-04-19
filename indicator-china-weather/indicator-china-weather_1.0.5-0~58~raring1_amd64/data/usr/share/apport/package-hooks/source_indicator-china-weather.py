from apport.hookutils import *
import os.path

def add_info(report, ui=None):
    if not apport.packaging.is_distro_package(report['Package'].split()[0]):
        report['ThirdParty'] = 'True'
        report['CrashDB'] = 'indicator_china_weather'
    report['Settings'] = command_output(['gsettings', 'list-recursively', 'apps.indicators.chinaweather'])
        
    log_filename = os.path.join(os.path.expanduser("~/.cache"), "indicator-china-weather.log")
    if os.path.exists(log_filename):
        report['IndicatorLog'] = open(log_filename).read()
