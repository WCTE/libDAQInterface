import time # for sleep
import random # for random
# import cppyy and ctypes for interaction with c++ entities
import cppyy, cppyy.ll
import ctypes
import re
from datetime import datetime,timedelta
import csv
import time
import signal
import os
import numpy as np
import glob
from ftplib import FTP
import re
from datetime import datetime,timedelta
import csv
import time
import signal
control_panel = FTP("192.168.11.3","CERN1","12345")
control_panel.cwd('CERN')


def send_data(timestamp,variable_name_list,values):
  
  # populate the monitoring Store
  print("setting monitoring vals")
  for name,value in zip(variable_name_list,values):
    print(name,value)
    monitoring_data.Set(name, value)
  print("\n")
  # generate a JSON from the contents
  monitoring_json = std.string("")
  monitoring_data.__rshift__['std::string'](monitoring_json)

  # send to the Database for plotting on the webpage
  print("Sending to DB:", monitoring_json)
  sentData = DAQ_inter.SendMonitoringData(monitoring_json)
  print("sentData = ", sentData)
  if(sentData==False):
    print("DAQ_inter.SendMonitoringData: Failed to send data to database ")

  return 0


running=1
def signal_handler(sig, frame):
    global running
    print("Data uploading stopped.")
    running = False


def generate_time_intervals(interval):
    times = []
    current_hour = 0
    current_minute = 0

    while current_hour < 24:
        times.append(f"{current_hour:02}:{current_minute:02}")
        current_minute += interval
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute = current_minute % 60
    
    return times


def stable_operating(value_list,last_value_list):
  
  stable_flag=1
  
#Threshold for 

#0Date,1Time,2Pump_A_Sel_Auto,3Pump_A_Sel_Man,4Pump_B_Sel_Auto,5Pump_B_Sel_Man,6Pump_A_In_OL,7Pump_B_In_OL,8Pump_A_Motor,9Pump_B_Motor,10MixTank_High,11MixTank_Low,12LeakDetector,
#13RemovalTank_High,14PT1_Pressure,15QC1_Conductivity,16QC2_Conductivity,17FT1_Flow,18PT2_Pressure,19UT1_Depth,20LT1_Level,21PT3_Level,22PT6_Depth,23PT5_Depth,24Salinity,25TDS,
# 26UT1_Conductivity,27UT1_Temperature,28Fault_Register



#                        2 , 3,  4, 5  , 6 ,           7 , 8 , 9 , 10, 11       12,13 ,14  ,15  ,16 ,       17, 18 , 19 , 20 , 21 ,      22,23,24,25,26,27      
  threshold = np.array([0.5,0.5,0.5,0.5,0.5,          0.5,0.5,0.5,0.5,0.5,      0.2,0.2,0.2,0.2,0.1,         0.2,0.1,0.03,0.03,0.03,     0.5,0.05,1,5,10,0.3],dtype=float)

  
  new_value=np.array(value_list[2:],dtype=float)
  last_value=np.array(last_value_list[2:],dtype=float)
  #print(new_value.shape,last_value.shape,np.abs(new_value-last_value).shape,len(value_list),len(last_value_list))
  #for i,name in enumerate(data_list):
     #print(i+1,name)

  variable_changing_fast = np.abs(new_value-last_value)[0:26]>threshold
  if variable_changing_fast.any():
     stable_flag=0
     for flag,name in zip(variable_changing_fast,data_list[2:]):
        if flag==1:
           
           print("!"+name +" is changing fast")
           #print(variable_changing_fast)


  return stable_flag


# def find_the_latest_valid_CSV(require_time,data_list):
  
#   value_list = []
#   valid_flag=1

#   for i in range(10):
#     local_file = '/home/wcte/water/FTP/data/' + (require_time-timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S") + '.CSV'
#     #print(local_file)
#     if os.path.exists(local_file)==0:
#         valid_flag=0
#     else:
      
#       with open(local_file, mode='r', newline='') as csvfile:
#         reader = csv.reader(csvfile)
#         for row in reader:
#           value_list.extend(row)

#       if len(value_list)!=len(data_list) or bool(re.match('^\d{2}-\d{2}-\d{4}$',value_list[0]))!=1 or bool(re.match('^\d{2}:\d{2}:\d{2}$',value_list[1]))!=1:
#         valid_flag=0
      
#     if valid_flag==1:
#       return value_list
#     else:
#       continue

#   return 0






def find_the_latest_valid_row(data_list):
  
  value_list = []
  files = glob.glob(os.path.join('data', "*"))
  latest_file = max(files, key=os.path.getmtime)
  
  if os.path.getsize(latest_file) == 0:
      return 0
  
  with open(latest_file, 'r') as file:
    reader = csv.reader(file)
    for row in reader:
      value_list =row
           
  valid_flag=1
  
  #print(value_list)
  if len(value_list)!=len(data_list) or bool(re.match(r'^\d{2}-\d{2}-\d{4}$',value_list[0]))!=1 or bool(re.match(r'^\d{2}:\d{2}:\d{2}$',value_list[1]))!=1:
      valid_flag=0
  else:
     for v in value_list:
        if v=='':
          return 0
  #print(len(value_list)!=len(data_list),bool(re.match(r'^\d{2}-\d{2}-\d{4}$',value_list[0]))!=1,bool(re.match(r'^\d{2}:\d{2}:\d{2}$',value_list[1]))!=1)
  if valid_flag==1:
    return value_list
  else:
    return 0


def find_the_latest_remote_CSV(files):
    csv_files = [file for file in files if file.lower().endswith('.csv')]
    if not csv_files:
        print("No CSV files found.")
        return None
    else:
        return max(csv_files, key=lambda file: control_panel.sendcmd(f"MDTM {file}"))


print("file list scanning")
files = control_panel.nlst()
latest_file = find_the_latest_remote_CSV(files)
if latest_file is None:
    print("No CSV files found.")
else:
    print("found the latest data")
    latest_file_lines = []
    control_panel.retrbinary(f'RETR {latest_file}', latest_file_lines.append)
    if latest_file_lines:
        first_line = latest_file_lines[0].decode().strip()
        with open("data_format.CSV",mode='w',newline="") as f:
            f.write(re.findall('^[^\n]*\n',first_line)[0])

control_panel.quit()

print("done")

control_panel = FTP("192.168.11.3","CERN1","12345")
control_panel.cwd('CERN')




data_list = []

with open('data_format.CSV', mode='r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        data_list.extend(row)
print("We are going to send device:\n")
print(data_list[2:])






# streamline accessing std namespace
std = cppyy.gbl.std
# pull in classes from the libDAQInterface
try:
  cppyy.load_reflection_info('libDAQInterfaceClassDict')
except:
  raise BaseException("class dictionary not found: did you run 'make python'?") from None
from cppyy.gbl import ToolFramework
from cppyy.gbl.ToolFramework import DAQInterface

# configuration
Interface_configfile = "./InterfaceConfig"
#database_name = "daq"

print("Initialising daqinterface")
# initialise DAQInterface
DAQ_inter = DAQInterface(Interface_configfile)
device_name = DAQ_inter.GetDeviceName()
print("for "+device_name+"\n")

def send_alarm(alarm_register, device_name,value_list):
    
    alarm_massage_list =(
       "","","","","",
       "","","","","",
       "","","","FT-1 too low "+value_list[17]+"t/h","PT-2 too low "+value_list[18]+"bar","PT_1 too low "+value_list[14]+"bar",
       "FT-1 too high "+value_list[17]+"t/h","PT-2 too high "+value_list[18]+"bar","PT_1 too high "+value_list[18]+"bar","Leakage","Pump B Overload",     
       "Pump A Overload","Pump B Failed to start","Pump A Failed to Start","Low Tank Level","High Tank Level",     
       "","","Detector Level High "+value_list[20]+"m","Detector Level Low "+value_list[20]+"m","Low Pressure Shutdown","Low Pressure Max Count Fault")

    for i,masse in zip(alarm_register,alarm_massage_list):
        
        if i == "1":
            DAQ_inter.SendAlarm(masse, 0, device_name)
    return 0

monitoring_data = cppyy.gbl.ToolFramework.Store()
# clear any values from the monitoring Store
monitoring_data.Delete()
# Note that 'Store::Set' calls to existing keys will overwrite old values, so calling 'Delete'
# just ensures no entries that weren't 'Set' before it's invoked carry over.
# Of course in the specific case here we make the same series of 'Set' calls on every loop,
# so calling 'Delete' is redundant as all keys will either be overwritten or re-created.

signal.signal(signal.SIGINT, signal_handler)

interval = 1
time_points = generate_time_intervals(interval)

last_value_list =np.zeros(len(data_list))
timer=0
send_threshold=60
print("start loop")


last_alarm_rigister=format(0, '016b') + format(0, '016b')


DAQ_inter.sc_vars["Status"].SetValue("Initializing")


print("input S to start")
input()
print("Uploading data from PLC, Ctrl+C to stop")


while running:

  if timer>65:
    #print("time_out")
    DAQ_inter.sc_vars["Status"].SetValue("TIME_OUT")

  #print(timer)
  # request_time = datetime.now() #+ timedelta(hours=1) - timedelta(minutes=1,seconds=30)
  # seconds = request_time.second
  # minutes = request_time.minute
  # hours = request_time.hour

  # minute_and_hour_string = f"{hours:02}:{minutes:02}"
  # send_flag = (seconds>=59) & (minute_and_hour_string in time_points)
  file_count = len(files)
  files = control_panel.nlst()
  if len(files) != file_count:
      print("Checking for new remote file")
      latest_file = find_the_latest_remote_CSV(files)

  #request_time = datetime.now() + timedelta(hours=1) - timedelta(minutes=1,seconds=14)
  #remote_file = 'CERN/'+request_time.strftime("%m%d%H")+'.CSV'
  #remote_file = find_the_latest_remote_CSV()
  local_file = 'data/' + latest_file

  if latest_file is None:
      print("Failed to find remote file...")
  else:
      #print(f"Getting data from {latest_file}, saving to {local_file}")
      
      
      with open(local_file,mode='wb') as f:
          control_panel.retrbinary(f'RETR {latest_file}', f.write)




  value_list = find_the_latest_valid_row(data_list)
  
  if value_list==0:
    print("latest data invalid. Ignore this second")
    time.sleep(1)
    timer = timer+1
    continue

  dt = datetime.strptime(value_list[0]+value_list[1], '%d-%m-%Y%H:%M:%S')
  
  unix_timestamp_ms = int(dt.timestamp() * 1000)
  #print(value_list)

  
  
  if stable_operating(value_list,last_value_list):
    send_threshold=60
  else:
    send_threshold=5
  
  
  alarm_register = format(int(value_list[29]), '016b') + format(int(value_list[28]), '016b')


  if timer>65:
    #print("time_out")
    DAQ_inter.sc_vars["Status"].SetValue("TIME_OUT")
  else:
    if int(alarm_register)!=0:
      DAQ_inter.sc_vars["Status"].SetValue("ALARM")
    else:
       DAQ_inter.sc_vars["Status"].SetValue("OK")




  if (alarm_register!=last_alarm_rigister) :
    last_alarm_rigister = alarm_register
    if alarm_register!=format(0, '016b') + format(0, '016b'):
      send_alarm(alarm_register,device_name,value_list)
  
  #print(timer, send_threshold)
  if timer>=send_threshold:
     print(dt) 

     sending_value_list = value_list[10:28]
     sending_data_list = data_list[10:28]
     sending_value_list.append(value_list[-1])
     sending_data_list.append(data_list[-1])
     send_data(unix_timestamp_ms,sending_data_list,sending_value_list)
     timer=0

  time.sleep(1)
  last_value_list = value_list
  timer = timer+1
  
  