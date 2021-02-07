########################################################################
# config.py - Core librry file to manage a config file for an app
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
from agileTools import buildFilePath
import sys
import logging
import os
import configparser

CONFIGPATH = "/home/ipace/.agiletrigger.ini"


class configFile:
    # the logger we use
    log = None
    # the config file
    config = None
    # The path to the config gile
    configFilePath = None

##############################################################################
#  __init__ class init for configFile class 
##############################################################################
    def __init__ (self, configFilePath=None, theLogger=None):
        # initialise the logfile
        if theLogger == None:
            theLogger = nulLogger()
        self.log = theLogger
        self.log.debug("STARTED __init__")


        if configFilePath == None:
            self.configFilePath = CONFIGPATH 

        if os.path.isfile(configFilePath) == False:
            print (f" getRates abandoned execution config file missing:{configFilePath}")
            self.configFilePath = None

        else:
            self.__load_config_file(configFilePath)

        self.log.debug("FINISHED __init__ ")

##############################################################################
#  set_logger  - reset the logger used for this class instance
##############################################################################
    def set_logger (self, theLogger):
         self.log = theLogger

##############################################################################
#  __load_config_file  process the config file for data
##############################################################################
    def __load_config_file(self,configFilePath):
        self.log.debug("STARTED __load_config_file")

        # open and read the config file into a parser
        self.config = configparser.ConfigParser()
        result = self.config.read(configFilePath)
        self.log.debug(f"config read result =[{result}]")

        self.log.debug("FINISHED __load_config_file")


##############################################################################
#  read_value  - return a section and field value
##############################################################################
    def read_value (self, section,field):
        self.log.debug("STARTED  read_value")
        try:
            result = (self.config[section][field]).strip('"')

        except KeyError as err:
            self.log.error("config file has unknown key entry : {0}".format(err))
            result=None
        except ValueError:
            self.log.error("Could not process data.")
            result=None
        except:
            self.log.error(f"Unexpected error in config file: {sys.exc_info()[0]}")
            self.log.error (f"file: {self.configFilePath}")
            result=None

        if result != None :
            self.log.debug(f"CONFIG:[{section}][{field}] value:{result}")
        self.log.debug("FINISHED read_value")

        return result

##############################################################################
