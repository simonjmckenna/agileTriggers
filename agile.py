########################################################################
# agile.py - Core librry file for the database and API calls to Ocotpus
# energy API to get both historic usage and forward looking prices for
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
from urllib.request import Request, build_opener
from mylogger import mylogger,nulLogger
import requests
import sqlite3
import dateutil.parser
import json
import sys
import logging
import os
import configparser

yroffset=2020
empty_rate=-999.99

class OctopusAgile:
    # Octopus account data
    elecMPAN = None
    elecSERIAL = None
    apiKey = None
    productCode = "AGILE-18-02-21"
    octopusUrl  = None
#filepaths
    database      = None
    binFolder     = None
# settings
    new_rate_hour = 16
    new_rate_mins = 10
    app_site_name = None
    agile_debug   = False
    
# other data
    region = None
    meterPointUrl    = None
    consumptionUrl    = None
    costUrl     = None
    tarrifCode  = None
    valid = 0 
# logging
    log=None
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
    
##############################################################################
#  __init__ class init for agile class 
##############################################################################
    def __init__ (self, theConfig, theLogger=None,dbOnly = False):
        # initialise the logfile
        
        if theLogger == None:
            theLogger = nulLogger()

        self.log = theLogger
        
        self.log.debug("STARTED __init__")

        self.__set_config(theConfig,dbOnly)

        if self.api_ready():
            self.log.debug("__init__ - set_api_ready - building urls")
            self.build_api_url()

        self.log.debug("FINISHED __init__ ")

        return

##############################################################################
#  __set_config  process the config file for data
##############################################################################
    def __set_config(self,theConfig,dbOnly):
        self.log.debug("STARTED __set_config")

        self.log.debug("STARTED process_config_file: octopus_account")
        self.elecMPAN   = theConfig.read_value('octopus_account','meterMPAN')
        self.elecSERIAL = theConfig.read_value('octopus_account','meterSERIAL')
        self.apiKey     = theConfig.read_value('octopus_account','OctopusAPIKey')
        self.octopusUrl = theConfig.read_value('octopus_account','OctopusUrl')

        self.log.debug("STARTED process_config_file: filepaths")
        self.database   = theConfig.read_value('filepaths','database_file')
        self.binFolder  = theConfig.read_value('filepaths','bin_folder')

        self.log.debug("STARTED process_config_file: chargebands")
        
        # Look at extreme - if not present use defaults
        rate = theConfig.read_value('chargebands','extreme_rate')
        if rate != None:
            self.chargebands["extreme"]["rate"] = rate
        
        # Look at high - if not present use defaults
        rate = theConfig.read_value('chargebands','high_rate')
        if rate != None:
            self.chargebands["high"]["rate"] = rate
    
        # Look at average - if not present use defaults
        rate = theConfig.read_value('chargebands','average_rate')
        if rate != None:
            self.chargebands["average"]["rate"] = rate
              
        # Look at good - if not present use defaults
        rate = theConfig.read_value('chargebands','good_rate')
        if rate != None:
            self.chargebands["good"]["rate"] = rate
    
        # Look at default - if not present use defaults
        # Nothing can be set for defaults as yet
        
        rate_time=[]
        self.log.debug("STARTED process_config_file: settings")
        rate_time   = theConfig.read_value('settings', 'new_rate_time')
        rate_time   = rate_time.split(':')
        
        self.new_rate_hour = int(rate_time[0])
        self.new_rate_mins = int(rate_time[1])
        
        self.log.debug (f" time = {self.new_rate_hour:02d}:{self.new_rate_mins:02d}")
        
        self.app_site_name  = theConfig.read_value('settings','app_site_name')
        
         # do we need the network or is this just the database
        if dbOnly == False:
            # Check to see if key values needed for API calls are set (MPAN)
            if self.elecMPAN  != None:
                self.valid += 1
                self.log.debug(f"__init__ - mpan    [{self.elecMPAN}].")
            
            # Check to see if key values needed for API calls are set (SERIAL)
            if self.elecSERIAL != None:
                self.log.debug(f"__init__ - serial  [{self.elecSERIAL}].")
                self.valid += 2
            
            # Check to see if key values needed for API calls are set (APIKEY)
            if self.apiKey != None:
                self.log.debug(f"__init__ apiKey  [{self.apiKey}].")
                self.valid += 4
            
            # Check to see if values needed for API calls are set (OCTOPUSURL)
            if self.octopusUrl != None:
                self.log.debug(f"__init__ octopusUrl [{self.octopusUrl}].")
                self.valid += 8
        
        self.log.debug("FINISHED process_config_file")

##############################################################################
#  build_api_url -  build the api urls we use
# ##############################################################################
    def build_api_url(self):
        self.log.debug("STARTED build_api_url")
        self.meterPointUrl = self.octopusUrl + "electricity-meter-points/" + self.elecMPAN
        self.consumptionUrl = self.octopusUrl + "electricity-meter-points/" + self.elecMPAN + "/meters/" + self.elecSERIAL + "/consumption"
        
        # Get the region 
        self.region = self.set_region()
        
        # set the tarriff code
        self.tarrifCode = "E-1R-" + self.productCode + "-" + self.region
        self.log.debug("TarrifCode is [" + self.tarrifCode + "].")
        # URL to query charges 
        self.costUrl =  self.octopusUrl + "products/" + self.productCode + "/electricity-tariffs/" + self.tarrifCode + "/standard-unit-rates/"
        self.log.debug("FINISHED build_api_url")

##############################################################################
#   db_ready - do we have the database config set up
##############################################################################
    def db_ready(self):
        result = self.database != None
        self.log.debug("db_ready: database [{self.database}] result =["+str(result)+"].")
        return result

############################################################################### 
#  api_ready - do we have the necessary data to call out to octopus
###############################################################################
    def api_ready(self):
        result= self.valid == 15
        self.log.debug("api_ready: result =["+str(result)+"].")
        return result

##############################################################################
# #  set_region - given an MPAN set the agile tarrif to use.
# ##############################################################################
    def set_region(self):
        self.log.debug("STARTED set_region")
        result = None
        if self.api_ready() == True:
            headers = {'content-type': 'application/json'}
            meter_details = requests.get(self.meterPointUrl, headers=headers, auth=(self.apiKey,''))
            self.log.debug("meter_details=["+meter_details.text+"]")
            
            json_meter_details = json.loads(meter_details.text)
            result = str(json_meter_details['gsp'][-1]).upper()
            
        self.log.debug("FINISHED set_region - region is ["+ result + "].")
        return result
        
##############################################################################
#  gen_periodno_date - work out the period number from the start of yroffset 
###############################################################################
    def gen_periodno_date(self,dateobj):
        self.log.debug("STARTED gen_periodno_date ")
        result = self.gen_periodno(dateobj.year,dateobj.month,dateobj.day,dateobj.hour,dateobj.minute)
        self.log.debug("FINISHED gen_periodno_date ")
        return result

##############################################################################
#  gen_periodno - work out the period number from the start of yroffset 
##############################################################################
    def gen_periodno(self,year,month,day,hour,minute):
        self.log.debug("STARTED gen_periodno ")
        period = 0
        
        if minute >= 30:
            period = 1
        # generate a periodno from the time components based on half hour
        # # periods - there are:
        # # 2 in an hour
        # # 48 in a day
        # # 1488 in a 31 day month (theer will be gaps for 28/29/30 day months) 
        # # each year has 17856 periods - start with yroffset being year 0 
        periodno = period + (hour*2) + (day*48) + (month*1488) + ((year-yroffset)*17856)
        
        self.log.debug("FINISHED gen_periodno - is ["+ str(periodno) + "].")
        return periodno

#############################################################################
# #  initialise_agile_db - create a new database  run this once
# #############################################################################
    def initialise_agile_db(self):
        sqliteConnection = None
        self.log.debug("STARTED initialise_agile_db ")
        result = None
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                
                self.log.debug("creating agile_data table")
                # create the agile_data table containing forward costs and back usage
                cursor.execute('CREATE TABLE agile_data (periodno INTEGER PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER, hour INTEGER, minute INTEGER, cost REAL, usage REAL, CHECK (year >= 2020 AND month <= 13 AND day <= 31 AND hour < 24 AND minute < 60))')
                
            except sqlite3.Error as error:
                self.log.error("Failed to create agile_data table", error)
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")
        
        self.log.debug("FINISHED initialise_agile_db ")

##############################################################################
#  create_period_cost - create a database entry with cost for this period 
##############################################################################
    def create_period_cost(self,year,month,day,hour,minute,cost):
        self.log.debug("STARTED create_period_cost ")
        sqliteConnection = None
        result=False

        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")

                # index is based on half hour periods (per day,month and year)
                periodno = self.gen_periodno(year,month,day,hour,minute)

                sqlite_insert_query = """INSERT INTO agile_data
                    ('periodno','year','month','day','hour','minute','cost','usage') 
                    VALUES (?,?,?,?,?,?,?,?); """
                data_tuple = (periodno,year,month,day,hour,minute,cost,empty_rate)

                cursor.execute(sqlite_insert_query,data_tuple)
                sqliteConnection.commit()
                result = True
                self.log.debug(f"Record {year:4d}/{month:02d}/{day:02d}/{hour:02d}/{minute:02d} inserted successfully ")
                cursor.close()

            except sqlite3.Error as error:
                self.log.error(f"Failed to insert data into sqlite table:{error}")
                result = False
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED create_period_cost ")

        return result

##############################################################################
# #   find_first_period_usage - find the first period missing usage data
# ##############################################################################
    def find_first_period_usage(self):
        self.log.debug("STARTED find_first_period_usage ")
        sqliteConnection = None
        periodno = -1
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")

                sqlite_select_query = f"SELECT periodno FROM agile_data WHERE usage = {empty_rate} ORDER BY periodno LIMIT 1"

                cursor.execute(sqlite_select_query)

                # There can be only 1 row - we search on the primary key
                got_row = False
                for row in cursor.fetchall():
                     got_row = True
                     periodno = row[0]

                if got_row == True:
                    self.log.debug(f"Database usage data missing from {periodno}")
                else:
                    self.log.debug("Database usage_data is up to date.")
                    periodno = 0
                cursor.close()

            except sqlite3.Error as error:
                self.log.error("Failed to update data in sqlite table", error)
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED find_first_period_usage ")
        return periodno

##############################################################################
#   find_last_period - find the first period missing 
##############################################################################
    def find_last_period(self):
        self.log.debug("STARTED find_last_period")
        sqliteConnection = None
        periodno =-1
        if self.db_ready() == True:
            try:
                periodno = -1
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")
                
                sqlite_select_query = f"SELECT MAX(periodno) FROM agile_data"
                cursor.execute(sqlite_select_query)
                
                # There can be only 1 row - the query is returning the max value
                got_row = False
                for row in cursor.fetchall():
                    got_row = True
                    periodno = row[0]
                    
                if got_row == True:
                    self.log.debug(f"database did not return a valid period")
                    cursor.close()
            
            except sqlite3.Error as error:
                self.log.error("Failed to update data in sqlite table", error)
            
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")
        
        self.log.debug("FINISHED find_last_period ")
        return periodno

##############################################################################
#   save_period_usage - update the database cost table with usage info
##############################################################################
    def save_period_usage(self,year,month,day,hour,minute,usage):
        self.log.debug("STARTED save_period_usage ")
        sqliteConnection = None
        result = False
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")

                # index is based on half hour slots (per day,month and year)
                periodno = self.gen_periodno(year,month,day,hour,minute)

                sqlite_update_query = """UPDATE agile_data SET usage = ? WHERE periodno = ? """
                data_tuple = (usage,periodno)

                count = cursor.execute(sqlite_update_query,data_tuple)
                sqliteConnection.commit()
                result = True

                self.log.debug(f"Record {year}/{month}/{day}/{hour}/{minute} updated with usage {usage} in database")
                cursor.close()

            except sqlite3.Error as error:
                self.log.error("Failed to update data in sqlite table", error)
                result = False
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED save_period_usage ")
        return result

##############################################################################
#  get_period_cost - get the cost for the requsted period
##############################################################################
    def get_period_cost(self,dateobj):
        self.log.debug("STARTED get_period_cost ")
        sqliteConnection = None
        cost = empty_rate
        if self.db_ready() == True:
            periodno = self.gen_periodno_date(dateobj)
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")

                sqlite_select_query = f"""SELECT cost from agile_data WHERE periodno = {periodno} """
                count = cursor.execute(sqlite_select_query)
                # initialise incase no return from query
                cost = empty_rate
                # There can be only 1 row - we are searching on the primary key
                for row in cursor.fetchall():
                    cost = row[0]
            
                self.log.debug(f"cost for periodno {periodno} is {cost} pence")
                cursor.close()

            except sqlite3.Error as error:
                
                self.log.error(f"Failed to retrieve database data from table: {error}")
                cost = empty_rate
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_period_cost ")
        return cost

##############################################################################
#   get_current_rates - call get_rates with current time 
##############################################################################
    def get_current_rates(self):
        self.log.debug("STARTED get_current_rates ")

        date_from =  self.time_now()
        result=self.get_rates(date_from)

        self.log.debug("FINISHED get_current_rates ")
        return result

##############################################################################
#   get_latest_rates - call get_rates with first missing rate time 
##############################################################################
    def get_latest_rates(self):
        self.log.debug("STARTED get_latest_rates ")

        periodno = self.find_last_period()
        self.log.debug(f"lastest periodno is {periodno} ")
        date_from =  self.date_from_periodno(periodno)
        self.log.debug(f"lastest date is {date_from} ")
        result=self.get_rates(date_from)

        self.log.debug("FINISHED get_latest_rates ")
        return result

##############################################################################
#  get_rates - call Octopus to get rates for period_from to period_to  
##############################################################################
    def get_rates(self, dateobj_from, dateobj_to=None):
        self.log.debug("STARTED get_rates ")
        result = None
        if self.api_ready() == True:
            period_from = self.timestring_from_date(dateobj_from)

            if dateobj_to is not None:
                period_to = self.timestring_from_date(dateobj_to)
                payload = { 'period_from' : period_from, 'period_to' : period_to }
            else:
                payload = { 'period_from' : period_from }
 
            headers = {'content-type': 'application/json'}
            response = requests.get(self.costUrl,headers=headers,auth=(self.apiKey,''),params=payload)
            self.log.debug("result of call = ["+str(response)+"].")
            result = response.json()
            self.log.debug("json data in response = ["+str(result)+"].")

        self.log.debug("FINISHED get_rates ")
        return result

##############################################################################
#  load_rate_data - load the rate data into the database
##############################################################################
    def load_rate_data(self,rate_data):
        self.log.debug("STARTED load_rate_data ")

        for result in rate_data['results']:
            cost = result['value_inc_vat']
            raw_from = result['valid_from']
            # We need to reformat the date to a python date from a json date
            date = datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ")
            self.log.debug( f" YY:{date.year:4d} MM:{date.month:02d} DD:{date.day:02d} hh:{date.hour:02d} mm:{date.minute:02d} COST:"+str(cost))
            self.create_period_cost(date.year, date.month, date.day, date.hour, date.minute, cost)

        result =  1
        self.log.debug("FINISHED load_rate_data ")
        return result

##############################################################################
#  load_usage_data - load the usage data into the database
##############################################################################
    def load_usage_data(self,usage_data):
        self.log.debug("STARTED load_usage_data ")
        
        for result in usage_data['results']:
            usage = result['consumption']
            raw_from = result['interval_start']
            # We need to reformat the date to a python date from a json date
            date = datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ")
            self.log.debug( f" YY:{date.year:4d} MM:{date.month:02d} DD:{date.day:02d} hh:{date.hour:02d} mm:{date.minute:02d} USAGE:{usage}")
            self.save_period_usage(date.year, date.month, date.day, date.hour, date.minute, usage)

        result =  1
        self.log.debug("FINISHED load_usage_data ")
        return result

##############################################################################
#   get_current_rates - call get_rates with current time 
##############################################################################
    def get_current_rates(self):
        self.log.debug("STARTED get_current_rates ")

        date_from =  self.time_now()
        result=self.get_rates(date_from)

        self.log.debug("FINISHED get_current_rates ")
        return result


##############################################################################
#  date_from_periodno - get a dateobj from a periodno
##############################################################################
    def date_from_periodno(self,periodno):
        self.log.debug("STARTED date_from_periodno ")
        year  = int(periodno / 17856) + yroffset 
        month = int((periodno % 17856) / 1488)
        day   = int((periodno % 1488) / 48)
        hour  = int((periodno % 48) / 2)
        minute= int((periodno % 2))
        theDate = datetime(year,month,day,hour,minute)
        self.log.debug(f"periodno [{periodno}] gives datetime {year}/{month}/{day}/{hour}/{minute} ")

        self.log.debug("FINISHED date_from_periodno ")
        return theDate
              
##############################################################################
#  timestring_from_date - get a timestring from a date object
##############################################################################
    def timestring_from_date(self,dateobject):
        self.log.debug("STARTED timestring_from_date ")
        result =  datetime.strftime(dateobject, '%Y-%m-%dT%H:%M:%SZ')
        self.log.debug("FINISHED timestring_from_date ")
        return result

##############################################################################
#  gen_timestring - generate the date/time in necesary format  from raw numbers
##############################################################################
    def gen_timestring(year,month,day,hour,minute,second):
        self.log.debug("STARTED gen_time ")
        # format is '%Y-%m-%dT%H:%M:%SZ' 
        result= f"{year:4d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
        self.log.debug("FINISHED gen_time ")
        return result

##############################################################################
#  time_now - get the date/time now and return it in necesary format 
##############################################################################
    def time_now(self):
        self.log.debug("STARTED time_now ")
        result =  datetime.utcnow()
        self.log.debug("FINISHED time_now ")
        return result
        
##############################################################################
#  get_usage - call Octopus to get usage for dateobj_from to dateobj_to  
##############################################################################
    def get_usage(self, dateobj_from, dateobj_to=None):
        self.log.debug("STARTED get_usage ")
        result = None
        if self.api_ready() == True:

            period_from = self.timestring_from_date(dateobj_from)
 
            if dateobj_to is not None:
                period_to = self.timestring_from_date(dateobj_to)
                payload = { 'period_from' : period_from, 'period_to' : period_to, 'page_size' : 25000 }
            else:
                payload = { 'period_from' : period_from, 'page_size' : 25000 }
 
 
            headers = {'content-type': 'application/json'}
            response = requests.get(self.consumptionUrl,headers=headers,auth=(self.apiKey,''),params=payload)
            self.log.debug("result of call = ["+str(response)+"].")
            result = response.json()
            self.log.debug("json data in response = ["+str(result)+"].")

        self.log.debug("FINISHED get_usage ")
        return result

##############################################################################
#  get_period_data - call Octopus to get usage/cost for a timestamp (day,month,year)  
##############################################################################
    def get_period_data(self,year=0,month=0,day=0):
        self.log.debug("STARTED get_period_data ")
        result = None
        if self.db_ready() == True:
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
            sqliteConnection = None
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()
                self.log.debug("Connected to SQLite [" + self.database + "].")

                count = cursor.execute(sqlite_select_query)
                for row in cursor.fetchall():
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
                cursor.close()

            except sqlite3.Error as error:
                self.log.error(f"Failed to retrieve database data from table: {error}")
                result = None
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_period_data ")
        return result




##############################################################################
#  get_data_years - get the years we have data for
##############################################################################
    def get_data_years(self):
        year_list=[]
        sqliteConnection = None
        result = None
        self.log.debug("STARTED get_data_years ")
 
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()

                self.log.debug("querying agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query="SELECT year FROM agile_data GROUP BY year"
                cursor.execute(sql_select_query)
        
                for row in  cursor.fetchall():
                    self.log.debug(f"row={row}")
                    year_list += row

                cursor.close()
            except sqlite3.Error as error:
                self.log.error(f"Failed SQL data call in get_data_years {error}")
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_data_years ")

        return year_list

##############################################################################
#  get_data_months- get the years we have data for
##############################################################################
    def get_data_months(self,year):
        sqliteConnection = None
        result = None
        self.log.debug("STARTED get_data_months ")
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()

                self.log.debug("creating agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query=f"SELECT year FROM agile_data WHERE year = {year} GROUP BY month"
                cursor.execute(sql_select_query)
        
                result = cursor.fetchall()

                cursor.close()
            except sqlite3.Error as error:
                self.log.error(f"Failed SQL data call in get_data_months {error}")
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_data_months ")
        return result
##############################################################################
#  get_data_days - get the years we have data for
##############################################################################
    def get_data_days(self,year,month):
        sqliteConnection = None
        result = None
        self.log.debug("STARTED get_data_days ")
        if self.db_ready() == True:
            try:
                sqliteConnection = sqlite3.connect(self.database)
                sqliteConnection.row_factory = sqlite3.Row
                cursor = sqliteConnection.cursor()

                self.log.debug("creating agile_data table")
                # create the agile_data table containing forward costs and back usage
                sql_select_query=f"SELECT day  FROM agile_data WHERE year = {year} AND month = {month} GROUP BY day"
                cursor.execute(sql_select_query)
        
                month_list = cursor.fetchall()

                cursor.close()
            except sqlite3.Error as error:
                self.log.error(f"Failed SQL data call in get_data_months {error}")
            finally:
                if (sqliteConnection):
                    sqliteConnection.close()
                    self.log.debug("The SQLite connection is closed")

        self.log.debug("FINISHED get_data_days ")
        return day_list
##############################################################################



