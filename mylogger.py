########################################################################
# mylogger.py - Core library file for the application logging 
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

import sys
import logging


class nulLogger:
    def __init__(self):
        pass

    def debug(self,message):
        pass

    def info(self,message):
        pass

    def error(self,message):
        pass

class mylogger:
    logger = None
    to_screen=False

##############################################################################
#  __init__ class init for mylogger class
##############################################################################
    def __init__(self, logname, logdest=None, is_debug=False,to_screen=False):
        self.logger = logging.getLogger(logname)
        FORMAT="%(asctime)s:%(levelname)s: %(message)s"
        if is_debug == True:
            LEVEL="DEBUG" 
        else:
            LEVEL="INFO" 
        if logdest == None:
            # Not logging to a file - but to a stream
            logging.basicConfig(format=FORMAT,level=LEVEL,stream=sys.stderr)
        else:
            # logging to a file (logdest)
            logging.basicConfig(format=FORMAT,level=LEVEL,filename=logdest) 
        self.logger.info("New Log Instance Started")

##############################################################################
#  debug  - if we're in debug mode write a message otherwise ignore it.
##############################################################################
    def debug(self,message):
        if self.to_screen:
            print(f"DEBUG :{message}")
        self.logger.debug(message)

##############################################################################
#  error  - write an error message
##############################################################################
    def error(self,message):
        if self.to_screen:
            print(f"ERRROR:{message}")
        self.logger.error(message)

##############################################################################
#  info  - write an info message
##############################################################################
    def info(self,message):
        if self.to_screen:
            print(f"INFO  :{message}")
        self.logger.info(message)

