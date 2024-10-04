import os

from gen_utils import get_folder

folder = get_folder(__file__)

#environment variables:
SHARED_FOLDER_ENV_VAR = "DATASET_GEN_SHARED_FOLDER"
TRACE_FOLDER_ENV_VAR = "DATASET_GEN_TRACE_FOLDER"
OUTPUT_FOLDER_ENV_VAR = "DATASET_GEN_OUTPUT_FOLDER"

# global constants
DEFAULT_XML_CONFIG_ABS_PATH = os.path.join(folder, "configurations/test.xml")
XML_SCHEMA_ABS_PATH = os.path.join(folder, "configurations/xml_schema.xsd")
DEFAULT_SHARED_FOLDER_LOCATION = "INTERNAL"
DEFAULT_TRACE_LOCATION = "INTERNAL"
DEFAULT_OUTPUT_LOCATION = "INTERNAL"
DEFAULT_ONLY_VALIDATE = False
DEFAULT_NO_ATTACK = False
DEFAULT_NO_TRAFFIC = False
DEFAULT_NO_CREATE = False
DEFAULT_NO_RECREATE = False
DEFAULT_NO_TRANSFORM = False

# system specific defaults
VIRTUAL_BOX_INSTALL_LOCATION = os.getenv("VBOX_MSI_INSTALL_PATH",os.path.join("C:",os.sep,"Program Files","Oracle","VirtualBox"))
DEFAULT_ADDITION_ISO_LOCATION = os.path.join(VIRTUAL_BOX_INSTALL_LOCATION,"VBoxGuestAdditions.iso")
DEFAULT_VBOXMANAGE_LOCATION = os.path.join(VIRTUAL_BOX_INSTALL_LOCATION,"VBoxManage.exe")
DEFAULT_VM_FOLDER = os.path.join("C:",os.sep,"Users","ma-lob","VirtualBox VMs")
DEFAULT_ISO_LOCATION = DEFAULT_VM_FOLDER
DEFAULT_SHARED_FOLDER_NAME = "shared"

# VM specific defaults
DEFAULT_VRAM = 128
DEFAULT_STORAGE  = 50*1024
DEFAULT_CPUS = 1
DEFAULT_GRAPHICS_CONTROLLER = "vboxsvga"
DEFAULT_AUDIO_CONTROLLER = "hda"
DEFAULT_PAE = "off"
DEFAULT_USB = "on"


#Keywords used for input arguments
FILE = "file"
VALIDATE = "validate"
NO_ATTACK = "no_attack"
NO_CREATE = "no_create"
NO_RECREATE = "no_recreate"
NO_TRAFFIC = "no_traffic"
ISO_FILE = "iso_folder"
SCHEMA_FILE = "schema_file"
MANAGER_TYPE = "manager"
SHARED = "shared"
SHARED_FOLDER = "shared_folder"
OUTPUT = "output"
TRANSFORMER_TYPE = "transformer"
TRACE = "trace"
NO_TRANSFORM = "no_transform"
START = "start"
END = "end"

# Keywords used in config file
ORIGIN = "origin"
TARGET = "target"
GENERAL = "general"
INDIVIDUAL = "individual"
TRAFFIC = "traffic"
SCRIPT = "script"
MODEL = "model"
PARAMS = "params"
ATTACK = "attack"
DURATION = "duration"
DURATION_TYPE = "duration_type"
NAME = "name"
VALUE = "value"
AMOUNT = "amount"
FREQUENCY = "frequency"
FREQUENCY_TYPE = "frequency_type"
MAX_DURATION = "max_duration"
PERPETUAL = "perpetual"

PROTOCOL_CONVERSION_MAP = {"ssh":22,"https":443,"http":80} 