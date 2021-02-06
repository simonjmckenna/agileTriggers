########################################################################
# agileTools.py - support library file for the database and API calls to Ocotpus
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
import sys
import os


yroffset=2020

############################################################################
#  buildfilepath - build a path to a file expanding path substitutions
############################################################################
def buildFilePath(directory,file):
     path = os.path.expanduser(directory)
     result = os.path.isdir(path)
     if result == True:
         result =  f"{path}/{file}" 
     return result
    
############################################################################
#  check permission - is file permission valid
############################################################################
def check_permission(permission,isdir):
    dir = 0
    if isdir: dir = 1
    result = None
    if len(permission) == 3:
        for chr in permission:
            val = int(chr) - dir
            if val == -1 or val == 0 or val == 2 or val == 4 or val == 6:
                result = permission
            else:
                result = None

    return result


##############################################################################
#  builddateobj - take an input string of the format 
##############################################################################
def builddateobj(datestring):
    result = None
    day = 1
    month = -1
    year = -1
    dateobj = None

    d2decade = ((int((datetime.utcnow().year)/10)*10)+10)
    # date format (date not time) is dd/mm/(yy-YYYY) OR mm/(yy-YYYY) - spint into fields
    date = datestring.split('/')

    # We work on 2 or 3 fields - otherwise something is wrong.
    if len(date)  < 2 or len(date) > 3:
        pass
    else:
        if len(date) == 2:
            # set the year as if it was post 2000
            year  = checkyy_year(date[1])
            month = checkmm_month(date[0])
        else:
            year =  checkyy_year(date[2])
            month = checkmm_month(date[1]) 
            day =   checkdd_day(date[0])
            
        if year != -1 or month != -1 or day != -1:
            dateobj = datetime(year,month,day)

    return dateobj

##############################################################################
#  checkyy_year- work out the full year number from yearstr in yy format 
#  return year as an integer
#  return -1 if invalid 
###############################################################################
def checkyy_year(yearstr):
    year = -1
    d2decade = ((int(datetime.utcnow().year)/10)*10)+10
    try:
        year=int(yearstr)
        # if we have a 2 digit year set the year as if it was post 2000
        if year < 100: year += 2000
    except ValueError as error:
        year = -1
        # if the calculated year is in the next decade keep it otherwise go back 100 years 
        # if current year is 2021 '29 refers to 2029 31 referss to 1931
    if year > d2decade : year -= 100 
    return year

##############################################################################
#  checkmm_month- work out the month number from the monthstr (in mm format) 
#  return month as an integer
#  return -1 if invalid 
###############################################################################
def checkmm_month(monthstr):
    try:
        month=int(monthstr)
        # months obvs are 1..12
        if month > 12 or month < 1: month = -1 
    except ValueError as error:
        month = -1
    return month

##############################################################################
#  checkdd_month- work out the month number from the monthstr (in mm format) 
#  return month as an integer
#  return -1 if invalid  
###############################################################################
def checkdd_day(daystr):
    try:
        day=int(daystr)
        # simple check - for 1..31 days in a month
        if day > 31 or day < 1: day = -1 
    except ValueError as error:
        day = -1
    return day

##############################################################################
#  gen_periodno_date - work out the period number from the start of yroffset 
###############################################################################
def gen_periodno_date(dateobj):
    result = gen_periodno(dateobj.year,dateobj.month,dateobj.day,dateobj.hour,dateobj.minute)
    return result

##############################################################################
#  gen_periodno - work out the period number from the start of yroffset 
##############################################################################
def gen_periodno(year,month,day,hour,minute):
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

    return periodno

##############################################################################
#  date_from_periodno - get a dateobj from a periodno
##############################################################################
def date_from_periodno(periodno):
    year  = int(periodno / 17856) + yroffset 
    month = int((periodno % 17856) / 1488)
    day   = int((periodno % 1488) / 48)
    hour  = int((periodno % 48) / 2)
    minute= int((periodno % 2))
    theDate = datetime(year,month,day,hour,minute)

    return theDate
              
##############################################################################
#  timestring_from_date - get a timestring from a date object
##############################################################################
def timestring_from_date(dateobject):
    result =  datetime.strftime(dateobject, '%Y-%m-%dT%H:%M:%SZ')
    return result

##############################################################################
#  gen_timestring - generate the date/time in necesary format  from raw numbers
##############################################################################
def gen_timestring(year,month,day,hour,minute,second):
    # format is '%Y-%m-%dT%H:%M:%SZ' 
    result= f"{year:4d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    return result

##############################################################################
#  time_now - get the date/time now and return it in necesary format 
##############################################################################
def time_now():
    result =  datetime.utcnow()
    return result
        
##############################################################################