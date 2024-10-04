import os
import dataset.constants as c
from gen_utils import get_folder

folder = get_folder(__file__)


def strip_filename_to_ts(name):
    name_with_ending = name.split("_")[1]
    if "." in name_with_ending:
        return name_with_ending.split(".")[0]
    return name_with_ending
    
def get_internal_shared_folder():
    return os.path.join(folder, "../shared_files")

def get_shared_folders(args):
    result = []  
    chosen_val = args[c.SHARED_FOLDER]
    if chosen_val != c.DEFAULT_SHARED_FOLDER_LOCATION and chosen_val != "ENV_VAR":
        result.append(chosen_val)

    value = os.getenv(c.SHARED_FOLDER_ENV_VAR,"ENV_VAR")
    if value == "ENV_VAR" and args[c.SHARED_FOLDER] == "ENV_VAR":
        print("ERROR NO ENV VAR SET FOR SHARED FOLDER")
    
    if value != "ENV_VAR":
        for vals in value.split(os.pathsep):
            result.append(vals)
    result.append(get_internal_shared_folder())
    return result # will be in order user specified,env_var,internal

def get_internal_output_folder():
    return os.path.join(folder, "../shared_files", "output")

def get_output_folder(args = {c.OUTPUT:c.DEFAULT_OUTPUT_LOCATION}):
    if args[c.OUTPUT] != c.DEFAULT_OUTPUT_LOCATION and args[c.OUTPUT] != "ENV_VAR":
        return args[c.OUTPUT]
    
    if args[c.OUTPUT] == "ENV_VAR":
        value = os.getenv(c.OUTPUT_FOLDER_ENV_VAR,"ENV_VAR")
        if value == "ENV_VAR":
            print("ERROR NO ENV VAR SET FOR OUTPUT FOLDER")
        else:
            # TODO check if it will always get a pathsep on the end.
            if os.pathsep in value:
                print("ERROR multiple output folders")
            return value
    return get_internal_output_folder()

def get_internal_trace_folder():
    return os.path.join(folder, "../shared_files", "output", "pcap_files")

def get_trace_folder(args):
    if args[c.TRACE] != c.DEFAULT_TRACE_LOCATION and args[c.TRACE] != "ENV_VAR":
        return args[c.TRACE]
    
    if args[c.TRACE] == "ENV_VAR":
        value = os.getenv(c.TRACE_FOLDER_ENV_VAR,"ENV_VAR")
        if value == "ENV_VAR":
            print("ERROR NO ENV VAR SET FOR TRACE FOLDER")
        else:
            return value
    return get_internal_trace_folder()

def get_pcap_files(args,start,end):
    parent_folder = get_trace_folder(args)
    return get_files(parent_folder,start,end,ending=".pcap")

def get_files(parent_folder,start,end,ending=".txt",depth=-1):
    if depth == 0:
        return []
    results = []
    all_files =  [f for f in os.listdir(parent_folder) if
                os.path.isfile(os.path.join(parent_folder, f)) and f.endswith(ending)]

    files = [f for f in os.listdir(parent_folder) if
                os.path.isfile(os.path.join(parent_folder, f)) and f.endswith(ending) and int(start) <= int(strip_filename_to_ts(f)) and int(end) >= int(strip_filename_to_ts(f))]
    results += [os.path.join(parent_folder,f) for f in files]
    folders =[f for f in os.listdir(parent_folder) if
                os.path.isdir(os.path.join(parent_folder, f))]
    for folder_name in folders:
        sub_result = get_files(os.path.join(parent_folder,folder_name),start,end,ending,depth-1)
        if sub_result != []:
            results += sub_result
    return results
     

    
