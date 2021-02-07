########################################################################
# checkTriggers.py - This script is called at each and every period 
# change (every 30 minutes) the script is scheduled via crontab
# 
# it queries the database for any triggers based on the current cost 
# if there is a trigger (start triggers are when cost is below trigger)
#                       (stop  triggers are when cost is above trigger)
# the trigger creates (start) or deletes (stop) the triggerfile
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

from config import configFile
from agileTools import buildFilePath,time_now
from agileDB import OctopusAgileDB
from agileTriggers import costTriggers
from mylogger import mylogger
from datetime import datetime,timedelta
import signal
import time
import sys
import os

############################################################################
# Global variable that controls the trigger loop
############################################################################
trigger_continue_loop = True

############################################################################
# Signal Handler for termination signals - set the loop vairable to False
############################################################################
def signal_handler(s,f):
    global trigger_continue_loop
    trigger_continue_loop = False
    log.info(f"recieved signal {s} terminating loop")
    raise Exception("Signal Exception")


############################################################################
# main function - sit here forever 
############################################################################
def check_trigger_main(my_account,my_triggers):
    global trigger_continue_loop
    global log
    unit_cost = None
    trigger_list = None
    result = None
    tgt_minutes = 0
    tgt_seconds = 15

    log.debug("Started check_trigger_main")

    # Setup the signal handler 
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        while trigger_continue_loop == True:

            t_now = datetime.utcnow()
            log.info(f" Trigger Check started {t_now}")

            # Get the current cost. 
            log.debug("Query Database for current cost")
            unit_cost = my_account.get_db_period_cost(time_now())

            # Get the list of triggers
            log.debug("Query Database for triggers")

            trigger_list=my_triggers.get_all_triggers()

            # iterate the list of triggers  creating or deleting file as necessary
            log.debug(" calling process triggers")

            result = my_triggers.process_triggers(trigger_list, unit_cost)
            
            # find the time now in preperation for going to sleep
            t_now = datetime.utcnow()
            log.info(f" Trigger Check completed {t_now}")

            #figure out the minutes offset for the next period
            if t_now.minute >= 30:
                tgt_minutes = 0
            else:
                tgt_minutes = 30

            # We are going to sleep for 30 minutes
            t_future = t_now + timedelta(minutes=30)
            # Set the desired future time to be on the half hour (plus 15 seconds)  
            t_future = t_future.replace(minute=tgt_minutes, second=tgt_seconds)
            # less the time we have been processing (in seconds)
            seconds = (t_future - t_now).seconds

            # Sleep
            log.info(f" Sleeping until  {t_future} in {seconds} seconds")
            time.sleep(seconds)
        # End of Loop
    except:
        log.info("check_trigger_main loop terminated due to exception")

    log.debug("FINISHED check_trigger_main")

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
    print ("checkTriggers abandoned execution log path missing:")
    raise sys.exit(1)

# setup logfile name
day = (datetime.utcnow()).day
logFile=buildFilePath(logPath, f"checktriggers_{day:02d}.log")

#read parameters
toscreen=config.read_value('settings','agileTrigger_debug2screen')
if toscreen == None: toscreen = False 
else: toscreen = True

isdebug=config.read_value('settings','agileTrigger_debug')
if isdebug == None: isdebug = False
else: isdebug = True

# initialise the logger
log = mylogger("checkTriggers",logFile,isdebug,toscreen)

############################################################################
#  Start of execution
############################################################################
log.debug("STARTED checkTriggers.py")

# create agile DB object
log.debug("init Octopus Agile object")
my_account = OctopusAgileDB(config,log)

# create cost trigger object
log.debug("init cost Trigger object")
my_triggers= costTriggers(config,log)
############################################################################
#  ruh main routine
############################################################################
result = check_trigger_main(my_account,my_triggers)

log.debug("FINISHED checkTriggers.py")