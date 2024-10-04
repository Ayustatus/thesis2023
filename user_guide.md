#installation
This project currently only works on linux.
To start using this project you need to source the file **"env.sh"**. When sourcing the file you have to stand in the project root.
You might need to read the report in [./thesis.pdf](./thesis.pdf) to fully understand the explainations.

# usage
There are 2 entry points in this project. One for the dataset generator and one for the AI-models.
both are in the file main.py and can be called by simple *python* **dataset/main.py** and *python* **ml_model/main.py**.


##dataset generator
To start using the dataset generator a config file needs to be created. The file is a xml file that contains the vms that needs to be created along with the 
traffic and attacks that are to be made.

This file needs to follow the xmlschema found in **dataset/configurations/xml_schema.xsd**.
A example file exists by the name of **dataset/configurations/test.xml**. But as a brief overview the file is divided into 5 parts
defaults,general,individual,traffic and attacks.
Defaults is an optional object that contains some default values for virtualbox vms such as ram,os etc.
General is an object that contains general information that is needed no matter what system its running on such as how many vms are to be made and how they can be divided into subnets as well as a maximum timer for how long the generator is allowed to run for.

Individual is a set of objects that is optional. Each object is used to override default or general values for more specific ones.

Traffic is an object that contains a set of traffic instances. Each instance corresponds to one script that needs to be run on one or more vms to generate traffic.
Attacks is structured in the same way as traffic but is for generating attacks. 
For full specs see the schema file at **dataset/configurations/xml_schema.xsd**.

Then you run python dataset/main.py config_file. This will start generating data and then creating a dataset file.
## configuration files
 The configuration files should be created in the folder [dataset/configurations](dataset/configurations). They should follow the schema file that also exists in that folder.
## managers
 The managers should be created under the [dataset/managers](dataset/managers) folder and support the interface that exist in there.

## Traffic
 To add traffic you need to add a script under [dataset/shared_files/traffic_scripts](dataset/shared_files/traffic_scripts).
The script will need to create its own meta file with the source and destination
ip and port along with the start and end time of the script. It also needs to add a False at the end to show its not an attack.

### Servers
To add internal servers you need to add a folder under the servers folder. In that folder you need to create two files. server.py and sitemap.xml. The server.py is responsible for creating and starting the server along with any other resource like databases etc. The sitemap.xml file is a derivation of the standard sitemap usually found on webservers. Instead of having absolute urls and metadata about them these sitemaps need to have the relative path of the url e.g. "/charts" for "example.com/charts" along with the method and json arguments. E.g for a login page the sitemap entry would be:
<url><loc>/login</loc><json><arg>username</arg><arg>password</arg></json></url>

This is to allow the internal webtraffic scripts to call the methods with arguments without a full blown crawler to simulate entering the information in fields.
NOTE: The sitemap has to be callable/getable via /structure
## Attacks
 Attacks can be added py adding scripts under [dataset/shared/files/attack_scripts](dataset/shared_files/attack_scripts).
The attack should be added under appropriete structure which can be found in the report.
Attack scripts will also need to create a meta data file.

## ATOMIC RED TEAM
Needs to be installed separetly due to security concerns(preferbly only in your own vms)
Note that ssh config needs to be done for this to work
add subsystem, allow pubke auth etc.
IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing);
Install-AtomicRedTeam -getAtomics -InstallPath /home/test-user/thesis2023/dataset/shared_files/attack_scripts/atomic


change /etc/systemd/resolved.conf
[Resolve]
DNS=8.8.8.8

sudo apt-get update
sudo apt-get install -y wget apt-transport-https software-properties-common
source /etc/os-release
wget -q https://packages.microsoft.com/config/ubuntu/$VERSION_ID/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y powershell


sudo visudo add %sudo ALL=(ALL) NOPASSWD: ALL
have ssh key
add ssh key to auth keys

change /etc/ssh/sshd_config
ensure PubKeyAuthXXX yes
ensure PublicPassXXX no
add Subsystem powershell /usr/bin/pwsh -sshs -nologo

ensure netstat installed :sudo apt install net-tools

## transformers
The transformers should be created under [dataset/transformers](dataset/transformers)
and support the interface that exist in there.

##AI model
To run the AI model you need 1-3 dataset files.
Then run it vis *python* **ml_model/main.py --validation-file file1 --training-file file2 --evaluation-file file3**.
You will also need to specify the model that you want to train. All parameters can be found in the main file.

You can add models by adding them under [ml_model/training_models](ml_model/training_models)
You can also add different dataset file handlers under [ml_model/dataset_creators](ml_model/dataset_creators).
Any new dataset handler should extend the base_dataset.
