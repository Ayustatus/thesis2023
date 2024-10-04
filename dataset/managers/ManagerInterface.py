import math
import time
import constants as c
import sys
import threading


from gen_utils import convert_to_sec

def handler():
    pass



class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, timeout,type_val, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False
        thread = threading.Thread(target=_timeout_kill,args=[self,timeout])
        thread.start()
        self.type_val = type_val

 
    def start(self):
        self.__run_backup = self.run
        self.run = self.__run      
        threading.Thread.start(self)
    
    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup


 
    def globaltrace(self, frame, event, arg):
        print("doing a global trace")
        print(str.format('self:{0}, frame:{1},event:{2},arg:{3}',self,frame,event,arg))
        if event == 'call':
            return self.localtrace
        else:
            return None
 
    def localtrace(self, frame, event, arg):
        print("in local trace")
        print(self.type_val)
        print(str.format('self:{0}, frame:{1},event:{2},arg:{3}',self,frame,event,arg))
        if self.killed:
            print(event)
            if event == 'line':
                print("rasing syskill")
                raise SystemExit()
            if event == 'exception':
                print("rasing exception")
                print(arg)
        return self.localtrace
 
    def kill(self,manager):
        self.killed = True
        if self.type_val == "trace":
            manager.kill_trace(self)
        #raise(signal.SIGTERM)
       # raise Exception()
    
def _timeout_kill(thread,timeout):
    time.sleep(timeout)
    thread.kill()


class ManagerInterface:
    def __init__(self,vms,args,max_depth,max_groups):
        # The vms to create
        self.vms = vms
        # The arguments the main process was launched with
        self.args= args
        # The dict containing all traffic that is to be generated
        self.traffic_dict = None
        # The dict containing all attacks that is to be used
        self.attack_dict = None
        # The max depth of sub groups in the network
        self.max_depth = max_depth
        # The max amount of devices at any level of the network
        self.max_groups = max_groups
        # The map of target name to ip-address
        self.ip_map = {}
        # The next free ip address
        self.curr_free_ip = 2
        #  The subnet value. Dependant on max_group and max_depth
        self.subnet = None
        # The amount of DelayedProcesses that will be created. Used for the barrier.
        self.script_count = 0
        # The barrier that will block until all processes are complete
        self.barrier = None
        # The path to the managers folder
        self._parent_folder = __file__[0:-20] 
        # The tcpdumps/traces that are monitoring the connections {name:object}
        self.traces = {}
        # The threads that the manager has spawned.(Except trace threads since they will be in self.traces)
        #In format [thread]
        self.threads = {"perpetual":[],"transient":[]}

        self.threads_interval = []

    
    def _exit(self):
        sys.exit(1)

    def set_barrier(self,barrier):
        self.barrier = barrier
    def create_vms(self):
        raise Exception("Not Yet Implemented")

    def set_traffic(self,traffic):
        raise Exception("Not Yet Implemented")

    def start_traffic(self,general_info):
        raise Exception("Not Yet Implemented")        

    def reshare(self,check=False):
        if check:
            return False
        return None
    
    def set_attacks(self,attacks):
        raise Exception("Not Yet Implemented")

    def start_attacks(self,general_info):
        raise Exception("Not Yet Implemented")

    def get_fullname(self,vm):
        raise Exception("Not Yet Implemented")

    def join(self):
        raise Exception("Not Yet Implemented")
    
    def stop_tracking(self):
        raise Exception("Not Yet Implemented")

    def coalesce(self):
        raise Exception("Not Yet Implemented")
    
    def calc_scripts(self,traffic_dict,attack_dict,max_time_dict):
        for instance in traffic_dict:
            origin_vm = None
            if c.ORIGIN in instance:
                origin_vm =  self.get_vm(instance[c.ORIGIN])
            if self.should_multi_run(instance,max_time_dict):
                self.script_count += self.multi_run_counter(instance[c.MODEL],max_time_dict)
            else:
                if origin_vm is None:
                    self.script_count += len(self.vms)
                else:
                    self.script_count += 1
        for instance in attack_dict:
            origin_vm =  self.get_vm(instance[c.ORIGIN])
            if self.should_multi_run(instance,max_time_dict):
                self.script_count += self.multi_run_counter(instance[c.MODEL],max_time_dict)
            else:
                if origin_vm is None:
                    self.script_count += len(self.vms)
                else:
                    self.script_count += 1
        max_time = convert_to_sec(max_time_dict[c.MAX_DURATION],max_time_dict[c.DURATION_TYPE])
        self.threads_interval = [[] for i in range(math.ceil((max_time-300)/180) +1)]

    def should_multi_run(self,instance,gen_info):
        # if script explicitly says to run more than once or if the frequency is less than max duration of program.
        if (c.AMOUNT in instance[c.MODEL] and int(instance[c.MODEL][c.AMOUNT]) > 1) or\
              self.frequency_calc(instance[c.MODEL]) < convert_to_sec(gen_info[c.MAX_DURATION],gen_info[c.DURATION_TYPE]):
            return True
        return False

    def frequency_calc(self,model):
       sec_to_divide= convert_to_sec(1,model[c.FREQUENCY_TYPE])
       return int(sec_to_divide/int(model[c.FREQUENCY]))
    

    def multi_run_counter(self,model,gen_info):
        sleep_time = self.frequency_calc(model)
        if c.AMOUNT in model:
            return int(model[c.AMOUNT])
        else: # frequency less
            count = 0
            max_sec= convert_to_sec(gen_info[c.MAX_DURATION],gen_info[c.DURATION_TYPE])
            for i in range(0,max_sec,sleep_time):
                count += 1
            return count
                

    def _additive_power(self,a,b):
        if b != 0:
            return self._power(a,b) + self._additive_power(a, b - 1)
        else:
            return 1

    def _power(self,a, b):
        if b != 0:
            return a * self._power(a, b - 1)
        else:
            return 1
        
    def get_vm(self,name):
        if name in self.vms:
            return self.vms[name]
        for vm_name in self.vms:
            if self.get_fullname(self.vms[vm_name]) == name:
                return self.vms[vm_name]
        print("Error 404 VM not found")
        return None
        

    def calc_ip_addr(self,device,root=False):
        max_needed = self._additive_power(self.max_groups,self.max_depth) + 1 # +1 is for root bridge
        bits = max_needed.bit_length()
        subnet = 32-bits
        self.subnet = subnet
        if root:
            self.ip_map['root-bridge'] = str.format('10.0.0.1/{0}',subnet) 
            return str.format('10.0.0.1/{0}',subnet)
        bin_addr = '00001010' + '0'*(subnet-8) # 10. and then 0 until subnet
        curr_len = len(bin_addr)
        bin_free = bin(self.curr_free_ip)[2:] # remove the first 2 to remove 0b from string
        bin_addr += '0'*(32-curr_len-len(bin_free)) # add 0 for the padding within subnet until actual adress
        bin_addr += bin_free #add tail end of adresss
        self.curr_free_ip += 1 #increment which ip is free
        addr = self._binary_to_ip(bin_addr)
        if hasattr(device,'name'):
            self.ip_map[device.name] = str.format('{0}/{1}',addr,subnet)
        else:
            self.ip_map[device['name']] = str.format('{0}/{1}',addr,subnet)
        return  str.format('{0}/{1}',addr,subnet)

    def _binary_to_ip(self,bin_addr):
        first_8 = bin_addr[:8]
        second_8 = bin_addr[8:16]
        third_8 = bin_addr[16:24]
        fourth_8 = bin_addr[24:]
        num_1 = self._binary_convert(first_8)
        num_2 = self._binary_convert(second_8)
        num_3 = self._binary_convert(third_8)
        num_4 = self._binary_convert(fourth_8)
        return str.format('{0}.{1}.{2}.{3}',num_1,num_2,num_3,num_4)
        
    def _binary_convert(self,eigth_bit_string):
        value = 128
        result = 0
        for digit in eigth_bit_string:
            val = int(digit)
            result += val*value
            value = value >> 1
        return result
    
    def _get_folder(self):
        return self._parent_folder
    
    def kill_all(self):
        raise Exception("Not Yet implemented")


