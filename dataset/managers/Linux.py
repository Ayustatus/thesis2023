import os
import sys
from threading import Thread,Timer
import time

import subprocess
from typing import Any
import constants as c
from gen_utils import convert_milli_to_sec, convert_to_sec,convert_to_millisec,convert_sec_to_milli
from dataset.utils import get_output_folder, get_shared_folders, get_trace_folder
from .ManagerInterface import ManagerInterface as Manager, StoppableThread
from multiprocessing import Pool, Process,current_process,active_children


CAPTURE_OUTPUT = True 

class RepeatTimer(Timer):  
    def run(self):  
        while not self.finished.wait(self.interval):  
            if not self.finished.is_set():
                self.function(*self.args,**self.kwargs) 
            else:
                break 
        self.finished.set()
        print("repeat timer is done")

class DelayedProcess(Process):

    def __init__(self,delay,time_info,log_args,attack,manager, *args, **keywords):
        Process.__init__(self,*args, **keywords)
        self.exec_device = log_args.split("ip netns exec ")[1].split(" ")[0]
        self.delay = delay
        self.has_started=False
        self.has_terminated=False
        self.time_info = time_info
        self.log_args = log_args
        self.attack = attack
        self.manager = manager
        self._start_time = None
        self._call_time = time.time()
        self._end_time = None

    def start(self):
        if not self.has_terminated:
            t = Thread(target=self._start,args=[])
            t.start()
    
    def _start(self):
        curr_time = time.time()
        pre_delay = curr_time - self._call_time
        if pre_delay < self.delay:
            time.sleep(self.delay-pre_delay)
        if not self.has_terminated:
            self.has_started=True
            self._start_time = convert_sec_to_milli(time.time())
            Process.start(self)
            self.manager._delayed_processes[self.pid] = self
        else:
            print(str.format("{0} terminated before start,no port info to get",self.name))
    
    def _get_timeout(self):
        start_time_in_milli = self.time_info["start_time"]
        max_time_in_milli = convert_to_millisec(self.time_info[c.MAX_DURATION],self.time_info[c.DURATION_TYPE])
        timeout_time_in_milli = start_time_in_milli + max_time_in_milli
        return convert_milli_to_sec(timeout_time_in_milli - convert_sec_to_milli(time.time()))                       

    def terminate(self):
        self.has_terminated=True 
        if self.is_alive():
            Process.terminate(self)
        if self._end_time == None:
            self._end_time = convert_sec_to_milli(time.time())


    def join(self):
        if self.is_alive():
            Process.join(self,self._get_timeout())
        self.has_terminated=True
        if self._end_time == None:
            self._end_time = convert_sec_to_milli(time.time())
        


class Linux(Manager):

    def __init__(self,vms,args,max_depth,max_groups):
        Manager.__init__(self,vms,args,max_depth,max_groups)
        self.shared_folders = None
        self.python_string = ""
        self._timers = {}
        self._processes = {}
        self._port_reports = []
        self._process_reports = []
        self._delayed_processes = {}

# setters and getters and modifiers
    def set_traffic(self,traffic):
        self.traffic_dict = traffic

    def set_attacks(self,attacks):
        self.attack_dict = attacks
    
    @classmethod
    def with_sudo(cls,input_str):
        #subprocess.run(["echo","password"]) # removed this by modifying sudo visudo to not require passwd
        #env PATH={1} PYTHONPATH={2}os.getenv("PATH") 
        return str.format('sudo -E env PYTHONPATH={1} {0}',input_str,os.getenv("PYTHONPATH"))
    
    def get_shared_folders(self):
        if self.shared_folders is not None:
            return self.shared_folders
        value = get_shared_folders(self.args)
        self.shared_folders = value
        return value
    
    def get_fullname(self,vm):
        ns_name = ""
        if vm.group != "":
            ns_name= str.format("{0}",".".join(vm.group.split("/")[1:])) # turn /test into test and /test/nested into test.nested
        ns_name += str.format('.{0}',vm.name)
        return ns_name
    
    def kill_all(self):
        for proc in self.threads["transient"]:
            exec_string= self.with_sudo(str.format('ip netns exec {0} kill -0 {1}',proc.exec_device,proc.pid))
            result = subprocess.run(exec_string.split(' '),capture_output=True)
            print(result.stdout.decode())
    
    def stop_tracking(self):
        print("attempting to stop traffic")
        print(self.traces)
        for trace_name in self.traces:
            self.traces[trace_name].terminate()
            self.traces[trace_name].join()
        print("tracking stopped")
        #for vm_port_listener in self._timers:
            #self._timers[vm_port_listener].cancel()

            #vm = self.get_vm(vm_port_listener)
            #if vm:
            #    self._calc_ports(self.ip_map[vm.name][:-3])
        print("port listening stopped")
            
    def join(self):
        for thread_interval_index in range(len(self.threads_interval)):
            for thread in self.threads_interval[thread_interval_index]:
                if thread.has_started:
                    thread.join()
                else:
                    print("Joining on not started thread")
                    while not thread.has_started:  
                        if time.time()*1000 >convert_to_millisec(thread.time_info[c.MAX_DURATION],thread.time_info[c.DURATION_TYPE]) + int(thread.time_info["start_time"]):
                            thread.terminate()
                            break
                    thread.join()
                    print("non started thread has now been completed")
        print("transient threads done")
        for thread in self.threads["perpetual"]:
            thread.terminate()
            thread.join()
        print("perpetual threads done")


    def coalesce(self):
        print("coalesce in progress")
        folder = get_output_folder(self.args)
        files = [f for f in os.listdir(os.path.join(folder,"temp")) if
            os.path.isfile(os.path.join(folder, "temp", f)) and f.endswith(".txt")]
        ts = time.time()
        output_filepath = os.path.join(folder,str.format("metadata_{0}.txt",int(ts*1000)))
        lines = {}
        with open(output_filepath,"w",encoding="UTF-8") as file:
            for input_filename in files:
                input_file = os.path.join(folder,"temp",input_filename)
                with open(input_file,"r") as i_file:
                    for line in i_file:
                        line = line.strip("\n")
                        line_parts = line.split(",")
                        if (line_parts[0],line_parts[1]) in lines:
                            lines[(line_parts[0],line_parts[1])].append((line_parts[2],line_parts[3],line))
                        else:
                            
                            lines[(line_parts[0],line_parts[1])] = [((line_parts[2],line_parts[3],line))]
                
            skipped_lines = 0  #purly log purpuse
            for ips in lines: 
                if len(lines[ips]) == 1:
                    file.write(lines[ips][0][2])
                    file.write("\n")
                elif "SRC_PORT" in ips:
                    continue  # undetermined src port(only for normal traffic which is okey to skip a few sessions in.)
                              # since we cant see if the timed subsections belong to same port or not.
                else:  # more than 1
                    for id in range(len(lines[ips])):
                        should_write = True
                        for id_2 in range(len(lines[ips])):
                            # if one line is a subset of the other
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] >= lines[ips][id][1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                            # if two lines are overlapping
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] <= lines[ips][id][1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                        if should_write:
                            file.write(lines[ips][id][2])
                            file.write("\n")
        
            print("skipped lines:",str(skipped_lines))
                        
        for filename in files:
            fullname = os.path.join(folder,"temp",filename)
            os.remove(fullname)
        

        #DP files
        # for vm in self.vms:
        #     files2 = [f for f in os.listdir(folder) if
        #         os.path.isfile(os.path.join(folder, f)) and f.endswith(".txt") and f.startswith(str.format("DP_{0}",self.ip_map[vm][:-3]))]
        #     ts2 = time.time()
        #     output_filepath = os.path.join(folder,str.format("DP_{0}_{1}_{2}.txt",self.ip_map[vm][:-3],int(ts2*1000),"full"))
        #     out_lines = []
        #     with open(output_filepath,"w",encoding="UTF-8") as file:
        #         for input_filename in files2:
        #             input_file = os.path.join(folder,input_filename)
        #             with open(input_file,"r") as i_file:
        #                 for line in i_file:
        #                     line =line.strip("\n")
        #                     if line not in out_lines:
        #                         file.write(line)
        #                         file.write("\n")
        #                         out_lines.append(line)
        #     #for filename in files2:
            #    fullname = os.path.join(folder,filename)
            #    os.remove(fullname)
        print("coalesce is done")
        
    def teardown(self,args):
        root_bridge_exists = self.bridge_exists('root-bridge')
        if not args[c.NO_RECREATE]:
            if root_bridge_exists:
                exec_string = self.with_sudo(str.format('ip link del name root-bridge type bridge'))
                subprocess.run(exec_string.split(' '))
        for vm_name in self.vms:
            vm = self.vms[vm_name]
            vm_exists = self.vm_exists(vm)
            if not args[c.NO_RECREATE]:
                if vm_exists:
                    bridges = vm.group.split("/")[1:]
                    for bridge_name in bridges:
                        exists = self.bridge_exists(bridge_name)
                        if exists:
                            #teardown
                            exec_string__1 = self.with_sudo(str.format('ip link del name {0} type bridge',bridge_name))
                            subprocess.run(exec_string__1.split(' '))
                            exec_string__2 = self.with_sudo(str.format('ip link del name veth-{0}-in type veth',bridge_name))
                            subprocess.run(exec_string__2.split(' '))
                            # exec_string__3 = self.with_sudo(str.format('ip link del name veth-{0}-out type veth',bridge_name))
                            # subprocess.run(exec_string__3.split(' '))

                    ns_name = self.get_fullname(vm)
                    exec_string_2 = self.with_sudo(str.format('ip netns del {0}',ns_name))
                    subprocess.run(exec_string_2.split(' '))
        time.sleep(30)

# creation
    def create_vm(self,vm,counter):
        ns_name = self.get_fullname(vm)
       # print("adding bridges")
        bridge_name = self.create_parent_bridges(vm,counter)
        #TODO non unique names
        print("adding netns")
        exec_string = self.with_sudo(str.format('ip netns add {0}',ns_name))
        subprocess.run(exec_string.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("adding link")
        exec_string_2 = self.with_sudo(str.format('ip link add veth-{0}-in type veth peer name veth-{0}-out',vm.name))
        subprocess.run(exec_string_2.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("connecting link to netns")
        exec_string_3 = self.with_sudo(str.format('ip link set veth-{0}-in netns {1}',vm.name,ns_name))
        subprocess.run(exec_string_3.split(' '),capture_output=CAPTURE_OUTPUT)
        ip_addr = self.calc_ip_addr(vm)
        #print("adding ip to netns")
        exec_string_4 = self.with_sudo(str.format('ip netns exec {0} ip addr add {1} dev veth-{2}-in',ns_name,ip_addr,vm.name))
        subprocess.run(exec_string_4.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("setting bridge to end of link")
        exec_string_5 = self.with_sudo(str.format('ip link set veth-{0}-out master {1}',vm.name,bridge_name))
        subprocess.run(exec_string_5.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("adding loopback interface")
        exec_string_6 = self.with_sudo(str.format('ip netns exec {0} ip link set dev lo up',ns_name))
        subprocess.run(exec_string_6.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("starting bridge side of link")
        exec_string_7 = self.with_sudo(str.format('ip link set veth-{0}-out up',vm.name))
        subprocess.run(exec_string_7.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("starting link")
        exec_string_8 = self.with_sudo(str.format('ip netns exec {0} ip link set dev veth-{1}-in up',ns_name,vm.name))
        subprocess.run(exec_string_8.split(' '),capture_output=CAPTURE_OUTPUT)
        #print("add default")
        exec_string_9 = self.with_sudo(str.format('ip netns exec {0} ip route add default via {1}',ns_name,self.ip_map[bridge_name][:-3]))
        result_9 = subprocess.run(exec_string_9.split(' '),capture_output=CAPTURE_OUTPUT)
        
        #ip netns exec namespace_A sshd -o PidFile=/run/sshd-namespace_A.pid
        #TODO fix issue with this string
        exec_sting_10 = self.with_sudo(str.format('ip netns exec {0} /usr/sbin/sshd -o PidFile=/run/sshd-{0}.pid',ns_name))
        result_10 = subprocess.run(exec_sting_10.split(" "),capture_output=CAPTURE_OUTPUT)
        print(result_10)
        exec_string_11 = self.with_sudo(str.format('ip netns exec {0} iptables-restore < /etc/network/firewall-{0}-v4',ns_name))
        result_11 = subprocess.run(exec_string_11.split(' '),capture_output=CAPTURE_OUTPUT) 
        print(result_11)
        exec_string_12 = self.with_sudo(str.format('mkdir -p /etc/netns/{0}/',ns_name))
        result_12 = subprocess.run(exec_string_12.split(' '),capture_output=CAPTURE_OUTPUT)
        print(result_12)
        exec_arr_13 = self.with_sudo("bash -c").split(' ')
        exec_arr_13.append(str.format('echo "nameserver 8.8.8.8" > /etc/netns/{0}/resolv.conf',ns_name))
        result_13 = subprocess.run(exec_arr_13,capture_output=False)
        print(result_13)

    def create_root_bridge(self,args):
        exists = self.bridge_exists('root-bridge')
        if not args[c.NO_RECREATE] or not exists:
            exec_string_2 = self.with_sudo(str.format('ip link add name root-bridge type bridge'))
            subprocess.run(exec_string_2.split(' '))
            exec_string_3 = self.with_sudo(str.format('ip link set root-bridge up'))
            subprocess.run(exec_string_3.split(' '))
            ip_addr = self.calc_ip_addr(None,root=True)
            exec_string_4 = self.with_sudo(str.format('ip addr add {0} dev root-bridge',ip_addr))
            subprocess.run(exec_string_4.split(' '))

    def create_vms(self):
        args = self.args
        pre_exec_string = str.format('which python')
        response = subprocess.run(pre_exec_string.split(' '),capture_output=CAPTURE_OUTPUT)
        if response.returncode == 0 and response.stdout != b'':
            self.python_string = "python"
        
        pre_exec_string_2 = str.format('which python3')
        response_2 = subprocess.run(pre_exec_string_2.split(' '),capture_output=CAPTURE_OUTPUT)
        if response_2.returncode == 0 and response_2.stdout != b'':
            self.python_string = "python3"
        exec_string_8 = self.with_sudo('ufw allow ssh')
        res_3 = subprocess.run(exec_string_8.split(' '),capture_output=True)
        print(res_3)
        self.teardown(args)
        self.create_root_bridge(args)
        vm_counter = 0
        for vm_name in self.vms:
            vm = self.vms[vm_name]
            exists = self.vm_exists(vm)
            if not args[c.NO_RECREATE] or not exists:
                self.create_vm(vm,vm_counter)
                vm_counter += 1

        filename = os.path.join(self._parent_folder[0:-9],"admin_req_scripts","add_nameserver.py")
        exec_string_3 = self.with_sudo(str.format('{0} {1} --file {2} --new-row',self.python_string,filename,"/etc/resolv.conf"))
        exec_arr = exec_string_3.split(' ')
        exec_arr.append('nameserver 8.8.8.8')
        res = subprocess.run(exec_arr,capture_output=True)
        print(res)
        exec_string_4 = self.with_sudo(str.format('iptables -t nat -A POSTROUTING -s 10.0.0.0/{0} -j MASQUERADE',self.subnet))
        subprocess.run(exec_string_4.split(' '))
        exec_string_5 = self.with_sudo(str.format('sysctl -w net.ipv4.ip_forward=1'))
        subprocess.run(exec_string_5.split(' '))

        print("VMs have been created")


    
    def create_parent_bridges(self,vm,counter):
        #TODO change naming so uniquness is not demanded
        parent = 'root-bridge'
        if vm.group != "":
            bridges = vm.group.split("/")[1:]
            for bridge_name in bridges:
                #print("checking existance")
                exists = self.bridge_exists(bridge_name)
                #print("existance checked")
                if not exists or (not self.args[c.NO_RECREATE] and counter == 0):
                    #print("creating bridge")
                    exec_string_2 = self.with_sudo(str.format('ip link add name {0} type bridge',bridge_name))
                    subprocess.run(exec_string_2.split(' '))
                    print("adding link")  # TODO the following command creates the RHNETLINk answer error
                    exec_string_3 = self.with_sudo(str.format('ip link add veth-{0}-in type veth peer name veth-{0}-out',bridge_name))
                    subprocess.run(exec_string_3.split(' '))
                    print("connecting link to self")
                    exec_string_4 = self.with_sudo(str.format('ip link set veth-{0}-in master {0}',bridge_name))
                    subprocess.run(exec_string_4.split(' '))
                    #print("connecting link to other")
                    exec_string_5 = self.with_sudo(str.format('ip link set veth-{0}-out master {1}',bridge_name,parent))
                    subprocess.run(exec_string_5.split(' '))
                    ip_addr = self.calc_ip_addr({'name':bridge_name})
                    #print("adding ip")
                    exec_string_6 = self.with_sudo(str.format('ip addr add {0} dev {1}',ip_addr,bridge_name))
                    subprocess.run(exec_string_6.split(' '))
                    #print("starting bridge")
                    exec_string_7 = self.with_sudo(str.format('ip link set {0} up',bridge_name))
                    subprocess.run(exec_string_7.split(' '))
                    #print("starting self part of link")
                    exec_string_8 = self.with_sudo(str.format('ip link set veth-{0}-in up',bridge_name))
                    subprocess.run(exec_string_8.split(' '))
                    #print("starting other part of link")
                    exec_string_9 = self.with_sudo(str.format('ip link set veth-{0}-out up',bridge_name))
                    subprocess.run(exec_string_9.split(' '))
                parent = bridge_name
        return parent
                    

# checks
    def vm_exists(self,vm):
        ns_name = self.get_fullname(vm)
        exec_string = self.with_sudo(str.format('ip netns list'))
        result = subprocess.run(exec_string.split(' '),capture_output=True)
        result_string = result.stdout #byte string
        result_arr = result_string.decode().split(os.linesep)
        for string_response in result_arr:
            if ns_name in string_response:
                return True
        return False
    
    def bridge_exists(self,name):
        exec_string = self.with_sudo(str.format('ip link show type bridge')) # does root bridge exist
        result = subprocess.run(exec_string.split(' '),capture_output=True)
        result_string = result.stdout #byte string
        result_arr = result_string.decode().split(os.linesep)
        for string_response in result_arr:
            if name in string_response:
                return True
        return False
    
    def set_traces(self,gen_info):
        for vm_name in self.vms:
                self.set_trace(self.vms[vm_name],gen_info)

#Traces
    def set_trace(self,vm,gen_info):
        if str.format("veth-{0}-out",vm.name) in self.traces:
            return
        trace_path = get_trace_folder(self.args)
        if vm.group != "":
            group_parts = vm.group.split("/")
            del group_parts[0]
            for part in group_parts:
                trace_path = os.path.join(trace_path,part)
        
        trace_dir = os.path.join(trace_path,vm.name)
        exec_string= self.with_sudo(str.format('mkdir -p {0}',trace_dir))
        result = subprocess.run(exec_string.split(' '),capture_output=CAPTURE_OUTPUT)
        print(result)
        exec_string_2= self.with_sudo(str.format('chmod ugo+rwx {0}',trace_dir))
        result_2 = subprocess.run(exec_string_2.split(' '),capture_output=True)
        
        ts = time.time()
        trace_path = os.path.join(trace_dir,str.format("{0}_{1}.pcap",vm.name,int(ts*1000)))

        t2 = Process(target=os.system,args=[self.with_sudo(str.format('tcpdump -U -i veth-{0}-out -w {1}',vm.name,trace_path))])
        self.traces[str.format("veth-{0}-out",vm.name)] = t2
        t2.start()
        #self._monitor_ports(self.get_fullname(vm))
        print("process tcpdump started")

    def _get_ports(self,device):
        exec_string= Linux.with_sudo(str.format('ip netns exec {0} ss -ptn',device))
        result = subprocess.run(exec_string.split(' '),capture_output=True)
        decoded_ports = result.stdout.decode()
        self._port_reports.append(decoded_ports)
        
        exec_string_2= Linux.with_sudo(str.format('ip netns exec {0} ps xao pid,ppid',device))
        result_2 = subprocess.run(exec_string_2.split(' '),capture_output=True)
        decoded_pids = result_2.stdout.decode()
        self._process_reports.append(decoded_pids)

    def _monitor_ports(self,device):
       # t = RepeatTimer(0.5,function=self._get_ports,kwargs={"device":device})
       # t.start()
       # self._timers[device] = t
        pass

    def _calc_ports(self,vm_ip_addr):
        self._pre_process_processes()
        actual_tcp_lines = []
        for report in self._port_reports:
            actual_tcp_lines +=  [line for line in report.split('\n') if line.startswith("ESTAB")]
        meta_lines = []
        src_addr = "x.x.x.x"
        non_meta_lines = []
        for tcp_line in actual_tcp_lines:  # ESTAB 0      0           10.0.0.3:33150     10.0.0.4:22   users:(("ssh",pid=3114,fd=3),("sshd",pid=2342,fd=4))
            line_segments = tcp_line.split(':')  #  ['...src_addr','src_port ... dest_addr','dest_port ... users','(("xx",pid=xxxxxx,fd=x))]
            src_port = self._get_port(line_segments[1].split(' ')[0],tcp_line)
            dest_port = self._get_port(line_segments[2].split(' ')[0],tcp_line)
            dest_addr = line_segments[1].split(' ')[-1]
            src_addr = line_segments[0].split(' ')[-1]
            if src_addr == vm_ip_addr:
                if len(line_segments) > 3: # ['(("ssh",','3114,fd=3),("sshd",','2342,fd=4))']
                    pid_segments = line_segments[3].split("pid=")[1:]  # skip the first since no pid in it. 
                    added = False
                    line_pid = "-1"
                    for segment in pid_segments:
                        line_pid = segment.split(",")[0]
                        for dp_pid in self._delayed_processes:
                            if (line_pid in self._processes and str(dp_pid) in self._processes[line_pid]) or str(dp_pid) == line_pid:
                                added=True
                                meta_lines.append(str.format("{0}:{1},{2}:{3},{4},{5},{6}",src_addr,src_port,dest_addr,dest_port,self._delayed_processes[dp_pid]._start_time,self._delayed_processes[dp_pid]._end_time,self._delayed_processes[dp_pid].attack))
                                break
                    if not added:  # no process is parent to this connection
                        procs = []
                        if line_pid in self._processes: # process has been seen so parents are available to show
                            procs = self._processes[line_pid]
                        else:
                            print("pid not recognized")
                            print(line_pid)
                        non_meta_lines.append(str.format("line={0},parents={1},processes={2}",tcp_line,procs,self._process_reports))
                else:
                    print("not included due to no users")
                    print(tcp_line)

        #print("writing to meta file")
        if src_addr  != "x.x.x.x":
            folder_path = get_output_folder()
            filename = os.path.join(folder_path,str.format("DP_{0}_{1}.txt",src_addr,convert_sec_to_milli(time.time())))
            exec_string= str.format('mkdir -p {0}',folder_path)
            result = subprocess.run(exec_string.split(' '),capture_output=True)
            exec_string_2= str.format('sudo chmod ugo+rwx {0}',folder_path)
            result_2 = subprocess.run(exec_string_2.split(' '),capture_output=True)
            if meta_lines == []:
                print(str.format("Empty meta file for {0}",src_addr))
                for line in non_meta_lines:
                    print(line)
            #print(meta_lines)
            with open(filename,"w+") as file:
                for dp_pid in self._delayed_processes:
                    file.write(str.format("{0}:{1},{2}:{3},{4},{5},{6}",src_addr,src_port,dest_addr,dest_port,self._delayed_processes[dp_pid]._start_time,self._delayed_processes[dp_pid]._end_time,self._delayed_processes[dp_pid].attack))
                    
                for line in meta_lines:
                    file.write(line)
                    file.write("\n")
            filename_2 = os.path.join(folder_path,str.format("port_lines_{0}_{1}.txt",src_addr,convert_sec_to_milli(time.time())))
            
            with open(filename_2,"w+") as port_file:
                for line in self._port_reports:
                    port_file.write(line)
        #print(actual_tcp_lines)

    def _pre_process_processes(self):
        for rep in self._process_reports:
            for line in rep.split("\n"):
                stripped_line = line.strip()
                child = stripped_line.split(" ")[0]
                parent = stripped_line.split(" ")[-1]
                if child in self._processes and parent not in self._processes[child]:
                    self._processes[child].append(parent)
                elif child not in self._processes:
                    self._processes[child] = [parent]
        # after each process has added all thier parents and parents parents to children.
        # Needs to be done after since it is not guaranteed that we have found all parents parents when adding the parent to
        # the child the first time.
        for child in self._processes:
            for parent in self._processes[child]:
                if parent in self._processes:
                    for other_parent in self._processes[parent]:
                        if other_parent not in self._processes[child]:
                            self._processes[child].append(other_parent)

    
    def _get_port(self,port_str,full_str=""):
        if port_str in c.PROTOCOL_CONVERSION_MAP:
            return c.PROTOCOL_CONVERSION_MAP[port_str]
        else:  # unspecific port or unsupported port mapping
            try:
                int_port = int(port_str)
                return int_port
            except ValueError as e:
                print(e)
                print(str.format("port str: {0} ;",port_str))
                print(full_str)

                raise Exception(str.format("Unknown port name:",port_str))
        

# traffic generation
    def start_traffic(self,gen_info):
        #input params into target,model,params
        self.start_script(self.traffic_dict,"traffic_scripts",gen_info)

# Attack generation
    def start_attacks(self,gen_info):
        print("starting attacks")
        self.start_script(self.attack_dict,"attack_scripts",gen_info)
    
    def start_script(self,dict,subfolder,gen_info):
        for instance in dict:
            if c.PERPETUAL in instance[c.MODEL]:
                origin_vm = None
                target_vm = None
                params = None
                if c.ORIGIN in instance:
                    origin_vm =  self.get_vm(instance[c.ORIGIN])
                if c.TARGET in instance:
                    target_vm = self.get_vm(instance[c.TARGET])
                if c.PARAMS in instance:
                    params = instance[c.PARAMS]
                if self.should_multi_run(instance,gen_info):
                    self.multi_run(subfolder,instance[c.SCRIPT],origin_vm,target_vm,instance[c.MODEL],params,gen_info,True)
                else:
                    self.run_script(subfolder,instance[c.SCRIPT],origin_vm,target_vm,instance[c.MODEL],params,gen_info,True)
        for instance in dict:
            if not c.PERPETUAL in instance[c.MODEL]:
                origin_vm = None
                target_vm = None
                params = None
                if c.ORIGIN in instance:
                    origin_vm =  self.get_vm(instance[c.ORIGIN])
                if c.TARGET in instance:
                    target_vm = self.get_vm(instance[c.TARGET])
                if c.PARAMS in instance:
                    params = instance[c.PARAMS]
                if self.should_multi_run(instance,gen_info):
                    self.multi_run(subfolder,instance[c.SCRIPT],origin_vm,target_vm,instance[c.MODEL],params,gen_info,False)
                else:
                    self.run_script(subfolder,instance[c.SCRIPT],origin_vm,target_vm,instance[c.MODEL],params,gen_info,False)
        print("starting scripts is completed")
    

    def multi_run(self,subfolder,script_file,origin_vm,target_vm,model,params,gen_info,perpetual):
        print("multi run happening")
        sleep_time = self.frequency_calc(model)
        run_time = convert_to_sec(model[c.DURATION],model[c.DURATION_TYPE])
        max_sec= convert_to_sec(gen_info[c.MAX_DURATION],gen_info[c.DURATION_TYPE])
        if c.AMOUNT in model:
            for i in range(int(model[c.AMOUNT])):
                act_sleep = i * sleep_time
                if act_sleep + run_time < max_sec:
                    self.run_script(subfolder=subfolder,script_file=script_file,origin_vm=origin_vm,target_vm=target_vm,model=model,params=params,gen_info=gen_info,perpetual=perpetual,sleep_time=act_sleep)
                #t = Thread(target=self.run_script,args=[subfolder,script_file,origin_vm,target_vm,model,params,gen_info,perpetual,act_sleep])
                #t.start()  
        else: # frequency less
            for i in range(0,max_sec,sleep_time):
                act_sleep = i 
                self.run_script(subfolder=subfolder,script_file=script_file,origin_vm=origin_vm,target_vm=target_vm,model=model,params=params,gen_info=gen_info,perpetual=perpetual,sleep_time=act_sleep)
                #t = Thread(target=self.run_script,args=[subfolder,script_file,origin_vm,target_vm,model,params,gen_info,perpetual,act_sleep])
                #t.start() 

    def run_script(self,subfolder,script_file,origin_vm,target_vm,model,params,gen_info,perpetual,sleep_time=0):
        script=None
        print(str.format("run_script is called from {0}",subfolder))
        for folder in self.get_shared_folders():
            pos_script = os.path.join(folder,subfolder,script_file)
            if os.path.isfile(pos_script):
                script = pos_script
        if script is None:
            print("ERROR SCRIPT FILE NOT FOUND Make sure shared folder is given and structured correctly or that the script exists in internal folder")
            return
        if origin_vm is None:
            exec_string = self.with_sudo(str.format('ip netns exec VM_NAME {0} {1}',self.python_string,script))
        else:
            exec_string = self.with_sudo(str.format('ip netns exec {0} {1} {2}',self.get_fullname(origin_vm),self.python_string,script))
        if target_vm is not None: 
            exec_string = str.format('{0} --{1} {2}',exec_string,c.TARGET,self.ip_map[target_vm.name][:-3])
        
        duration_val = model[c.DURATION]
        duration_type = model[c.DURATION_TYPE]
        duration = convert_to_sec(duration_val,duration_type)
        exec_string = str.format('{0} --{1} {2}',exec_string,c.DURATION,duration)
        if params is not None:
            for param_dict in params:
                if param_dict[c.VALUE] == "ORIGIN" and origin_vm is not None:
                    exec_string = str.format('{0} --{1} {2}',exec_string,param_dict[c.NAME], self.ip_map[origin_vm.name][:-3])
                elif param_dict[c.VALUE] == "ORIGIN":    
                    exec_string = str.format('{0} --{1} ORIGIN',exec_string,param_dict[c.NAME])
                else:
                    exec_string = str.format('{0} --{1} {2}',exec_string,param_dict[c.NAME], param_dict[c.VALUE])
        atk = False
        if subfolder =="attack_scripts":
            atk = True
        if origin_vm is None:
            for vm_name in self.vms:
                
                actual_exec_string = exec_string.replace("VM_NAME",str.format('{0}',self.get_fullname(self.vms[vm_name])))
                if "ORIGIN" in actual_exec_string:
                    actual_exec_string = actual_exec_string.replace("ORIGIN",self.ip_map[vm_name][:-3])

                t = DelayedProcess(target=os.system,delay=sleep_time,time_info=gen_info,args=[actual_exec_string],log_args = actual_exec_string,attack=atk,manager=self)
                if perpetual:
                    self.threads["perpetual"].append(t)
                else:
                    #self.threads["transient"].append(t)
                    if sleep_time <= 300:
                        self.threads_interval[0].append(t)
                    else:
                        i = 1
                        while i*180 < sleep_time-300:
                            i+=1
                        #print(i)
                        #print(sleep_time)
                        self.threads_interval[i].append(t)
                       
                #t.start()
        else:
            t = DelayedProcess(target=os.system,delay=sleep_time,time_info=gen_info,args=[exec_string],log_args = exec_string,attack=atk,manager=self)
            if perpetual:
                self.threads["perpetual"].append(t)
            else:
                #self.threads["transient"].append(t)
                if sleep_time <= 300:
                    self.threads_interval[0].append(t)
                else:
                    i = 1
                    while i*180 < sleep_time-300:
                        i+=1
                    #print(i)
                    #print(sleep_time)
                    self.threads_interval[i].append(t)
                       
            #t.start()

        print("run script ending")
        return
    

    def start_perpetual_threads(self):
        for thread in self.threads["perpetual"]:
             thread.start()
             
    def start_threads(self):
        t = Thread(target=self.start_perpetual_threads)
        t.start()
        time.sleep(30)
        t2 = Thread(target = self.thread_starter)
        t2.start() 

    def thread_starter(self):
        for index in range(len(self.threads_interval)):
            threads_to_start = self.threads_interval[index]
            for thread in threads_to_start:
                thread.start()
            time.sleep(180)


