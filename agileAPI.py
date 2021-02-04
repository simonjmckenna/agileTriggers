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

from mylogger import mylogger,nulLogger
from  agileTools import timestring_from_date
import requests
import json
import os
import configparser

empty_rate=-999.99

class OctopusAgileAPI:
    # Octopus account data
    elecMPAN = None
    elecSERIAL = None
    apiKey = None
    productCode = "AGILE-18-02-21"
    octopusUrl  = None
#filepaths
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


##############################################################################
#  __init__ class init for agile class 
##############################################################################
    def __init__ (self, theConfig, theLogger=None):
        # initialise the logfile
        
        if theLogger == None:
            theLogger = nulLogger()

        self.log = theLogger
        
        self.log.debug("STARTED __init__")

        self.__set_config(theConfig)

        if self.api_ready():
            self.log.debug("__init__ - set_api_ready - building urls")
            self.build_api_url()

        self.log.debug("FINISHED __init__ ")

        return

##############################################################################
#  __set_config  process the config file for data
##############################################################################
    def __set_config(self,theConfig):
        self.log.debug("STARTED __set_config")

        self.log.debug("STARTED process_config_file: octopus_account")
        self.elecMPAN   = theConfig.read_value('octopus_account','meterMPAN')
        self.elecSERIAL = theConfig.read_value('octopus_account','meterSERIAL')
        self.apiKey     = theConfig.read_value('octopus_account','OctopusAPIKey')
        self.octopusUrl = theConfig.read_value('octopus_account','OctopusUrl')

        self.log.debug("STARTED process_config_file: filepaths")
        self.binFolder  = theConfig.read_value('filepaths','bin_folder')

        
    
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
    def get_rates(self, dateobj_from, dateobj_to=None, count=100):
        self.log.debug("STARTED get_rates ")
        result = []
        data = None
        not_finished = True
        if self.api_ready() == True:
            period_from = timestring_from_date(dateobj_from)

            if dateobj_to is not None:
                period_to = timestring_from_date(dateobj_to)
                payload = { 'period_from' : period_from, 'period_to' : period_to, 'page_size' : count }
            else:
                payload = { 'period_from' : period_from, 'page_size' : count }
 
            headers = {'content-type': 'application/json'}
            weburl = self.costUrl

            while not_finished:
                self.log.debug(f"new weburl = [{weburl}]")  
                response = requests.get(weburl,headers=headers,auth=(self.apiKey,''),params=payload)
                self.log.debug("result of call = ["+str(response)+"].")
                # check we got a 200 return code
                if response.status_code  != 200:
                    self.log.debug(f"Call Failed - aborting [{response.status_code}]")
                    break
                # pull the JSON data from the web response.
                data = response.json()

                # If we have not got another page - set theloop to terminate
                if data['next'] == None:
                    # last page - end the loop
                    self.log.debug("did not get any page continuation data")
                    not_finished = False
                else:
                    # We havea snother page of data to retrieve
                    self.log.debug("Got page continuation data")
                    weburl = data['next']  

                # SAve the results    
                result+=data['results']

        self.log.debug("FINISHED get_rates ")
        return result

##############################################################################
#  get_usage - call Octopus to get usage for dateobj_from to dateobj_to  
##############################################################################
    def get_usage(self, dateobj_from, dateobj_to=None):
        self.log.debug("STARTED get_usage ")
        result = None
        data = None
        if self.api_ready() == True:

            period_from = timestring_from_date(dateobj_from)
 
            if dateobj_to is not None:
                period_to = timestring_from_date(dateobj_to)
                payload = { 'period_from' : period_from, 'period_to' : period_to, 'page_size' : 25000 }
            else:
                payload = { 'period_from' : period_from, 'page_size' : 25000 }
 
 
            headers = {'content-type': 'application/json'}
            response = requests.get(self.consumptionUrl,headers=headers,auth=(self.apiKey,''),params=payload)
            self.log.debug("result of call = ["+str(response)+"].")
            data = response.json()
            self.log.debug("json data in response = ["+str(data)+"].")
            result = data['results']
        self.log.debug("FINISHED get_usage ")
        return result






        










