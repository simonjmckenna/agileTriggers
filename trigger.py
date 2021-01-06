########################################################################
# trigger.py - command line application to manage the triggers 
# checked every 30 minutes by agileTriggers.py the tool makes sqlite calls 
# to the database to update the triggers table.
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

from config import configFile,buildFilePath
from agileTriggers import costTriggers
from mylogger import mylogger
from datetime import datetime
import sys
import argparse

#
# This script is called to add a trigger to the agile triggers
# the triggers are acted on by checkTriggers.py scheduled via crontab
# 

############################################################################
# add_trigger add the trigger to the list of triggers
############################################################################
def  add_trigger(my_triggers, trigger, cost):
     log.debug("STARTED  add_trigger")
     if args.trigger == None:
         print("addtrigger - No trigger name provided")
         raise sys.exit(1)

     if args.cost == None:
         print("addtrigger - No trigger cost provided")
         raise sys.exit(2)

############################################################################
# update_trigger update the trigger to the list of triggers
############################################################################
def  update_trigger(my_triggers, trigger, cost):
     log.debug("STARTED  update_trigger")
     if args.trigger == None:
         print("updatetrigger - No trigger name provided")
         raise sys.exit(1)

     if args.cost == None:
         print("updatetrigger - No trigger cost provided")
         raise sys.exit(2)

     if my_triggers.update_trigger(args.trigger,args.cost) == False:
        print("Failed to update Trigger")
        result = False
     else:
        result = True

     log.debug("FINISHED update_trigger")

     return result

############################################################################
# del_trigger delete the trigger from the list of triggers
############################################################################
def  del_trigger(my_triggers, trigger):
     log.debug("STARTED  del_trigger")
     if args.trigger == None:
         print("addtrigger - No trigger name provided")
         raise sys.exit(1)

     if my_triggers.del_trigger(trigger) == False:
        print("Failed to delete Trigger")
        result = False
     else:
        result = True

     log.debug("FINISHED del_trigger")

     return result

############################################################################
# list_trigger show all/one trigger from the list of triggers
############################################################################
def  list_trigger(my_triggers, trigger_name):
     log.debug("STARTED  list_trigger")
     result = False

     if trigger_name == None:
         result  = True

     triggers= my_triggers.get_all_triggers()

     if trigger_name == None: 
         print(f" cost(p)	trigger name")  
     for trigger in triggers:
         if trigger_name == None: 
              print(f"{trigger[1]:0.03f}		{trigger[0]:20s}")  
         if trigger_name == trigger[0]:
              print(f"{trigger[1]:0.03f}	{trigger[0]:20s}")  
              result=True

     log.debug("FINISHED list_trigger")

     return result

############################################################################
#  setup config
############################################################################

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
logFile=buildFilePath(logPath, "trigger.log")
log = mylogger("trigger",logFile,True)

############################################################################
#  Start of execution
############################################################################

log.debug("STARTED trigger.py")

############################################################################
# parse the command line for cost and trigger
############################################################################
parser = argparse.ArgumentParser(description="Add a trigger to the agile trigger list")
group = parser.add_mutually_exclusive_group()
group.add_argument("-A", "--add",  action="store_true",
                    help=" Add a trigger ")
group.add_argument("-D", "--delete", action="store_true",
                    help=" Delete a trigger")
group.add_argument("-L", "--list", action="store_true",
                    help="List Triggers")
group.add_argument("-U", "--update", action="store_true",
                    help="List Triggers")
parser.add_argument("-t", "--trigger", type=str,
                    help="trigger name")
parser.add_argument("-c", "--cost", type=float,
                    help="trigger cost")
args = parser.parse_args()

log.debug("init cost Trigger object")

my_triggers= costTriggers(config,log)
            
log.debug("process trigger command")

command=False
if args.add  == True:
    add_trigger(my_triggers,args.trigger,args.cost)
    command=True
if args.delete  == True:
    del_trigger(my_triggers,args.trigger)
    command=True
if args.list == True:
    list_trigger(my_triggers,args.trigger)
    command=True
if args.update == True:
    update_trigger(my_triggers,args.trigger,args.cost)
    command=True

if command == False:
   print ("use trigger --help for more information")


