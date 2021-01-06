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
import sqlite3
import sys
import os

class costTriggers:
    triggers = None
    database      = None
    triggerFolder = None

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
        self.log.debug("STARTED initialise_trigger_db ")
        try:
            sqliteConnection = sqlite3.connect(self.database)
            cursor = sqliteConnection.cursor()

            # create the agile_triggers table 
            # containing a trigger_name
            #            a trigger cost, 
            #            a the trigger file
            self.log.debug("creating agile_triggers table")
            cursor.execute('CREATE TABLE agile_triggers (trigger_name TEXT PRIMARY KEY, cost REAL )')

        except sqlite3.Error as error:
            print("Failed to create agile_triggers table", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED initialise_trigger_db ")

##############################################################################
#   __start_trigger -  function to trigger a start
##############################################################################
    def __start_trigger(self,trigger_name):
        self.log.debug("STARTED  start_trigger ")
        self.log.debug("FINISHED start_trigger ")
##############################################################################
#   __stop_trigger -  function to trigger a stop
##############################################################################
    def __stop_trigger(self,trigger_name):
        self.log.debug("STARTED  stop_trigger ")
        self.log.debug("FINISHED stop_trigger ")

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
        self.log.debug("STARTED get_all_triggers ")
        try:
            sqliteConnection = sqlite3.connect(self.database)
            cursor = sqliteConnection.cursor()
            self.log.debug("Connected to SQLite [" + self.database + "].")

            sqlite_select_query = """SELECT trigger_name,cost FROM agile_triggers """

            count = cursor.execute(sqlite_select_query)
            triggers=cursor.fetchall()
            self.log.debug(f"get_all_triggers returned {count} triggers")
            cursor.close()

        except sqlite3.Error as error:
            self.log.error(f"Failed to query data in agile_triggers table:{error}")
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_all_triggers ")

        return triggers

##############################################################################
#   add_new_trigger - update the triggers with a new trigger
##############################################################################
    def add_new_trigger(self,trigger_name,cost):
        result = False
        self.log.debug("STARTED add_new_trigger ")
        try:
            sqliteConnection = sqlite3.connect(self.database)
            cursor = sqliteConnection.cursor()
            self.log.debug("Connected to SQLite [" + self.database + "].")

            sqlite_insert_query = """INSERT INTO agile_triggers ('trigger_name','cost') VALUES (?,?); """
            data_tuple = (trigger_name,cost)

            cursor.execute(sqlite_insert_query,data_tuple)
            sqliteConnection.commit()
            result = True

            self.log.debug(f"result={result}")
            cursor.close()

        except sqlite3.Error as error:
            self.log.error(f"Failed to insert data in agile_triggers table, {error}")
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED add_new_trigger ")

        return result
          
##############################################################################
#   update_trigger - update the triggers with a new trigger
##############################################################################
    def update_trigger(self,trigger_name,cost):
        result = False
        self.log.debug("STARTED update_trigger ")
        try:
            sqliteConnection = sqlite3.connect(self.database)
            cursor = sqliteConnection.cursor()
            self.log.debug("Connected to SQLite [" + self.database + "].")

            sqlite_update_query = """UPDATE agile_triggers SET cost = ? WHERE trigger_name = ? """
            data_tuple = (cost, trigger_name)

            cursor.execute(sqlite_update_query,data_tuple)
            sqliteConnection.commit()
            result = True

            self.log.debug(f"result={result}")
            cursor.close()

        except sqlite3.Error as error:
            self.log.error(f"Failed to insert data in agile_triggers table, {error}")
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED update_trigger ")
          
        return result

##############################################################################
#   del_trigger - update the triggers table deleting a trigger
##############################################################################
    def del_trigger(self,trigger_name):
        result = False
        self.log.debug("STARTED delete_trigger ")
        try:
            sqliteConnection = sqlite3.connect(self.database)
            cursor = sqliteConnection.cursor()
            self.log.debug("Connected to SQLite [" + self.database + "].")

            sqlite_delete_query = 'DELETE FROM agile_triggers WHERE trigger_name=?'
            cursor.execute(sqlite_delete_query,(trigger_name,))
            sqliteConnection.commit()

            result=True

            cursor.close()

        except sqlite3.Error as error:
            self.log.error(f"Failed to delete data in agile_triggers table, {error}")
            result = False
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED delete_trigger ")

        return result

##############################################################################



