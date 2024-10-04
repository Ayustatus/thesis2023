import argparse    
import os
from _rng_external_https import main as rng_main
parser = argparse.ArgumentParser(description="Create calls to websites via https")
parser.add_argument("--source",help="Source device(used for meta data)",required=True)
parser.add_argument("--target",help="other vm or device to connect to. Will be none since this is to external websites")
parser.add_argument("--duration",help="how long should the script run for in seconds",default=300)
parser.add_argument("--site",help="Specific site to connect to.",default=[])
parser.add_argument("--depth",help="How deep to dive in each site.",default=5)

args = parser.parse_args()
arg_dict = vars(args)
cfg_file = os.path.join(__file__[0:-18],'rng_external_https_config.json')
rng_main(cfg_file,source=arg_dict["source"],timeout=arg_dict['duration'],roots=arg_dict['site'],depth=arg_dict['depth'])
print("external traffic script is complete")