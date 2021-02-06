########################################################################
# agileTriggerInit.py script to initialise the configuration of the 
# agileTrigger  set of python scripts for linux  to work with the 
# octopus agile Tarrif to define a set fo triggers that
# can be used for other devices to switch on and off at varying rates.
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
from agileTriggers import costTriggers
from config import configFile
from agileTools import buildFilePath
from crontab import CronTab
from mylogger import mylogger
import os
import sys

# build the config path
configPath=buildFilePath('~',".agileTriggers.ini")
if  configPath == False:
    print (f" getRates abandoned execution config file missing:{configPath}")
    raise sys.exit(1)
else:
    config=configFile(configPath)

binPath=config.read_value('filepaths','bin_folder')
if binPath == None:
    print ("getRates abandoned execution bin path missing:")
    raise sys.exit(1)

logPath=config.read_value('filepaths','log_folder')
if logPath == None:
    print ("getRates abandoned execution log path missing:")
    raise sys.exit(1)

toscreen=config.read_value('settings','agileTrigger_debug2screen')
if toscreen == None: toscreen = False
isdebug=config.read_value('settings','agile_triggerdebug')
if isdebug == None: isdebug = False

# setup logger
logFile=buildFilePath(logPath, "agileTriggerInit.log")
log = mylogger("agileTriggerInit",logFile,isdebug,toscreen)

############################################################################
#  Start of execution 
############################################################################
log.info("STARTED agileTriggerInit.py")
log.info("init Agile object")
ratetime=None

my_account= OctopusAgileDB(config,log)
log.info("init Agile database and cost/usage tables")
my_account.initialise_agile_db()

log.info("init trigger database tables")
my_trigger= costTriggers(config,log)
my_trigger.initialise_trigger_db()

log.info("Opening crontab entries")
my_cron = CronTab(user=True)

cron_comment="added by agileTriggerInit"
# get list of jobs in crontab with this comment.
my_jobs = my_cron.find_comment(cron_comment)

log.info("deleting old crontab entries")
# delete old jobs if any
for job in my_jobs:
    if job.is_valid():
        log.info("deleting: "+str(job))
        my_cron.remove(job)


# Initialise the  daily rate pull from octopus
# cron vairiables

cron_command="/usr/bin/python3 "+binPath+"/getrates.py -L 2>&1 > "+logPath+"/cron.log"

log.info("init new crontab entries to refresh database")
# create new job Octopus publishes prices @16:05 daily, but take data from config
log.info("creating new crontab entry")
my_job1 = my_cron.new(command=cron_command)
my_job1.minute.on(15)
my_job1.hour.on(16)
my_job1.set_comment(cron_comment)

# Initialise the  daily usage pull from octopus
cron_comment="added by agileTriggerInit"
cron_command="/usr/bin/python3 "+binPath+"/getusage.py 2>&1 > "+logPath+"/cron.log"
my_job2 = my_cron.new(command=cron_command)
my_job2.hour.on(0,6,12,18)
my_job2.set_comment(cron_comment)

# Initialise the  trigger check every 30 minutes
cron_comment="added by agileTriggerInit"
cron_command="/usr/bin/python3 "+binPath+"/checkTriggers.py 2>&1 > "+logPath+"/cron.log"
my_job3 = my_cron.new(command=cron_command)
my_job3.minute.on(0,30)
my_job3.set_comment(cron_comment)

log.info("updating cron entry settings")
my_cron.write_to_user(user=True)

log.info("FINISHED agileTriggerInit.py")
