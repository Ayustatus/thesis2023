from .session import Session
from .frame import Frame
class PCAPParser:   

    def __init__(self,file=None):
        self.file=file

    def parse(self,pcap_file=None,attack_config=None):
        # open file 
        if pcap_file == None and self.file == None:
            print("Error no file given to parse")
            return -1
        
        capture = None # capture of file
        sessions = {}
        dataset = []
        for packet in capture:
            session = self.get_session(packet,sessions)
            session.update(packet)
            dataitem = Frame()
            #set parameters of item
            dataset.append(dataitem)
        for dataitem in dataset:
            dataitem.session_len = sessions[dataitem.session].length
            dataitem.session_flow = sessions[dataitem.session].flow
        return dataset
    
    def get_session(self,packet,sessions):
        src_port = None # TODO
        dest_port = None
        src_ip = None
        dest_ip = None
        protocol = None
        session = (src_port,dest_port,src_ip,dest_ip,protocol)
        if session in sessions:
            return sessions[session]
        new_session = Session(session)
        sessions[session] = new_session
        return new_session

