########################################################################
# agileDB.py - Core librry file for the database support for Octopus
# energy API data read from the API for both usage and  prices for
# a smart meter running on the Octopus Agile Tarriff. 
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

from datetime import datetime, timedelta, date
from mylogger import mylogger,nulLogger
from agileTools import gen_periodno, gen_periodno_date,yroffset
from sqliteDB import sqliteDB
import sys
import calendar
import os

empty_rate=-999.99


class OctopusAgileDB:
#filepaths
    database    = None
#sqlite database object
    dbobject    = None
# logging
    log         = None
#chargebands
    chargebands = { 
        "default" : {
            "rate"  : empty_rate
        },
        "good" :  {
            "rate"  : 0.00
        },
        "average" :  {
            "rate"  : 12.0
        },
        "high" :  {
            "rate"  : 18.0
        },
        "extreme" :  {
            "rate"  : 25.0
        }
    }

 

#############################################################################
#  __init__ initialise an agile DB object
##############################################################################
    def __init__(self, theConfig, theLogger=None,):
        # initialise the logfile   
        if theLogger == None:
            theLogger = nulLogger()

        self.log = theLogger
        
        self.log.debug("STARTED OctopusAgileDB __init__")

        self.log.debug("STARTED process_config_file: filepaths")

        # Get the database we are using from the configuration file
        self.database   = theConfig.read_value('filepaths','database_file')

        if self.database == None :
            self.log.error("no database file path registered")
        else:
            self.dbobject = sqliteDB(self.database, theLogger)
        
        self.log.debug("STARTED process_config_file: chargebands")
        
        # Look at extreme - if not present use defaults
        rate = theConfig.read_value('chargebands','extreme_rate')
        if rate != None: self.chargebands["extreme"]["rate"] = rate
        
        # Look at high - if not present use defaults
        rate = theConfig.read_value('chargebands','high_rate')
        if rate != None: self.chargebands["high"]["rate"] = rate
    
        # Look at average - if not present use defaults
        rate = theConfig.read_value('chargebands','average_rate')
        if rate != None: self.chargebands["average"]["rate"] = rate
              
        # Look at good - if not present use defaults
        rate = theConfig.read_value('chargebands','good_rate')
        if rate != None: self.chargebands["good"]["rate"] = rate

        self.log.debug("FINISHED OctopusAgileDB __init__")

#############################################################################
#  initialise_agile_db - create a new database  run this once
##############################################################################
    def initialise_agile_db(self):

        self.log.debug("STARTED initialise_agile_db ")
        result = False
        data = False
        month_rollup = False
        day_rollup = False

        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                # create the agile_data table containing forward costs and back usage
                self.log.debug("creating agile_data table")
                sqlite_query = 'CREATE TABLE agile_data (periodno INTEGER PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER, hour INTEGER, minute INTEGER, cost REAL, usage REAL, CHECK (year >= 2020 AND month <= 12 AND day <= 31 AND hour < 24 AND minute < 60))'
                if self.dbobject.db_query(sqlite_query) == True:
                    data = True
                    self.log.debug("Created agile_data table")

                # create a rollup table with the results by day averaged
                self.log.debug("creating day_rollup table")
                sqlite_query = 'CREATE TABLE agile_rollup_day (dayno INTEGER PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER, cost REAL, usage REAL, unit REAL, CHECK (year >= 2020 AND month <= 12 AND day <= 31))'
                if self.dbobject.db_query(sqlite_query) == True:
                    rollup = True
                    self.log.debug("Created day_rollup table")
                
                # create a rollup table with the results by month averaged
                self.log.debug("creating month rollup table")
                sqlite_query = 'CREATE TABLE agile_rollup_month (monthno INTEGER PRIMARY KEY, year INTEGER, month INTEGER,  cost REAL, usage REAL, unit REAL, CHECK (year >= 2020 AND month <= 12 ))'
                if self.dbobject.db_query(sqlite_query) == True:
                    rollup = True
                    self.log.debug("Created day_rollup table")
                
                if data and day_rollup and month_rollup:
                    result = True
            
                self.dbobject.db_disconnect()
        self.log.debug("FINISHED initialise_agile_db ")
        return result

##############################################################################
#  connect to the database
###############################################################################
    def connect_agile_db(self):
        self.log.debug("STARTED connect_agile_db ")
        result = self.dbobject.db_connect()
        self.log.debug("FINISHED connect_agile_db  ")
        return result

##############################################################################
#  disconnect from the database
###############################################################################
    def disconnect_agile_db(self):
        self.log.debug("STARTED disconnect_agile_db ")
        result = self.dbobject.db_disconnect()
        self.log.debug("FINISHED disconnect_agile_db  ")
        return result

##############################################################################
#  get_db_first_missing_usage - find the first period missing usage data
###############################################################################
    def get_db_first_missing_usage(self):
        result = None
        periodno = -1
        self.log.debug("STARTED get_db_first_missing_usage ")

        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:
                # Query the database for the lowest periodno where usgae value is empty_rate
                sqlite_select_query = f"SELECT periodno FROM agile_data WHERE usage = {empty_rate} ORDER BY periodno LIMIT 1"
                if self.dbobject.db_query(sqlite_select_query) == True:

                    # There can be only 1 row - we have a LIMIT1 on the result of the query
                    got_row = False
                    for row in self.dbobject.db_queryresults():
                         got_row = True
                         periodno = row[0]

                    if got_row != True:
                        self.log.debug(f"Database usage data missing from {periodno}")
                    else:
                        self.log.debug("Database usage_data is up to date.")

                self.dbobject.db_disconnect()
            else:
                self.log.error(f"Failed to query agile_data ")

        if periodno != -1:
            result = periodno        

        self.log.debug("FINISHED get_db_first_missing_usage ")
        return result

##############################################################################
#   get_db_first_missing_period - find the first period missing 
##############################################################################
    def get_db_first_missing_period(self):
        self.log.debug("STARTED get_db_first_missing_period")
        result = None
        periodno = -1
        if self.dbobject.db_ready() == True:

            if self.dbobject.db_connect() == True:
                
                sqlite_select_query = f"SELECT MAX(periodno) FROM agile_data"
                if self.dbobject.db_query(sqlite_select_query) == True:
                
                    # There can be only 1 row - the query is returning the max value
                    got_row = False
                    for row in self.dbobject.db_queryresults():
                        got_row = True
                        periodno = row[0]
            
                else:
                    self.log.error("Failed to update data in sqlite table")
            
            
                self.dbobject.db_disconnect()
                self.log.debug("The SQLite connection is closed")
        if periodno != -1:
            result = periodno
        self.log.debug("FINISHED get_db_first_missing_period ")
        return periodno

##############################################################################
#  get_db_period_cost - get the cost for the requsted period
##############################################################################
    def get_db_period_cost(self,dateobj):
        self.log.debug("STARTED get_db_period_cost ")
        result = None
        cost = empty_rate
        if self.dbobject.db_ready() == True:
            periodno = gen_periodno_date(dateobj)
            if self.dbobject.db_connect() == True:


                sqlite_select_query = f"""SELECT cost from agile_data WHERE periodno = {periodno} """
                if self.dbobject.db_query(sqlite_select_query) == True:

                    # There can be only 1 row - we are searching on the primary key
                    for row in self.dbobject.db_queryresults():
                        cost = row[0]
            
                    self.log.debug(f"cost for periodno {periodno} is {cost} pence")

                else:                 
                    self.log.error(f"Failed to retrieve database data from table:")

            
                self.dbobject.db_disconnect()
                self.log.debug("The SQLite connection is closed")
        if cost != empty_rate:
            result = cost
        self.log.debug("FINISHED get_db_period_cost ")
        return result

##############################################################################
#  create_db_period_cost - create a database entry with cost for this period 
##############################################################################
    def create_db_period_cost(self,year,month,day,hour,minute,cost,inlist=False):
        self.log.debug("STARTED create_period_cost ")
        result=False
        connected = True

        if self.dbobject.db_ready() == True:

            if inlist == False: connected = self.dbobject.db_connect()
            if connected == True:
                # index is based on half hour periods (per day,month and year)
                periodno = gen_periodno(year,month,day,hour,minute)

                sqlite_insert_query = """INSERT INTO agile_data
                     ('periodno','year','month','day','hour','minute','cost','usage') 
                        VALUES (?,?,?,?,?,?,?,?); """
                data_tuple = (periodno,year,month,day,hour,minute,cost,empty_rate)

                if self.dbobject.db_query(sqlite_insert_query,data_tuple) == True:      
                    result = True
                    self.log.debug(f"SQLQuery {year:4d}/{month:02d}/{day:02d}/{hour:02d}:{minute:02d} completed ")
                else:
                    self.log.error(f"Failed to insert data into sqlite table:")
                    result = False

            if inlist == False: self.dbobject.db_disconnect()

        self.log.debug("FINISHED create_period_cost ")

        return result

##############################################################################
#  get_db_period_data - call Octopus to get usage/cost for a timestamp (day,month,year)  
##############################################################################
    def get_db_period_data(self,year=0,month=0,day=0,inlist=False):
        self.log.debug("STARTED get_db_period_data ")
        result = None
        connected = True
        if self.dbobject.db_ready()== True:
            yearstring=""
            monthstring=""
            daystring=""
            result=[]
    
            if year != 0:
                yearstring =f" WHERE YEAR='{year}'"
                if month != 0:
                    monthstring =f" and MONTH='{month}'"
                    if day != 0:
                        daystring =f" and DAY='{day}'"
    
            sqlite_select_query=" SELECT * from agile_data " + yearstring + monthstring + daystring + ";"

            if inlist == False: connected = self.dbobject.db_connect()

            if connected == True:
                if self.dbobject.db_query(sqlite_select_query) == True:
                    for row in self.dbobject.db_queryresults():
                        # row0 = periodno, row1=year, row2=month, row3=day, row4=hour,row5=minute, row6=cost, row7 = usage
                        target_band="default"
                        for band in self.chargebands:
                            if  row[6] > float(self.chargebands[band]["rate"]):
                                target_band = band
                        if row[7] != empty_rate:
                            cost = row[6]*row[7]
                        else:
                            cost = 0
                        output = (f"{row[3]:02d}/{row[2]:02d}/{row[1]:04d} {row[4]:02d}:{row[5]:02d}", row[6], row[7], f"{cost:5.3f}" ,target_band)
                        self.log.debug(output)
                        result+= [output]

                else:
                    self.log.error(f"Failed to retrieve database data from table: ")
                    result = None

                if inlist == False: 
                    self.dbobject.db_disconnect()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_period_data ")
        return result

##############################################################################
#   update_db_period_usage - update the database cost table with usage info
##############################################################################
    def update_db_period_usage(self,year,month,day,hour,minute,usage,inlist):
        result = False
        connected = True
        periodno = 0
        self.log.debug("STARTED save_period_usage ")

        if self.dbobject.db_ready() == True:

            if inlist == False: 
                connected = self.dbobject.db_connect()
            
            if connected == True:
                # index is based on half hour slots (per day,month and year)
                periodno = gen_periodno(year,month,day,hour,minute)

                sqlite_update_query = """UPDATE agile_data SET usage = ? WHERE periodno = ? """
                data_tuple = (usage,periodno)

                if self.dbobject.db_query(sqlite_update_query,data_tuple) == True:
                    result = True
                    self.log.debug(f"Record {year}/{month}/{day}/{hour}:{minute} updated with usage {usage} in database")

                else:
                    self.log.error("Failed to update data in sqlite table")
                    result = False

            if inlist == False: self.dbobject.db_disconnect()
                
        self.log.debug("FINISHED save_period_usage ")
        return result

##############################################################################
#  get_db_data_years - get the years we have data for
##############################################################################
    def get_db_data_years(self):
        year_list=[]
        result = None
        self.log.debug("STARTED get_db_data_years ")
 
        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug("querying agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query="SELECT year FROM agile_data GROUP BY year"
                if self.dbobject.db_query(sql_select_query) == True:
        
                    for row in  self.dbobject.db_queryresults():
                        self.log.debug(f"row={row}")
                        year_list += row

                else:
                    self.log.error(f"Failed SQL data call in get_data_years ")

                self.dbobject.db_disconnect()
                self.log.debug("The SQLite connection is closed")
                result = year_list
        self.log.debug("FINISHED get_db_data_years ")

        return result

##############################################################################
#  get_db_data_months- get the months we have data for
##############################################################################
    def get_db_data_months(self,year):
        month_list=[]
        result = None
        self.log.debug("STARTED get_db_data_months ")
        if self.dbobject.db_ready() == True:
            if self.dbobject.db_connect() == True:

                self.log.debug("creating agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query=f"SELECT year FROM agile_data WHERE year = {year} GROUP BY month"
                if self.dbobject.db_query(sql_select_query) == True:
        
                    for row in  self.dbobject.db_queryresults():
                        self.log.debug(f"row={row}")
                        month_list += row

                else:
                    self.log.error("Failed SQL data call in get_data_months")

                self.dbobject.db_disconnect()
                self.log.debug("The SQLite connection is closed")
                result = month_list

        self.log.debug("FINISHED get_db_data_months ")
        return result
        
##############################################################################
#  get_db_data_days - get the years we have data for
##############################################################################
    def get_db_data_days(self,year,month):
        day_list=[]
        result = None
        self.log.debug("STARTED get_db_data_days ")
        if self.dbobject.db_ready() == True:   
            if self.dbobject.db_connect() == True:

                self.log.debug("creating agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query=f"SELECT day  FROM agile_data WHERE year = {year} AND month = {month} GROUP BY day"
                if self.dbobject.db_query(sql_select_query) == True:
        
                    for row in  self.dbobject.db_queryresults():
                        self.log.debug(f"row={row}")
                        day_list += row
                else:
                    self.log.error("Failed SQL data call in get_data_days")

                self.dbobject.db_disconnect()
                self.log.debug("The SQLite connection is closed")
                result = day_list

        self.log.debug("FINISHED get_db_data_days ")
        return result


##############################################################################
#  create_db_rollup_period - create a rollup for a period
##############################################################################
    def create_db_rollup_month(self,year,month):
        period_data=[]
        month_use = 0
        month_cost = 0
        month_unit = 0
        result = None
        self.log.debug("STARTED create_db_rollup_month ")
        daysinmonth = calendar.monthrange(year,month)[1]
        cost= [] * daysinmonth
        use= [] * daysinmonth
        unit= [] * daysinmonth
        if self.db_ready() == True:   
            if self.dbobject.db_connect() == True:
                # we'vew got more database work to do - set inlist to true to keep connection open
                period_data = self.get_db_period_data(year,month,0,True)

                if period_data != None:
                    for entry in period_data:
                        # got a months worth of entries total up the days
                        day = int(entry[0].split('/')[0])
                        self.log.debug(f"entry data = [{entry}] day=[{day}]")
                        if float(entry[2]) != -999.99:
                            use[day]  += float(entry[2])
                            cost[day] += float(entry[3])
                            unit [day] = cost[day]/use[day]
                            # average out the result for the current month
                            month_use  += float(entry[2])
                            month_cost += float(entry[3])
                            month_unit  = month_cost/ month_use
                    
                    # we have a per day total and a per month total (running in the case the periods are not complete)
                    # put those values into the database 

                    #first off insert the month into the month table
                    monthno = 12 * (year - yroffset) + month
                    sql_month_insert_query = "INSERT INTO agile_rollup_month (monthno, year, month, cost , usage , unit) VALUES = (?,?,?,?,?,?)"
                    month_tuple=(monthno, year, month, month_cost , month_use , month_unit)

                    for day in 1..daysinmonth:
                        dayno = day + (month * 31) + ((year - yroffset ) * 366)
                        day_tuple=(dayno, year, month, day, cost[day], use[day], unit[day])
                        sql_day_insert_query = "INSERT INTO agile_rollup_day (dayno, year, month, day, cost, usage, unit) VALUES = (?,?,?,?,?,?.?)"



            # Finished disconnect from the database
            self.dbobject.db_disconnect()
        self.log.debug("FINISHED create_db_rollup_month ")
        return result