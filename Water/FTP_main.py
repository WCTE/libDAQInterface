from ftplib import FTP
import re
from datetime import datetime,timedelta
import csv
import time
import signal
control_panel = FTP("192.168.11.3","CERN1","12345")
control_panel.cwd('CERN')


def find_the_latest_remote_CSV(files):
    csv_files = [file for file in files if file.lower().endswith('.csv')]
    if not csv_files:
        print("No CSV files found.")
        return None
    else:
        return max(csv_files, key=lambda file: control_panel.sendcmd(f"MDTM {file}"))

print("Updating data_format...")

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

running = True

def signal_handler(sig, frame):
    global running
    print("Data uploading stopped.")
    running = False

# 绑定信号处理程序
signal.signal(signal.SIGINT, signal_handler)

control_panel = FTP("192.168.11.3","CERN1","12345")
control_panel.cwd('CERN')

print("input S to start")
input()
print("Uploading data from PLC, Ctrl+C to stop")
while running:
    # check if number of files has changed, find new latest files if the count changed
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
        print(f"Getting data from {latest_file}, saving to {local_file}")
        
        
        with open(local_file,mode='wb') as f:
            control_panel.retrbinary(f'RETR {latest_file}', f.write)

    time.sleep(0.9)
    

control_panel.quit()
