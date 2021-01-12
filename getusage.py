########################################################################
# getUsage.py - Core application file for the daily update of the 
# database for historic usage using calls to the Ocotpus energy API to 
# get usage data for a smart meter running on the Octopus 
# Agile Tarriff. the App is predicated on 30 minute pricing. 
# The API is documented here: https://developer.octopus.energy/docs/api/
#
# the core database is createed and populated using getRates.py to get
# forward looking pricing this follows later (1 day) to fill in actual 
# usage in the 30 minute slots
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
from mylogger import mylogger
from config import configFile, buildFilePath
from datetime import datetime
import sys
############################################################################
#  setup config
############################################################################
# build the config path
configPath=buildFilePath('~',".agileTriggers.ini")
if  configPath == False:
    print (f"getRates abandoned execution config file missing:{configPath}")
    raise sys.exit(1)
else:
    config=configFile(configPath)

############################################################################
#  setup logger
############################################################################
logPath=config.read_value('filepaths','log_folder')
if logPath == None:
    print ("getUsage abandoned execution log path missing:")
    raise sys.exit(1)

# setup logger
day = (datetime.utcnow()).day
logFile=buildFilePath(logPath, f"getUsage_{day}.log")
log = mylogger("getUsage",logFile,True)

log.debug("STARTED getUsage ")

my_account=OctopusAgile(config,log)

f_periodno = my_account.find_first_period_usage()
t_periodno = my_account.gen_periodno_date(datetime.utcnow())-24

log.debug(f"f_periodno = {f_periodno} t_periodno={t_periodno}")
if t_periodno > f_periodno:
    from_date = my_account.date_from_periodno(f_periodno)
    to_date = my_account.date_from_periodno(t_periodno)

    usagedata = my_account.get_usage(from_date, to_date)
    usagedata = my_account.load_usage_data(usagedata)
else:
    log.info("No outstanding usage data to upload")

log.debug("FINISHED getUsage ")
