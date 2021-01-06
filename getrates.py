########################################################################
# getrates.py - Core application file for the daily update of the 
# database for forward pricing using calls to the Ocotpus energy API to 
# get forward looking prices for a smart meter running on the Octopus 
# Agile Tarriff. the App is predicated on 30 minute pricing. 
# The API is documented here: https://developer.octopus.energy/docs/api/
#
# Copyright 2020 Simon McKenna.
#
# Licensed under the Apache License, Version 2.0 (the "License");
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########################################################################

from agile import OctopusAgile
from config import configFile,buildFilePath
from mylogger import mylogger
from datetime import datetime, date
import os
import sys

# build the config path
configPath=buildFilePath('~',".agileTriggers.ini")
if  configPath == False:
    print (f" getRates abandoned execution config file missing:{configPath}") 
    raise sys.exit(1)
else:
    config=configFile(configPath)

logPath=config.read_value('filepaths','log_folder')
day = (datetime.utcnow()).day
logPath=buildFilePath(logPath,f"getRates_{day:02d}.log")

if logPath != None:
    log = mylogger("getRates",logPath,True)
else:
    print ("getRates abandoned execution log path missing:") 
    raise sys.exit(1)

log.debug("in getRates.py starting agile init")

my_account=OctopusAgile( config, log)

log.debug("in getRates.py post agile init")

rates = my_account.get_current_rates()

log.debug("in getRates.py post get_rates")

result = my_account.load_rate_data(rates)

log.debug("in getRates.py post load_rates")
