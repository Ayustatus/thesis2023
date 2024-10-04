import os

import gen_constants as c
import subprocess

def convert_sec_to_milli(sec):
    return sec*1000

def convert_to_millisec(value,val_type):
    sec = convert_to_sec(value,val_type)
    return convert_sec_to_milli(sec)

def convert_milli_to_sec(milli):
    return milli/1000

def convert_to_sec(value,val_type):
    if val_type.lower() == "sec" or val_type.lower() == "second":
        return int(value)
    if val_type.lower() == "min" or val_type.lower() == "minute":
        return int(value)*c.SECONDS_IN_MINUTE
    if val_type.lower() == "hour":
        return int(value)*c.SECONDS_IN_HOUR
    if val_type.lower() == "day":
        return int(value)*c.SECONDS_IN_DAY
    if val_type.lower() == "month":
        return int(value)*c.SECONDS_IN_MONTH
    if val_type.lower() == "year":
        return int(value)*c.SECONDS_IN_YEAR
    
def write_meta_file(folder_path,filename,lines):
    exec_string= str.format('mkdir -p {0}',folder_path)
    result = subprocess.run(exec_string.split(' '),capture_output=True)
    exec_string_2= str.format('sudo chmod ugo+rwx {0}',folder_path)
    result_2 = subprocess.run(exec_string_2.split(' '),capture_output=True)
    #print(lines)
    with open(filename,"w+") as file:
        for line in lines:
            file.write(line)
            file.write("\n")

def get_folder(full_file_path):
    file_name_length = len(os.path.basename(full_file_path))
    return __file__[0:-file_name_length - 1]