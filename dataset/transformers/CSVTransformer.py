import time
import os
import re
import traceback
from dataset.transformers.objects.NoneSession import NoneSession
from dataset.transformers.objects.Session import Session
from gen_utils import convert_sec_to_milli
from dataset.utils import  get_output_folder, get_pcap_files, strip_filename_to_ts
from pcapkit import extract,IP
from .transformer_interface import TransformerInterface

class CSVTransformer(TransformerInterface):
    def __init__(self,start=None,end=None,args=None):
        TransformerInterface.__init__(self,start,end,args)
    
    def transform(self,use_given):
        if use_given:
            sessions = self.parse_meta_file(start_time=self.start,end_time=self.end)
        else:
            sessions = self.parse_meta_file()
        # turn pcap_folders into absoulte path to pcap files (within time period)
        print("Session print here")
        print(sessions)
        pcap_files = get_pcap_files(self.args,self.start,self.end)
        if use_given:
            pass  # split pcap_files into mutiple arrays and create multiple outputs
        ts = int(convert_sec_to_milli(time.time()))
        output_file = os.path.join(get_output_folder(),"csv",str.format("{0}.csv",int(ts)))
        original_output = output_file
        unpack_timer = 0
        for file in pcap_files:
            print(file)
            if use_given:
                output_file = str.format("{0}.{1}.csv",original_output,file.split("\\")[-1])
            start_ts = time.time()
            extraction = extract(fin=file,nofile=True)
            print("extract:",(time.time() -start_ts)*1000)
            # reassembly each packet but if multi packet then all indexes all gathered together
            frame_len = extraction.length
            percent = frame_len/100
            index = 0
            for frame in extraction.frame:
                if index % percent == 0:
                    print(index / percent,"%")
                index+=1
                try:
                    fr_time_str = convert_sec_to_milli(time.time())
                    data = frame.unpack()
                    fr_time_end = convert_sec_to_milli(time.time())
                    fr_time = fr_time_end-fr_time_str
                    unpack_timer += fr_time
                except AttributeError:
                    continue
                frame_ts = int(convert_sec_to_milli(data.time_epoch))
                pck_len = data.cap_len
                protocol_string = data.protocols
            
                src_port = "NaN"
                dest_port = "NaN"
                src_ip = "0.0.0.0"
                dest_ip= "0.0.0.0"
                protocols = protocol_string.lower().split(":")
                if protocols[0] =="ethernet":  #Ethernet:IPv6:IPv6_ICMP
                    src_ip = data.ethernet.src
                    dest_ip = data.ethernet.dst
                    if protocols[1] == "ipv4":
                        src_ip = data.ethernet.ipv4.src 
                        dest_ip = data.ethernet.ipv4.dst
                        if protocols[2] == "tcp":
                            src_port = data.ethernet.ipv4.tcp.srcport
                            dest_port = data.ethernet.ipv4.tcp.dstport
                        elif protocols[2] == "udp":
                            src_port = data.ethernet.ipv4.udp.srcport
                            dest_port = data.ethernet.ipv4.udp.dstport
                    elif protocols[1] == "ipv6":
                        dest_ip = data.ethernet.ipv6.dst
                        src_ip =  data.ethernet.ipv6.src
                        if protocols[2] == "tcp":
                            src_port =  data.ethernet.ipv6.tcp.srcport
                            dest_port =  data.ethernet.ipv6.tcp.dstport
                        elif protocols[2] == "udp":
                            src_port = data.ethernet.ipv6.udp.srcport
                            dest_port = data.ethernet.ipv6.udp.dstport
                if "[" in src_port:
                    src_port = src_port.split("[")[1].split(" ")[0]  # format 'unknown [XXXXX tcp]' so remove everything except digits
                if "[" in dest_port:
                    dest_port = dest_port.split("[")[1].split(" ")[0]

                # Only allow IPv4 addresses currently.
                try:
                    regex_match_src = re.search("([0-9]{1,3}\\.){3}[0-9]{1,3}",str(repr(src_ip)))
                    regex_match_dst = re.search("([0-9]{1,3}\\.){3}[0-9]{1,3}",str(repr(dest_ip)))
                except:
                    print("Regexp error")
                    traceback.print_exc()
                    print(src_ip)
                    print(dest_ip)
                    print(repr(src_ip))
                    print(repr(dest_ip))
                if  regex_match_src is not None and src_ip != "0.0.0.0" and regex_match_dst is not None and dest_ip != "0.0.0.0":

                    session,sessions =self.get_session(format(src_ip),src_port,format(dest_ip),dest_port,frame_ts,sessions) # identify_session   sessions[(src_ip,src_port,dest_ip,dest_port)] #TODO fix protocol...
                    if session is not None:
                        if not isinstance(session, NoneSession) and session.src_ip != format(src_ip) and session.dst_ip != format(src_ip):
                            print("Error normal session attempting to add packet not belonging to session")
                            print(session.src_ip)
                            print(session.dst_ip)
                            print(src_ip)
                        session.add_packet(frame_ts,format(src_ip),pck_len,protocol_string)
            if use_given:
                with open(output_file,"w+") as o_file:   
                    for sess_id in sessions:
                        for time_tuple in sessions[sess_id]:
                            for port_sess_tuple in sessions[sess_id][time_tuple]:
                                sess = port_sess_tuple[1]
                                o_string = str.format("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n",sess.src_ip,sess.src_port,sess.dst_ip,sess.dst_port,sess.protocol,sess.start,sess.end,sess.num_pck,sess.size(),sess.attack,sess.packets)
                                o_file.write(o_string)        
            print("unpack: ",unpack_timer) 
        if not use_given:
            with open(output_file,"w+") as o_file:   
                for sess_id in sessions:
                    for time_tuple in sessions[sess_id]:
                        for port_sess_tuple in sessions[sess_id][time_tuple]:
                            sess = port_sess_tuple[1]
                            o_string = str.format("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n",sess.src_ip,sess.src_port,sess.dst_ip,sess.dst_port,sess.protocol,sess.start,sess.end,sess.num_pck,sess.size(),sess.attack,sess.packets)
                            o_file.write(o_string)
                

    def get_session(self,src_ip,src_port,dest_ip,dest_port,ts,sessions):
    
        dest = str.format("{0}:{1}",dest_ip,dest_port)
        src = str.format("{0}:{1}",src_ip,src_port)
        if (src_ip,dest) in sessions.keys():
            for time_tuple in sessions[(src_ip,dest)]:
                if int(ts) >= int(time_tuple[0]) and int(ts) <= int(time_tuple[1]):
                    for port_sess_tuple in sessions[(src_ip,dest)][time_tuple]:
                        if src_port == port_sess_tuple[0]:
                            return port_sess_tuple[1],sessions          
        
        if (dest_ip,src) in sessions.keys():  # returning part of connection
            for time_tuple in sessions[(dest_ip,src)]:
                if int(ts) >= int(time_tuple[0]) and int(ts) <= int(time_tuple[1]):
                    for port_sess_tuple in sessions[(dest_ip,src)][time_tuple]:
                        if dest_port == port_sess_tuple[0]:
                            return port_sess_tuple[1],sessions
                          
        #if this is reached then either session is unknown or src port is unknown.
        # check if any matching session still has a unknown src port.
        # if so use it,ootherwise its a no session.
        #print("No existing session with port existed for src:",src_ip,":",src_port," and destination",dest,"at time:",ts)
        replace_id_one = None
        replace_id_two = None
        replace_id_three = None
        return_sess = None
        #print(sessions.keys())
        if (src_ip,dest) in sessions.keys():
            #print("ip exist from src")
            for time_tuple in sessions[(src_ip,dest)]:
                #print(time_tuple)
                if int(ts) >= int(time_tuple[0]) and int(ts) <= int(time_tuple[1]):
                    #print("time match in src")
                    for port_sess_tuple in sessions[(src_ip,dest)][time_tuple]:
                        #print(port_sess_tuple)
                        if "SRC_PORT" in port_sess_tuple[0]:
                            #print("found a src port sess with src")
                            replace_id_one = (src_ip,dest)
                            replace_id_two = time_tuple
                            replace_id_three = port_sess_tuple
                            return_sess = port_sess_tuple[1]
                            return_sess.src_port = src_port
                            break         
        if return_sess is None:
            if (dest_ip,src) in sessions.keys():  # returning part of connection
                #print("ip exist from dest")
                for time_tuple in sessions[(dest_ip,src)]:
                    if int(ts) >= int(time_tuple[0]) and int(ts) <= int(time_tuple[1]):
                        #print("time match in dest")
                        for port_sess_tuple in sessions[(dest_ip,src)][time_tuple]:
                            #print(port_sess_tuple)
                            if "SRC_PORT" in port_sess_tuple[0]:
                                
                                #print("found a src port sess with dst")
                                replace_id_one = (dest_ip,src)
                                replace_id_two = time_tuple
                                replace_id_three = port_sess_tuple
                                return_sess = port_sess_tuple[1]
                                return_sess.src_port = src_port
                                break
                            
        if return_sess is not None:
            print("replacing a src port session")
            sessions[replace_id_one][replace_id_two].remove(replace_id_three)
            sessions[replace_id_one][replace_id_two].append((src_port,return_sess))
            return return_sess,sessions
        non_sess = NoneSession(src_ip=src_ip,src_port=src_port,dest_ip=dest_ip,dest_port=dest_port,attack=False,start=str(self.start),end=str(self.end))
        
        if (src_ip,dest) in sessions.keys():
            if (str(self.start),str(self.end)) in sessions[(src_ip,dest)].keys():
                sessions[(src_ip,dest)][(str(self.start),str(self.end))].append((src_port,non_sess))
            else:
                sessions[(src_ip,dest)][(str(self.start),str(self.end))] = [(src_port,non_sess)]
        else:
            sessions[(src_ip,dest)] = {(str(self.start),str(self.end)):[(src_port,non_sess)]}
        return non_sess,sessions
    
    def parse_meta_file(self,specified_file=None,start_time=0,end_time = 0):
        meta_files = []
        if specified_file is None and start_time == 0 and end_time == 0:  # We want the latest meta data file
            ts = convert_sec_to_milli(time.time())
            folder = get_output_folder()
            print(folder)
            files = [f for f in os.listdir(folder) if
                os.path.isfile(os.path.join(folder, f)) and f.endswith(".txt") and f.startswith("metadata")]
            print(files)
            closest_file_ts = -1
            closest_file = None
            for file in files:
                file_ts = strip_filename_to_ts(file)
                if closest_file is None or closest_file_ts < 0 or closest_file_ts > ts-float(file_ts):
                    closest_file_ts = ts-float(file_ts)
                    closest_file = file
            meta_files.append(os.path.join(folder,closest_file))
        elif specified_file is None:  # We have an interval and want all meta files within that interval
            folder = get_output_folder()
            print(folder)
            files = [f for f in os.listdir(folder) if
                os.path.isfile(os.path.join(folder, f)) and f.endswith(".txt") and f.startswith("metadata")]
            print(files)
            for file in files:
                file_ts =  strip_filename_to_ts(file)  # remove the meta_file and .txt so only the ts remains
                if  start_time <= int(file_ts) and int(file_ts) <= end_time:
                    meta_files.append(os.path.join(folder,file))
        else:  # we have a singular specified file
            meta_files.append(specified_file)
        sessions = {}
        for file_name in meta_files:
            with open(file_name,"r") as meta_file:
                for line in meta_file:
                    #"srcIp:srcPort,destIp:destPort,StartTime,EndTime,atk"
                    csv_objs = line.split(',')
                    if csv_objs == ['\n']:
                        continue
                    #print(csv_objs)

                    src_ip,src_port = csv_objs[0].split(':')
                    if src_port == "":
                        src_port = "SRC_PORT"
                        if csv_objs[4] == "True":
                            raise Exception("Attack meta data is lacking src port,will not be reliable")
                    sess_id = (src_ip,csv_objs[1])
                    if sess_id in sessions:
                        if (csv_objs[2],csv_objs[3]) in sessions[sess_id]:
                            appendable = True
                            for port_sess_tuple in sessions[sess_id][(csv_objs[2],csv_objs[3])]:
                                if src_port in port_sess_tuple and src_port != "SRC_PORT":
                                    appendable = False 
                                    print(src_port)
                                    print(sess_id)
                                    
                                    raise Exception("Multiple usage of port simultainously") 
                                
                            if appendable:
                                sessions[sess_id][(csv_objs[2],csv_objs[3])].append((src_port,
                                                                                        Session(src_ip=src_ip,
                                                                                                src_port=src_port,
                                                                                                dest_ip=csv_objs[1].split(":")[0],
                                                                                                dest_port=csv_objs[1].split(":")[1],
                                                                                                attack=csv_objs[4],
                                                                                                start=csv_objs[2],end=csv_objs[3]))) 
                        else:
                            sessions[sess_id][(csv_objs[2],csv_objs[3])] = [(src_port,Session(src_ip=src_ip,
                                                                                                src_port=src_port,
                                                                                                dest_ip=csv_objs[1].split(":")[0],
                                                                                                dest_port=csv_objs[1].split(":")[1],
                                                                                                attack=csv_objs[4],
                                                                                                start=csv_objs[2],end=csv_objs[3]))]
                    else:
                        sessions[sess_id] = {(csv_objs[2],csv_objs[3]):[(src_port,Session(src_ip=src_ip,
                                                                                                src_port=src_port,
                                                                                                dest_ip=csv_objs[1].split(":")[0],
                                                                                                dest_port=csv_objs[1].split(":")[1],
                                                                                                attack=csv_objs[4],
                                                                                                start=csv_objs[2],end=csv_objs[3]))]}
        return sessions
    
    def is_attack(self,src_ip,src_port,dest_ip,dest_port,timestamp,meta_object):
        src = str.format("{0}:{1}",src_ip,src_port)
        dest = str.format("{0}:{1}",dest_ip,dest_port)
        if (src,dest) in meta_object:
            durations = meta_object[(src,dest)]
            for duration in durations:
                if int(timestamp) >= int(duration[0]) and int(timestamp) <= int(duration[1]):
                    return True
        if (dest,src) in meta_object:
            durations = meta_object[(dest,src)]
            for duration in durations:
                if int(timestamp) >= int(duration[0]) and int(timestamp) <= int(duration[1]):
                    return True
        return False


                