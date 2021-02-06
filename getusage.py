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

from agileDB import OctopusAgileDB
from agileAPI import OctopusAgileAPI
from agileTools import gen_periodno_date, date_from_periodno
from mylogger import mylogger
from config import configFile, buildFilePath
from datetime import datetime
import sys

log = None

##############################################################################
#  load_usage_data - load the usage data into the database
##############################################################################
def load_usage_data(agileDB, usage_data):
    record = 0
    result = None

    log.debug("STARTED load_usage_data ")
    if agileDB.connect_agile_db() == True:

        for result in usage_data:
            usage = result['consumption']
            raw_from = result['interval_start']

            # We need to reformat the date to a python date from a json date
            date = datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ")
            log.debug( f"Record {record:05d} YY:{date.year:4d} MM:{date.month:02d} DD:{date.day:02d} hh:{date.hour:02d} mm:{date.minute:02d} USAGE:{usage}")
        
            agileDB.update_db_period_usage (date.year, date.month, date.day, date.hour, date.minute, usage, True)
            # increment the number of records
            record += 1

    log.debug(f" completed all loads record {record}")
    result =  record
    agileDB.disconnect_agile_db()
    
    log.debug("FINISHED load_usage_data ")
    return result


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

toscreen=config.read_value('settings','agileTrigger_debug2screen')
if toscreen == None: toscreen = False
isdebug=config.read_value('settings','agile_triggerdebug')
if isdebug == None: isdebug = False

log = mylogger("getUsage",logFile,isdebug,toscreen)

log.debug("STARTED getUsage ")

my_account= OctopusAgileAPI(config,log)
my_database = OctopusAgileDB (config, log)

f_periodno = my_database.get_db_first_missing_usage()
t_periodno = gen_periodno_date(datetime.utcnow())-24

log.debug(f"f_periodno = {f_periodno} t_periodno={t_periodno}")

if  f_periodno != None and t_periodno > f_periodno:
    from_date = date_from_periodno(f_periodno)
    to_date = date_from_periodno(t_periodno)

    # Query the data from Octopus 
    usagedata = my_account.get_usage(from_date, to_date)
    # Load it into the database
    load_usage_data(my_database, usagedata)
else:
    log.info("No outstanding usage data to upload")

log.debug("FINISHED getUsage ")
