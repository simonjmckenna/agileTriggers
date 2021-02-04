###################################################################
# Basic Flask App
##################################################################
from flask import Flask, render_template, request, redirect, Response
from werkzeug.exceptions import abort
from config import configFile,buildFilePath
from agileTriggers import costTriggers
from agileDB import OctopusAgileDB
from agileTriggers import costTriggers
from mylogger import mylogger
from datetime import datetime, timedelta
import calendar
import sys
import io

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
#  setup App perameters
############################################################################
app_site_name = config.read_value('settings','app_site_name')
if app_site_name == None:
    print ("webapp abandoned execution app_sitte_name missing:")
    raise sys.exit(1)
#############################################################################
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
my_database=OctopusAgileDB(config,log)

log.debug("Completed init of my_database")

############################################################################
#  manage_triggers() - display and manage triggers 
############################################################################
@app.route('/triggers/manage', methods=["GET"])
def manage_triggers():
    triggers=[]
    log.debug("STARTED webapp manage_triggers()")

    my_triggers= costTriggers(config,log)

    triggers= my_triggers.get_all_triggers()

    # Trigger [0] = Trigger NAme
    # Trigger [1] = Trigger Cost

    if triggers == None:
        print ("no triggers")
        triggers = [{"No Triggers","None"}]

    log.debug("FINISHED webapp manage_triggers()")

    return render_template('triggers.html',app_site_name=app_site_name,triggers=triggers)


############################################################################
#  show_day functon for monthly rollups from the homepage
############################################################################
@app.route('/<int:year>-<int:month>-<int:day>/month', methods=["GET"])
def show_month(year,month,day):
    log.debug("STARTED webapp show_month()")
    year_list=[]
    month_list=["01","02","03","04","05","06","07","08","09","10","11","12"]
    day_list=["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31"]
    year_list = my_database.get_db_data_years()
    log.debug(f"year list is {year_list}")

    next = get_next_month(year,month)
    prev = get_previous_month(year,month)
    log.debug("FINISHED webapp index()")

    return render_template('index.html',next=next,prev=prev,app_site_name=app_site_name,year_list=year_list,month_list=month_list,day_list=day_list,year=year,month=month,day=day)

############################################################################
#  main functon for web root shows today
############################################################################
@app.route('/', methods=["GET"])
def index():
    log.debug("STARTED webapp index()")

    td = datetime.utcnow()
    year = td.year
    month = td.month
    day =1
    log.debug("FINISHED webapp index()")

    return redirect(f"/{year:4d}-{month:02d}-{day:02d}/month")
 
############################################################################
#  main functon for web about
############################################################################
@app.route('/about', methods=["GET"])
def show_about():
    log.debug("STARTED webapp show_about()")
    log.debug("FINISHED webapp show_about()")
    return render_template('about.html',app_site_name=app_site_name)

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
    
    octopus_data = my_database.get_db_period_data(year,month,day)
    prev=get_previous_day(year,month,day)
    next=get_next_day(year,month,day)
    if octopus_data == [] :
        log.debug("no data returned")
        titlestring=f"No Data Available for {day:02d}/{month:02d}/{year}"
        result = render_template('daytable.html', app_site_name=app_site_name,titlestring=titlestring, octopus_data=octopus_data, prev=prev, next=next)
    else:
        titlestring=f"Octopus Agile data for {day:02d}/{month:02d}/{year}"
        daily_total=f"£{get_period_total(octopus_data)/100:8.3f}"

        log.debug(f"previous={prev}, next={next}")
        log.debug("FINISHED webapp show_day()")
        result = render_template('daytable.html', app_site_name=app_site_name,titlestring=titlestring, octopus_data=octopus_data, daily_total=daily_total, prev=prev, next=next)
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

    FigureCanvas(fig).print_png(output)

    log.debug("FINISHED webapp plot_png()")
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(year,month,day):
    log.debug(f"STARTED webapp create_figure({year},{month},{day})")
    daysinmonth = calendar.monthrange(year,month)[1]
    x_days = range(daysinmonth)
    y_cost =        [0] * daysinmonth
    y_use  =        [0] * daysinmonth
    y_costperkwh  = [0] * daysinmonth
   
    log.debug(f"building plots webapp create_figure({year},{month},{day})")
    # Create the subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    fig.set_size_inches(12,10)
    # make a little extra space between the subplots
    fig.subplots_adjust(hspace=0.5)

    log.debug(f"querying database  webapp create_figure({year},{month},{day})")
    octopus_data = my_database.get_db_period_data(year,month)
    for entry in octopus_data:
        # got a months worth of entries total up the days
        day = int(entry[0].split('/')[0])
        log.debug(f"entry data = [{entry}] day=[{day}]")
        if float(entry[2]) != -999.99:
            y_cost[day] += float(entry[3])
            y_use[day] += float(entry[2])
            y_costperkwh[day]  = y_cost[day]/y_use[day]
    
    
    ax1.bar(x_days, y_cost, color="red")
    ax1.set_xlim(1, daysinmonth)
    ax1.set_xlabel('day of month')
    ax1.set_ylabel('cost (pence)')
    ax1.grid(True)

    ax2.bar(x_days, y_use, color="green")
    ax2.set_xlim(1, daysinmonth)
    ax2.set_xlabel('day of month')
    ax2.set_ylabel('usage (Kw/h)')
    ax2.grid(True)

    ax3.bar(x_days, y_costperkwh, color="blue")
    ax3.set_xlim(1, daysinmonth)
    ax3.set_xlabel('day of month')
    ax3.set_ylabel('cost(pence) per Kw/h')
    ax3.grid(True)

    log.debug("FINISHED webapp create_figure()")
    return fig

############################################################################
#  get_previous_month get the previous day
############################################################################
def get_previous_month(year,month):
    day =1
    if month == 1:
        year -=1 
        month =12
    else:
        month = (month-1)
    result=f"{year:04d}-{month:02d}-{day:02d}"
    print(f"result={result}")
    return result
############################################################################
#  get_next_month get the next month
############################################################################
def get_next_month(year,month):
    day =1
    if month == 12:
        year +=1 
        month =1
    else:
        month = (month+1)
    result=f"{year:04d}-{month:02d}-{day:02d}"
    print(f"result={result}")
    return result
