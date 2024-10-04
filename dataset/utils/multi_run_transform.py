import os
base_line = "python3 dataset/main.py dataset/training_data.xml --no-create --no-traffic --start XXXXXXXXXXXXX --end YYYYYYYYYYYYY > dataset/shared_files/output/output_240123_ZZZZ_trans_AAh.txt 2>&1"
start_12 = "1705681000000"
end_12 =   "1705800000000"

time = "0000"
hour_twelve = "12"
hour_twofour = "24"
start_24 = "1705500000000"
end_24 = "1705680000000"
base_12 = base_line.replace("XXXXXXXXXXXXX",start_12).replace("YYYYYYYYYYYYY",end_12).replace("ZZZZ",time).replace("AA",hour_twelve)
base_24 = base_line.replace("XXXXXXXXXXXXX",start_24).replace("YYYYYYYYYYYYY",end_24).replace("ZZZZ",time).replace("AA",hour_twofour)
print(base_12)
print(base_24)
os.system(base_12)
os.system(base_24)
