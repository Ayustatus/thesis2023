import subprocess
import time
from gen_utils import convert_sec_to_milli
exec_string_1 = "python3 dataset/main.py dataset/test.xml > dataset/shared_files/output/output_2312XX_XXXX.txt 2>&1"
exec_string_2 = "python3 dataset/main.py dataset/test2.xml > dataset/shared_files/output/output_2312YY_YYYY.txt 2>&1"
exec_string_3 = "python3 dataset/main.py dataset/test3.xml > dataset/shared_files/output/output_2312ZZ_ZZZZ.txt 2>&1"

start_ts = convert_sec_to_milli(time.time())
print("Running first file")
subprocess.run(exec_string_1.split(" "))
first_end = convert_sec_to_milli(time.time())
print(str.format("First file done, starting second,time elapsed(ms):{0}",first_end-start_ts))
subprocess.run(exec_string_2.split(" "))
second_end = convert_sec_to_milli(time.time())
print(str.format("Second file done, starting third,time elapsed(ms):{0}",second_end-first_end))
subprocess.run(exec_string_3.split(" "))
third_end = convert_sec_to_milli(time.time())
print(str.format("Third file done, ending,time elapsed(ms):{0}",third_end-second_end))
print(str.format("Programs complete, total time elapsed(ms):{0}",third_end-start_ts))