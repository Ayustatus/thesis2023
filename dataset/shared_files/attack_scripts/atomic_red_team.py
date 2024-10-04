import argparse    
import os
import subprocess
import time
from dataset.utils import get_output_folder
from gen_utils import write_meta_file, get_folder

parser = argparse.ArgumentParser(description="Create calls to atomic red team attacks and create meta file about it")
parser.add_argument("--target",help="other vm or device to connect to.")
parser.add_argument("--source",help="Source device(used for meta data)",required=True)
parser.add_argument("--duration",help="how long should the script run for in seconds",default=None)
parser.add_argument("--attack",help="Specific attack to do")
parser.add_argument("--nameOption",help="Specific subattack id format")
parser.add_argument("--nameOptionVal",help="Specific subattack id")
parser.add_argument("--src-port",help="Specific port to attack from")#
parser.add_argument("--tgt-port",help="Specific port to attack")#
parser.add_argument("--key-path",help="Absolute path to ssh key file")
parser.add_argument("--schedule",help="Absolute path to csv file containing all the attacks that needs to made")

folder = get_folder(__file__)
args = parser.parse_args()
arg_dict = vars(args)
start_time =  int(time.time() * 1000)
#invoke attack
path_str = os.path.join(folder, "atomic","invoke-atomicredteam","Invoke-AtomicRedTeam.psd1")
atomic_path = os.path.join(folder, "atomic","atomics")

target = None
nameOpt = arg_dict["nameOption"]
nameVal =  arg_dict["nameOptionVal"]

#$myArgs = @{ "file_name" = "c:\Temp\myfile.txt"; "ads_filename" = "C:\Temp\ads-file.txt"  }

if "target" in arg_dict: # Remote attack
    target = arg_dict["target"]

if "schedule" in arg_dict and arg_dict["schedule"] is not None: # multiple attacks in certain order defined by schedule.
    wrapper_path = os.path.join(__file__[0:-19],"atomic_red_team_schedule_wrapper.ps1")
    exec_arr = ['sudo', 'pwsh',wrapper_path,'-module',path_str,'-atomic',atomic_path,'-duration',arg_dict["duration"],'-target',target,
                '-schedule',arg_dict["schedule"],'-user','test-user','-passwd',arg_dict["key_path"],"-cleanup","True"]
else: # single attack
    wrapper_path = os.path.join(__file__[0:-19],"atomic_red_team_wrapper.ps1")
    exec_arr = ['sudo', 'pwsh',wrapper_path,'-module',path_str,'-atomic',atomic_path,'-duration',arg_dict["duration"],'-test',arg_dict["attack"],
                '-target',target,'-nameOptionOpt',nameOpt,'-nameOptionVal',nameVal,'-user','test-user','-passwd',arg_dict["key_path"],"-cleanup","True"]

if "input_arg" in arg_dict:
    exec_arr.append("-input-args")
    exec_arr.append(arg_dict["input_args"])
print("running atr attack")
#print(exec_arr)
result = subprocess.run(exec_arr,capture_output=True,timeout=int(arg_dict["duration"]))
print(result)
result_stdout_string =  result.stdout.decode()
first_process_set,second_process_set =result_stdout_string.split("Target Port")
#TODO make use of pre and post process check to remove old or other ssh connections
end_time = int(time.time()*1000)

source = arg_dict["source"]

destPorts = []
if arg_dict["tgt_port"]:
    destPorts.append(arg_dict["tgt_port"])
#print(result_stdout_string)
string_arr = result_stdout_string.split("Target Port:")[1:]  # remove the first since all target port will be after this print
#print("destPort trace")
#print(string_arr)
tgt_port_arr = [string_arr[i].split(';')[0] for i in range(len(string_arr))] # remove any remaining text and leave only port numbers
#print(tgt_port_arr)
for port_num in tgt_port_arr:
    destPorts.append(port_num)
#print("destPorts")

srcPorts = []
if arg_dict["src_port"]:
    srcPorts.append(arg_dict["src_port"])
src_temp_string_arr_before =first_process_set.split('\n')
src_temp_string_arr_after =second_process_set.split('\n')
#all lines with both source ip and target ip in line
src_n_target_lines_arr_before = [line for line in src_temp_string_arr_before if source in line and target in line]
src_n_target_lines_arr_after = [line for line in src_temp_string_arr_after if source in line and target in line]
target_port_lines =  []
for line in src_n_target_lines_arr_after:
    if line not in src_n_target_lines_arr_before:
        for port in destPorts:
            if  port in line.split(target)[1] or "ssh" in line.split(target)[1]: # port exists after target ip(so not matching ports or take port from source)
                target_port_lines.append(line)
src_port_arr = [line.split(str.format('{0}:',source))[1].split(' ')[0] for line in target_port_lines ] # extracts the port number from the source
#print(src_port_arr)
for port_num in src_port_arr:
    srcPorts.append(port_num)
#print(srcPorts)

#print(destPorts)
if target is None: 
    target = source

meta_line = str.format("{0}:SRC_PORT,{1}:TGT_PORT,{2},{3},True",source,target,start_time,end_time)
meta_lines = []

# Some ports may be in a one to one if so this can be improved.
for src_port in srcPorts:
    temp_line = meta_line.replace("SRC_PORT",src_port)
   # print("temp_line")
  #  print(temp_line)
    for dest_port in destPorts:
        temp_line = temp_line.replace("TGT_PORT",dest_port)
 #       print(temp_line)
        meta_lines.append(temp_line)

ts = time.time()
print("writing to meta file")
folder_path = os.path.join(get_output_folder(),"temp")
filename = os.path.join(folder_path,str.format("atr_{0}_{1}.txt",source,int(ts*1000)))
write_meta_file(folder_path,filename,meta_lines)
print("attack script complete")