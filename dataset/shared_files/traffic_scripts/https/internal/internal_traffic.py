import argparse
import json    
import os
import time
import requests
import random
import string
import datetime
import xml.etree.ElementTree as ET
from dataset.utils import get_output_folder

from gen_utils import convert_sec_to_milli, write_meta_file

parser = argparse.ArgumentParser(description="Create calls to internal webinterfaces via https")

parser.add_argument("--source",help="Source device(used for meta data)",required=True)
parser.add_argument("--target",help="other vm or device to connect to.")
parser.add_argument("--duration",help="how long should the script run for in seconds",default=None)
# TODO add the following parameter in a meaningful way and remove the override on line 17
parser.add_argument("--sitemap-parser",help="Specific way to parse the sitemap.",default=None)
parser.add_argument("--folder",help="folder containing cert file server.csr",required=True)
parser.add_argument("--port",help="Specific port to access.",default=80)

args = parser.parse_args()
arg_dict = vars(args)
arg_dict['sitemap-parser'] = None
site = arg_dict['target']
if site.startswith("https://"):
    site = site[9:]
target = site
traffic_scripts_folder = __file__[0:-35]
site = str.format('https://{0}:{1}',site,arg_dict['port'])
start_ts = int(convert_sec_to_milli(time.time()))
verify_path = os.path.join(traffic_scripts_folder,arg_dict["folder"],"server.csr")
sitemap_response = requests.get(str.format('{0}/structure',site),verify=verify_path)
print(sitemap_response.content)
root_elem = ET.fromstring(sitemap_response.content)


ns = {"ns":"http://www.sitemaps.org/schemas/sitemap/0.9"}
def parse(tree):
    url_map = {}
    for url in tree.findall("ns:url",ns):
        url_dict = {}
        for url_child in url:
            if url_child.tag.endswith('}json'):
                args = {}
                for arg_elem in url_child:
                    args[arg_elem.text] = "string" if arg_elem.attrib == {} else arg_elem.attrib['type']
                url_dict['json'] = args
            else:
                url_dict[url_child.tag[len(ns["ns"])+2:]] = url_child.text
        url_map[url_dict["loc"]] = url_dict
    return url_map

tree_map = parse(root_elem)

def random_string():
        return ''.join(random.choices(string.ascii_uppercase  + string.ascii_lowercase, k = 16))

def random_time(start_time=None):
    if start_time is None:
        start_time = datetime.datetime.min
    end_time = datetime.datetime.now()
    random_time = random.random() * (end_time - start_time) + start_time
    return random_time
json_login_token = None
if '/login' in tree_map:
    credential_resp = requests.post(str.format('{0}/login',site),json={'username':'test-user','password':'password'},verify=verify_path)
    print(credential_resp)
    cred_dict = json.loads(credential_resp.content.decode('utf-8'))
    json_login_token = cred_dict["access_token"]


for url_name in tree_map:
    filters = {}
    url = tree_map[url_name]
    if url_name != "/login":
        if url['method'] == 'GET':
            if url['login'] == 'true':
                print("login reqed")
                print(json_login_token)
                print("token is between")
                #result = requests.get(str.format('{0}/{1}',site,url['loc']),verify=verify_path,headers={'Authorization': str.format("access_token {0}",json_login_token)})
                
                result = requests.get(str.format('{0}/{1}',site,url['loc']),verify=verify_path,headers={'Authorization': str.format("Bearer {0}",json_login_token)})
                #result = requests.get(str.format('{0}/{1}',site,url['loc']),verify=verify_path,headers={'Authorization': str.format("token {0}",json_login_token)})
            else:
                result = requests.get(str.format('{0}/{1}',site,url['loc']),verify=verify_path)
            print(result)
        elif url['method'] == 'POST':
            json_data={}
            for attrib in url['json']:
                if url['json'][attrib] == 'datetime':
                    #TODO maybe ensure datetime end is after begin
                    json_data[attrib] = str(random_time())
                elif url['json'][attrib] == 'string':
                    json_data[attrib] = random_string()
                else: # type = multiple values comma separated
                    options = url['json'][attrib].split(',')
                    json_data[attrib] = random.choice(options)
            if url['login'] == 'true':
                #print("login reqed")
                #print(json_login_token)
                #print("token is between")
                result = requests.post(str.format('{0}/{1}',site,url['loc']),json=json_data,verify=verify_path,headers={'Authorization': str.format('Bearer {0}',json_login_token)})
            else:
                #print("no login reqed")
                result = requests.post(str.format('{0}/{1}',site,url['loc']),json=json_data,verify=verify_path)
            print(result)
end_ts = int(convert_sec_to_milli(time.time()))
line = str.format("{0}:{1},{2}:{3},{4},{5},{6}",arg_dict["source"],"SRC_PORT",target,arg_dict['port'],start_ts,end_ts,"False")
folder_path = os.path.join(get_output_folder(),"temp")
filename = os.path.join(folder_path,str.format("internal_https_{0}_{1}.txt",arg_dict["source"],int(end_ts*1000)))
write_meta_file(folder_path,filename,[line])

print("internal traffic script is complete")