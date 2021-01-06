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

from agile import OctopusAgile
from config import configFile,buildFilePath
from agileTriggers import costTriggers
from mylogger import mylogger
from datetime import datetime

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

# setup logger
day = (datetime.utcnow()).day
logFile=buildFilePath(logPath, f"checktriggers_{day:02d}.log")
log = mylogger("checkTriggers",logFile,True)

############################################################################
#  Start of execution
############################################################################
log.debug("STARTED checkTriggers.py")

log.debug("init Octopus Agile object")
my_account = OctopusAgile(config,log,True)

log.debug("init cost Trigger object")
my_triggers= costTriggers(config,log)

############################################################################
# Get the current cost. 
############################################################################
log.debug("Query Database for current cost")
unit_cost = my_account.get_period_cost(my_account.time_now())

############################################################################
# Get the list of triggers
############################################################################
log.debug("Query Database for triggers")

trigger_list=my_triggers.get_all_triggers()
############################################################################
# iterate the list of triggers  creating or deleting file as necessary
############################################################################
log.info(" calling process triggers")

result = my_triggers.process_triggers(trigger_list, unit_cost)

log.debug("FINISHED checkTriggers.py")
