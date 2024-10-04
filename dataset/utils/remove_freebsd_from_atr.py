import os

from gen_utils import get_folder

keywords = ['freebsd']
folder = get_folder(__file__)

atomics = os.path.join(folder, "../shared_files", "attack_scripts", "atomic", "atomics")
for file_name in os.listdir(atomics):
    if file_name.startswith("T"):
        with open(os.path.join(atomics,file_name,str.format("{0}.yaml",file_name))) as oldfile, open(os.path.join(atomics,file_name,str.format("tmp_{0}.yaml",file_name)), 'w') as newfile:
            for line in oldfile:
                if not any(keyword in line for keyword in keywords):
                    newfile.write(line)
for file_name in os.listdir(atomics):
        if file_name.startswith("T"):
            os.rename(os.path.join(atomics,file_name,str.format("tmp_{0}.yaml",file_name)),os.path.join(atomics,file_name,str.format("{0}.yaml",file_name)))