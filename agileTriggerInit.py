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

from agile import OctopusAgile
from config import configFile,buildFilePath
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

# setup logger
logFile=buildFilePath(logPath, "agileTriggerInit.log")
log = mylogger("agileTriggerInit",logFile,True)

############################################################################
#  Start of execution 
############################################################################
log.info("STARTED agileTriggerInit.py")
log.info("init Agile object")
my_account= OctopusAgile(config,log)

# cron vairiables
cron_comment="added by agileTriggerInit"
cron_command="/usr/bin/python3 "+binPath+"/getrates.py 2>&1 > "+logPath+"/cron.log"

log.info("init Agile database")
my_account.initialise_agile_db()

log.info("init crontab entry to refresh database")
my_cron = CronTab(user=True)


# get list of jobs in crontab with this comment.
my_jobs = my_cron.find_comment(cron_comment)

log.info("deleting old crontab entries")
# delete old jobs if any
for job in my_jobs:
    if job.is_valid():
        log.info("deleting: "+str(job))
        my_cron.remove(job)

# create new job Octopus publishes prices @16:05 daily
log.info("creating new crontab entry")
my_job = my_cron.new(command=cron_command)
my_job.minute.on(15)
my_job.hour.on(16)
my_job.set_comment(cron_comment)

log.info("updating cron entry settings")
my_cron.write_to_user(user=True)

log.info("FINISHED agileTriggerInit.py")
