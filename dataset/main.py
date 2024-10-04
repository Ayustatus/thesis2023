from multiprocessing import Barrier
import argparse
import traceback
import time
import os
import importlib

from gen_utils import convert_sec_to_milli, get_folder
from dataset.utils.xmlparser import Parser
import dataset.constants as c

managers = {}
managers_ignored = ["__init__.py","ManagerInterface.py"]
manager_names = []

transformers = {}
transformers_ignored = ["__init__.py","transformer_interface.py"]
transformers_names = []
folder = get_folder(__file__)

def dynamic_import(subfolder,ignored_arr,result_object,name_arr):
    files = [f for f in os.listdir(os.path.join(folder,subfolder)) if
                os.path.isfile(os.path.join(folder, subfolder, f)) and f.endswith(".py") and f not in ignored_arr]
    for file in files:  # dynamically import each manager to allow easy additions of managers
        try:
            name, extension = file.rsplit('.', 1)
            fullname = str.format("{0}.{1}",subfolder,name)
            module = importlib.import_module(fullname)
            result_object[name.lower()] = getattr(module, name)
            name_arr.append(name.lower())
        except Exception as e:
            print("Exception in dynamic import")
            print(e)
            traceback.print_exc()
    return result_object, name_arr

managers, manager_names = dynamic_import("managers",managers_ignored,managers,manager_names)
transformers, transformers_names = dynamic_import("transformers",transformers_ignored,transformers,transformers_names)

def main(arg_dict):
    file = arg_dict[c.FILE]
    if not os.path.exists(file):
        print("Error 404: file not found")
        return -1
    parser = Parser(file,arg_dict[c.SCHEMA_FILE])

    validate_result,validate_error = parser.validate_file()
    if arg_dict[c.VALIDATE]:
        if validate_error:
            print(validate_error)
        return validate_result

    vms,error = parser.parse_vms()
    if error != "good":
        print(error)
        return -2

    
    manager = managers[arg_dict[c.MANAGER_TYPE]](vms,arg_dict,parser.max_depth,parser.max_groups)
    if not arg_dict[c.NO_CREATE]:
        manager.create_vms()
    
    if manager.reshare(True):
        manager.reshare()
    ts = int(convert_sec_to_milli(time.time()))
    if not arg_dict[c.NO_TRAFFIC]:
        traffic,traffic_error = parser.parse_traffic()
        if traffic_error != "good":
            print(traffic_error)
            return -3
        attacks = []
        if not arg_dict[c.NO_ATTACK]:
            #start attacks
            attacks,attack_error = parser.parse_attacks()
            if attack_error != "good":
                print(attack_error)
                return -4
        manager.calc_scripts(traffic,attacks,parser.general_info)
        manager.set_barrier(Barrier(manager.script_count))
        ts = int(convert_sec_to_milli(time.time()))
        parser.general_info["start_time"] = ts
        manager.set_traffic(traffic)
        manager.set_traces(parser.general_info)
        manager.start_traffic(parser.general_info)
        if not arg_dict[c.NO_ATTACK]:
            manager.set_attacks(attacks)
            manager.start_attacks(parser.general_info)
        manager.start_threads()
        print("waiting on completion")
        manager.join()
        #here all traffic and attacks are done
        manager.stop_tracking()
        manager.coalesce()
    end_ts = int(convert_sec_to_milli(time.time()))
    print(str.format("start,end,elapsed of generating:{0},{1},{2}",ts,end_ts,end_ts-ts))
    use_given = False
    if not arg_dict[c.NO_TRANSFORM]:
        if arg_dict[c.START] != 0 and arg_dict[c.END] != 0:
            ts = int(arg_dict[c.START])
            end_ts = int(arg_dict[c.END])
            use_given = True
        transformer = transformers[arg_dict[c.TRANSFORMER_TYPE]](ts,end_ts,arg_dict)
        time.sleep(30)  # delay transformation to ensure proper closure of generation.
        transformer.transform(use_given)
    trans_ts_end = convert_sec_to_milli(time.time())
    print(str.format("start,end,elapsed of transformation:{0},{1},{2}",end_ts,trans_ts_end,trans_ts_end-end_ts))
    print(str.format("start,end,elapsed of program:{0},{1},{2}",ts,trans_ts_end,trans_ts_end-ts))
    print("Program is done")

    
def start():
    parser = argparse.ArgumentParser(description="Create and manage a dataset of encrypted network traffic with or without malware")
    # ALL systems
    parser.add_argument("file",help="Config file used to generate vms as well as run traffic and attacks.",default=c.DEFAULT_XML_CONFIG_ABS_PATH)
    parser.add_argument('-v','--validate',action='store_true', help="Only validate the file and quit",default=c.DEFAULT_ONLY_VALIDATE)
    parser.add_argument('--no-create',action='store_true',help="If vms should not be created",default=c.DEFAULT_NO_CREATE)
    parser.add_argument('--no-recreate',action='store_true',help="If vms should not be recreated if they already exists",default=c.DEFAULT_NO_RECREATE)
    parser.add_argument('--no-traffic',action='store_true',help="If traffic should not be generated, will also disable attacks",default=c.DEFAULT_NO_TRAFFIC)
    parser.add_argument('--no-attack',action='store_true',help="If no attacks should be made",default=c.DEFAULT_NO_ATTACK)
    parser.add_argument('--schema-file',help="Location of config schema",default=c.XML_SCHEMA_ABS_PATH) # schema file
    parser.add_argument('-sh','--shared-folder',help="Location of shared folder, defaults to internal folder",default=c.DEFAULT_SHARED_FOLDER_LOCATION)
    parser.add_argument('-o','--output',help="Location of output folder, if not present it will default to internal folder",default=c.DEFAULT_OUTPUT_LOCATION)
    parser.add_argument('-t','--trace',help="Location of trace folder, if not present it will default to internal folder",default=c.DEFAULT_TRACE_LOCATION)
    
    #SYSTEM decider
    parser.add_argument('--manager',choices=manager_names,help="Choose which system to run on",default="linux")
    parser.add_argument('--transformer',choices=transformers_names,help="Choose which system to run on",default="csvtransformer")
    

    #Transform pre generated traffic
    parser.add_argument('--start',help="unix timestamp for the start of the generated data in 13 digits",default=0)
    parser.add_argument('--end',help="unix timestamp for the end of the generated data in 13 digits",default=0)
    parser.add_argument('--no-transform',action='store_true',help="If transformation should be applied.",default=c.DEFAULT_NO_TRANSFORM)

    # OLD arguments  remaining from attempt at VirtualBOX manager implementation.
    # Linux VIA Windows
    #parser.add_argument('--vm-manager-loc',help="absolute path to VBoxManage.exe file",default=c.DEFAULT_VBOXMANAGE_LOCATION) # vmbox manage location
    #parser.add_argument('--iso-folder',help="Folder where iso file is located",default=c.DEFAULT_ISO_LOCATION) # iso location
    

    # Windows (includes all linux via windows arguments as well)
    #parser.add_argument('-s','--shared',help="name of shared folder in vms",default=c.DEFAULT_SHARED_FOLDER_NAME)
    #parser.add_argument('--vm-create-loc',help="Folder where vms get created",default=c.DEFAULT_VM_FOLDER) # vm creation location
    #parser.add_argument('-gc','--graphicscontroller',help="Which graphicscontroller to use",default=c.DEFAULT_GRAPHICS_CONTROLLER) # graphicscontroller
    #parser.add_argument('--pae',action='store_true',help="If PAE should be turned on",default=c.DEFAULT_PAE) # pae
    #parser.add_argument('--no-usb',action='store_true',help="If usb should be turned off",default=c.DEFAULT_USB) # usb
    #parser.add_argument('-ac','--audiocontroller',help="Which audiocontroller to use",default=c.DEFAULT_AUDIO_CONTROLLER) #audiocontroller
    #parser.add_argument('--reshare-folder',action='store_true',help="Attempt to create the shared folder. (Used when installation failed to do so)",default=False)
   

    args = parser.parse_args()
    arg_dict = vars(args)
    main(arg_dict)

if __name__ == "__main__":
    start()
