########################################################################
# agileTriggers.py - Core library file for the price triggers  used 
# to trigger the triggers (creation/deletion of files) depending on the value
# passed and a trigger value (on - create file, off - delete file)
#
# the library can be used as frequently as required and the location of the
# files is defined in the ini file for the applicaiton. 
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
from agileDB import OctopusAgileDB
from mylogger import nulLogger, mylogger
from sqliteDB import sqliteDB
from agileTools import check_permission
import sys
import os

class costTriggers:
    triggers = None
    database      = None
    triggerFolder = None
    triggerPerms  = None
    dbobject      = None

##############################################################################
#  __init__ class init for costTriggers class 
##############################################################################
    def __init__ (self, theConfig, theLogger=None):
        # initialise the logfile
        if theLogger == None:
           theLogger = nulLogger()
        self.log = theLogger
        self.log.debug("STARTED __init__")

        self.__set_config(theConfig)

        if self.database == None :
            self.log.error("no database file path registered")
        else:
            self.dbobject = sqliteDB(self.database, theLogger)

        self.triggerFolder = theConfig.read_value('filepaths','trigger_folder')
        perms = theConfig.read_value('filepaths','trigger_permissions')

        permission = check_permission(perms, True)

        if self.triggerFolder == None or permission == None:
            print ("checkTriggers abandoned execution trigger path missing:")
            raise sys.exit(1)

        self.triggerPerms= int(perms,8)


        if os.path.isdir(self.triggerFolder) == False:
            try:
                os.mkdir(self.triggerFolder,self.triggerPerms)
            except OSError as error:
                print(f"checkTriggers Error - {error}")
                raise sys.exit(1)
        else:
            try:
                os.chmod(self.triggerFolder,self.triggerPerms)
            except OSError as error:
                print(f"checkTriggers Error - {error}")
                raise sys.exit(1)



        self.log.debug("FINISHED __init__ ")

##############################################################################
#  set_logger - change the logger we use
##############################################################################
    def set_logger(self,theLogger):
         self.log = theLogger

##############################################################################
#  __set_config  process the config file for data
##############################################################################
    def __set_config(self,theConfig):
        self.log.debug("STARTED __set_config")
        # First read database file
        self.database= theConfig.read_value('filepaths','database_file')
        # second key is read the trigger_folder
        self.triggerFolder= theConfig.read_value('filepaths','trigger_folder')
          
        self.log.debug("FINISHED __set_config")
        
##############################################################################
#  initialise_trigger_db - create a new trigger database  run this once
##############################################################################
    def initialise_trigger_db(self):
        data = False
        result = False
        self.log.debug("STARTED initialise_trigger_db ")
        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                # create the agile_triggers table 
                # containing a trigger_name
                #            a trigger cost, 
                #            a the trigger file
                self.log.debug("creating agile_triggers table")
                sqlite_query = 'CREATE TABLE agile_triggers (trigger_name TEXT PRIMARY KEY, cost REAL )'
                if self.dbobject.db_query(sqlite_query) == True:
                    data = True
                    self.log.debug("Created agile_triggers table")
   
                if data == True:
                    result = True

                self.dbobject.db_disconnect()
            else:
                self.log.debug("Failed to connect to agileDB agile_triggers table")
        self.log.debug("FINISHED initialise_trigger_db ")

##############################################################################
#   __start_trigger -  function to trigger a start
##############################################################################
    def __start_trigger(self,trigger_name):
        self.log.debug("STARTED  start_trigger ")
        file=os.path.join(self.triggerFolder,trigger_name)
        if os.path.exists(file) == False:
            os.mknod(file,self.triggerPerms)
        self.log.debug("FINISHED start_trigger ")
##############################################################################
#   __stop_trigger -  function to trigger a stop
##############################################################################
    def __stop_trigger(self,trigger_name):
        self.log.debug("STARTED  stop_trigger ")
        file=os.path.join(self.triggerFolder,trigger_name)
        if os.path.exists(file):
            os.remove(file)
        self.log.debug("FINISHED stop_trigger ")

##############################################################################
#   is triggered -  function to trigger a stop
##############################################################################
    def is_triggered(self,trigger_name):
        result = False
        self.log.debug("STARTED  is_triggered ")
        file=os.path.join(self.triggerFolder,trigger_name)
        if os.path.exists(file):
            result = True
        self.log.debug(f"FINISHED is_triggered  status {result}")
        return result


##############################################################################
#   process_triggers -  process all the triggers against a cost trigger
##############################################################################
    def process_triggers(self,triggers,trigger_cost):
        self.log.debug(f"STARTED  process_triggers trigger_cost={trigger_cost}")

        for trigger in triggers:
            name = trigger[0]
            cost = trigger[1]
            self.log.debug(f"trigger[{name}] cost={cost:5f}")

            if  trigger_cost >= cost :
                self.log.debug(f"trigger[{name}] STOP  trigger")
                self.__stop_trigger(name)
            else:
                self.log.debug(f"trigger[{name}] START trigger")
                self.__start_trigger(name)

        self.log.debug("FINISHED process_triggers ")

##############################################################################
#   get_all_triggers -  get the list of triggers
##############################################################################
    def get_all_triggers(self):
        triggers = None
        self.log.debug("STARTED get_all_triggers ")

        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug(f"Connected to SQLite [{self.database}]")
                sqlite_select_query = """SELECT trigger_name,cost FROM agile_triggers """

                if self.dbobject.db_query(sqlite_select_query) == True:

                    # the triggers tabel is returned from the query
                    triggers =self.dbobject.db_queryresults()
                    self.log.debug(f"Got Triggers")
                    got_triggers = True   
                else:
                    self.log.error("Failed to Get Triggers")

                self.dbobject.db_disconnect()
            else:
                self.log.error(f"Failed to connect to  agile_triggers ")

        self.log.debug("FINISHED get_all_triggers ")

        return triggers

##############################################################################
#   add_new_trigger - update the triggers with a new trigger
##############################################################################
    def add_new_trigger(self,trigger_name,cost):
        result = False
        self.log.debug("STARTED add_new_trigger ")

        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug(f"Connected to SQLite [{self.database}]")

                sqlite_insert_query = """INSERT INTO agile_triggers ('trigger_name','cost') VALUES (?,?); """
                data_tuple = (trigger_name,cost)

                if self.dbobject.db_query(sqlite_insert_query,data_tuple) == True:
                    result = True
                    self.log.debug(f"trigger data inserted")
                else:
                    self.log.error("Failed to insert Trigger")

                self.dbobject.db_disconnect()
            else:
                self.log.error(f"Failed to connect to  agile_triggers ")


        self.log.debug("FINISHED add_new_trigger ")

        return result
          
##############################################################################
#   update_trigger - update the triggers with a new trigger
##############################################################################
    def update_trigger(self,trigger_name,cost):
        result = False
        self.log.debug("STARTED update_trigger ")

        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug(f"Connected to SQLite [{self.database}]")

                sqlite_update_query = """UPDATE agile_triggers SET cost = ? WHERE trigger_name = ? """
                data_tuple = (cost, trigger_name)
                if self.dbobject.db_query(sqlite_update_query,data_tuple) == True:
                    result = True
                    self.log.debug(f"trigger [{trigger_name}] data updated")
                else:
                    self.log.error(f"Failed to update Trigger [{trigger_name}] ")

                self.dbobject.db_disconnect()
            else:
                self.log.error(f"Failed to connect to  agile_triggers ")

        self.log.debug("FINISHED update_trigger ")
          
        return result

##############################################################################
#   del_trigger - update the triggers table deleting a trigger
##############################################################################
    def del_trigger(self,trigger_name):
        result = False
        self.log.debug("STARTED delete_trigger ")
        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug(f"Connected to SQLite [{self.database}]")

                sqlite_delete_query = 'DELETE FROM agile_triggers WHERE trigger_name=?'

                if self.dbobject.db_query(sqlite_delete_query,(trigger_name,)) == True:
                    result = True
                    self.log.debug(f"trigger [{trigger_name}] deleted")
                else:
                    self.log.error(f"Failed to delete Trigger [{trigger_name}] ")

                self.dbobject.db_disconnect()
            else:
                self.log.error(f"Failed to connect to  agile_triggers ")

        self.log.debug("FINISHED delete_trigger ")

        return result

##############################################################################



