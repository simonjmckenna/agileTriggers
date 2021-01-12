###################################################################
# Basic Flask App
##################################################################
from flask import Flask, render_template, request, redirect, Response
from werkzeug.exceptions import abort
from config import configFile,buildFilePath
from agileTriggers import costTriggers
from agile import OctopusAgile
from mylogger import mylogger
from datetime import datetime, timedelta
import calendar
import sys
import io
import random
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvas

############################################################################
#  Create the flask App
############################################################################
app = Flask(__name__)

############################################################################
#  setup config
############################################################################
# build the config path
configPath=buildFilePath('~',".agileTriggers.ini")
if  configPath == False:
    print (f"webapp abandoned execution config file missing:{configPath}")
    raise sys.exit(1)
else:
    config=configFile(configPath)

############################################################################
#  setup logger
############################################################################
logPath=config.read_value('filepaths','log_folder')
if logPath == None:
    print ("webapp abandoned execution log path missing:")
    raise sys.exit(1)

day = (datetime.utcnow()).day
logFile=buildFilePath(logPath, f"webapp_{day:02d}.log")
log = mylogger("webapp",logFile,True)   

############################################################################
# Create the Octopus Agile Object
############################################################################
my_account=OctopusAgile(config,log)

log.debug("Completed init of my_account")

############################################################################
#  main functon for web root shows today
############################################################################
@app.route('/', methods=["GET"])
def index():
    log.debug("STARTED webapp index()")
    year_list=[]
    month_list=["01","02","03","04","05","06","07","08","09","10","11","12"]
    day_list=["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31"]
    year_list = my_account.get_data_years()
    log.debug(f"year list is {year_list}")
    log.debug("FINISHED webapp index()")
    td=datetime.utcnow()
    
    return render_template('index.html',app_site_name=my_account.app_site_name,year_list=year_list,month_list=month_list,day_list=day_list,year=td.year,month=td.month,day=td.day)

############################################################################
#  main functon for web about
############################################################################
@app.route('/about', methods=["GET"])
def show_about():
    log.debug("STARTED webapp show_about()")
    log.debug("FINISHED webapp show_about()")
    return render_template('about.html',app_site_name=my_account.app_site_name)
############################################################################
#  main functon for web root shows today
############################################################################
@app.route('/root_form', methods=["POST"])
def root_form():
    log.debug("STARTED webapp root_form()")
    year = request.form.get("year_dropdown")
    month= request.form.get("month_dropdown")
    day = request.form.get("day_dropdown")
    log.debug(f"year={year} month={month} day={day}")
    log.debug("FINISHED webapp root_form()")
    return redirect(f"/{year}-{month}-{day}/data")
############################################################################
#  show_today function for web /today shows today
############################################################################
@app.route('/today', methods=["GET"])
def show_today():
    log.debug("STARTED webapp show_today()")
    
    today=datetime.utcnow()
    # octopus_data = my_account.get_period_data(today.year,today.month,today.day)
    result = show_day(today.year,today.month,today.day)

    #titlestring=f"Octopus Agile data for {today.day:02d}/{today.month:02d}/{today.year}"
    #daily_total=get_period_total(octopus_data)
    log.debug("FINISHED webapp show_today()")

    return result 
############################################################################
#  show_day functon for each day 
############################################################################
@app.route('/<int:year>-<int:month>-<int:day>/data', methods=["GET"])
def show_day(year,month,day):
    log.debug("STARTED webapp show_day()")
    
    octopus_data = my_account.get_period_data(year,month,day)
    prev=get_previous_day(year,month,day)
    next=get_next_day(year,month,day)
    if octopus_data == [] :
        log.debug("no data returned")
        titlestring=f"No Data Available for {day:02d}/{month:02d}/{year}"
        result = render_template('daytable.html', app_site_name=my_account.app_site_name,titlestring=titlestring, octopus_data=octopus_data, prev=prev, next=next)
    else:
        titlestring=f"Octopus Agile data for {day:02d}/{month:02d}/{year}"
        daily_total=f"£{get_period_total(octopus_data)/100:8.3f}"

        log.debug(f"previous={prev}, next={next}")
        log.debug("FINISHED webapp show_day()")
        result = render_template('daytable.html', app_site_name=my_account.app_site_name,titlestring=titlestring, octopus_data=octopus_data, daily_total=daily_total, prev=prev, next=next)
    return result

############################################################################
#  get_period_total get the totl costs for the period
############################################################################
def get_period_total(octopus_data):
    total = 0.0
    for period in octopus_data:
        total+= float(period[3])
    return total

############################################################################
#  get_previous_day get the previous day
############################################################################
def get_previous_day(year,month,day):
    previous = datetime(year,month,day) - timedelta(days=1)
    result=f"{previous.year:04d}-{previous.month:02d}-{previous.day:02d}"
    return result
############################################################################
#  get_next_day get the next day
############################################################################
def get_next_day(year,month,day):
    next = datetime(year,month,day) + timedelta(days=1)
    result=f"{next.year:04d}-{next.month:02d}-{next.day:02d}"
    return result


@app.route('/<int:year>-<int:month>-<int:day>/plot.png', methods=["GET"])
def plot_png(year,month,day):
    log.debug(f"STARTED webapp plot_png({year},{month},{day})")
    fig = create_figure(year,month,day)
    log.debug("one")
    output = io.BytesIO()   
    log.debug("one")
    FigureCanvas(fig).print_png(output)
    log.debug("one")

    log.debug("FINISHED webapp plot_png()")
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(year,month,day):
    log.debug(f"STARTED webapp create_figure({year},{month},{day})")
    daysinmonth = calendar.monthrange(year,month)[1]
    x_days = range(daysinmonth)
    y_cost = [0] * daysinmonth
    y_use  = [0] * daysinmonth
   
    log.debug(f"building plots webapp create_figure({year},{month},{day})")
    # Create the subplots
    fig, (ax1, ax2) = plt.subplots(2, 1)
    # make a little extra space between the subplots
    fig.subplots_adjust(hspace=0.5)

    log.debug(f"querying database  webapp create_figure({year},{month},{day})")
    octopus_data = my_account.get_period_data(year,month)
    for entry in octopus_data:
        # got a months worth of entries total up the days
        day = int(entry[0].split('/')[0])
        log.debug(f"entry data = [{entry}] day=[{day}]")
        if float(entry[2]) != -999.99:
            y_cost[day] += float(entry[3])
            y_use[day] += float(entry[2])
    
    log.debug(f"cost values={y_cost}")
    log.debug(f"use  values={y_use}")

    ax1.plot(x_days, y_cost)
    ax1.set_xlabel('day of month')
    ax1.set_ylabel('cost (pence)')
    ax1.grid(True)

    ax2.plot(x_days, y_use)
    ax2.set_xlabel('day of month')
    ax2.set_ylabel('usage (Kw/h)')
    ax2.grid(True)

    log.debug("FINISHED webapp create_figure()")
    return fig