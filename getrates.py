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

from agileDB import OctopusAgileDB
from agileAPI import OctopusAgileAPI
from agileTools import time_now, builddateobj
from config import configFile,buildFilePath
from mylogger import mylogger
from datetime import datetime, date
import os
import sys
import argparse


##############################################################################
#  load_rate_data - load the rate data into the database
##############################################################################
def load_rate_data(agileDB,rate_data):
    log.debug("STARTED load_rate_data ")
    result = -1
    record = 0
    if agileDB.connect_agile_db() == True:

        for slot in rate_data:
            cost = slot['value_inc_vat']
            raw_from = slot['valid_from']
            # We need to reformat the date to a python date from a json date
            date = datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ")
            log.debug( f" Record {record:05d} YY:{date.year:4d} MM:{date.month:02d} DD:{date.day:02d} hh:{date.hour:02d} mm:{date.minute:02d} COST:"+str(cost))
            result = agileDB.create_db_period_cost(date.year, date.month, date.day, date.hour, date.minute, cost, True)
            if  result == -1:
                log.debug(f"create period cost failed - record [{record}]")
                break
            record += 1

        if result ==  -1:
            result = record

    agileDB.disconnect_agile_db()
    log.debug("FINISHED load_rate_data ")
    return result


# build the config path
configPath=buildFilePath('~',".agileTriggers.ini")
if  configPath == False:
    print (f" getRates abandoned execution config file missing:{configPath}") 
    raise sys.exit(1)
else:
    config=configFile(configPath)

logPath=config.read_value('filepaths','log_folder')

toscreen=config.read_value('settings','agileTrigger_debug2screen')
if toscreen == None: toscreen = False
isdebug=config.read_value('settings','agile_triggerdebug')
if isdebug == None: isdebug = False

day = (datetime.utcnow()).day
logPath=buildFilePath(logPath,f"getRates_{day:02d}.log")

if logPath != None:
    log = mylogger("getRates",logPath,isdebug,toscreen)
else:
    print ("getRates abandoned execution log path missing:") 
    raise sys.exit(1)

log.debug("in getRates.py starting agile init")

############################################################################
# parse the command line for cost and trigger
############################################################################
parser = argparse.ArgumentParser(description="Get the usage from Octpus Energy for the configured meter")
parser.add_argument("-E", "--end", type=str,
                    help=" Set the date to of the form dd/mm/yy")
parser.add_argument("-S", "--start", type=str,
                    help=" Set the date to of the form dd/mm/yy")

group = parser.add_mutually_exclusive_group()

group.add_argument("-L", "--latest", action="store_true",
                    help=" Get the latest data")
group.add_argument("-H", "--historic", action="store_true",
                    help=" Get the latest data")
args = parser.parse_args()

my_account=OctopusAgileAPI( config, log)

my_database=OctopusAgileDB( config, log)

datefrom=time_now()
dateto=None
valid = False

if args.latest == True:
    valid = True

if args.historic == True:
    if args.start != None:
        datefrom = builddateobj(args.start)
        if datefrom == None:
            print(f"The date from detail could not be resolved [{args.start}]")
            valid = False
        else: valid = True
    else:
        print ("Need to specify a start date")
        valid = False

    if args.end != None and valid == True:
        dateto = builddateobj(args.end)
        if dateto == None:
            print(f"The date to detail could not be resolved [{args.end}]")
            valid = True
        else: 
            # work out how many slots we are being asked for 
            daterange = dateto - datefrom
            count = int(daterange.total_seconds() / (30 * 60))
            if count > 1500: 
                print(f"Error too many records asked for {int(count/48)} days - max is 31 days")
                sys.exit()

    
if valid == True:


    log.debug("in getRates.py post agile init")

    rates = my_account.get_rates(datefrom,dateto)

    log.debug(f"getRates: post call to get_rates")

    result = load_rate_data(my_database,rates)
