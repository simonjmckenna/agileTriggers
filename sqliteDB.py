########################################################################
# sqliteDB.py - Core library file for using a SQLIte DB
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



from mylogger import mylogger,nulLogger
import agileTools
import sqlite3
import sys
import os


class sqliteDB:
#filepaths
    database      = None
# sql connection
    sqlconnection = None
    sqlcursor     = None
# logging
    log           = None


##############################################################################
#   __init__ initialise class 
##############################################################################
    def __init__ (self, database, theLogger=None):
        # initialise the logfile
        
        if theLogger == None:
            theLogger = nulLogger()

        self.log = theLogger
        
        self.log.debug("STARTED sqliteDB __init__")

        self.log.debug("STARTED process_config_file: filepaths")

        # Get the database we are using from the configuration file
        self.database   = database

        self.log.debug("FINISHED sqlliteDB __init__ ")

        return


##############################################################################
#   db_ready - do we have the database config set up
##############################################################################
    def db_ready(self):
        result = self.database != None
        self.log.debug("db_ready: database [{self.database}] result =["+str(result)+"].")
        return result

##############################################################################
#  db_connect - connect to SQLite database stored in self.database
#  return True if successful
#  return False if not
##############################################################################
    def db_connect(self):
        result = True
        if self.db_ready() == True:
            if self.sqlconnection:
                self.log.debug(f" Reopened sql connection ")   
                result = True
            else:
                try:
                    self.sqlconnection = sqlite3.connect(self.database)
                    self.sqlconnection.row_factory = sqlite3.Row
                    self.sqlcursor = self.sqlconnection.cursor()                
                    self.log.debug(f" Opened sql connection ")   
                except sqlite3.Error as error:
                    self.log.error(f"Failed to connect to Agile Database: {self.database}")
                    result = False
        return result

#############################################################################
#   db_disconnect - disconnect from to SQLite
##############################################################################
    def db_disconnect(self):

        result = True
        
        if self.db_ready() == True:
            if self.sqlconnection:
                try:
                    # Close the curor and then the database
                    self.sqlcursor.close()
                    self.sqlconnection.close() 
                    self.sqlcursor = None 
                    self.sqlconnection = None
                    self.log.debug(f" Closed sql connection ")          
                except sqlite3.Error as error:
                    self.log.error(f"Failed to close sql connection [{error}]")
                    result = False
        return result

#############################################################################
#   query_db - query to SQLite database
#   returns True if Query worked
#   returns False if query didnt  *** TBD handle internal SQL errors ***
##############################################################################
    def db_query(self, query, data_tuple=None):
        result = True
        try:
            if data_tuple == None:
                self.sqlcursor.execute(query)
            else:
                self.sqlcursor.execute(query, data_tuple)
            self.sqlconnection.commit()        
        except sqlite3.Error as error:
            self.log.error(f"Failed to execute query {error}")
            result = False
        return result

#############################################################################
#   db_queryresults - get the results of the query to SQLite
##############################################################################
    def db_queryresults(self):
        result = self.sqlcursor.fetchall()
        return result

