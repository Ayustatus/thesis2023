from enum import Enum


class PacketDirectionType(Enum):
    OUT = 0
    IN = 1

class Session:
    def __init__(self,src_ip=None,src_port=None,dest_ip=None,dest_port=None,protocol_string=None,start=None,end=None,attack=None):
        if isinstance(attack,bool):
            if not attack:
                self.attack = "False"
            else:
                self.attack = "True"
        else:
            self.attack = str.strip(attack,"\n ")
        self.packets = [] # [(frame_ts,frame_dir,frame_len)]
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_port = dest_port
        self.dst_ip = dest_ip
        self.protocol = protocol_string
        self.start = start
        self.end = end
        self.num_pck = 0
        self._size = 0

    #def __repr__(self):
    #    return str.format("\{src_ip:{0},src_port:{1},dst_ip:{2},dst_port:{3},protocol:{4},start:{5},end:{6},num_pck:{7},size:{8},attack:{9},packets:[]")
    
    def add_packet(self,ts,src,pck_len,protocol_sting):
        if self.protocol == None:
            self.protocol = protocol_sting
        direction = self._get_dir(src)
        self.packets.append((ts,direction,pck_len))
        self.num_pck += 1
        self._size += pck_len


    def _get_dir(self,source):
        if str(source) == str(self.src_ip):
            return PacketDirectionType.OUT
        if str(source) == str(self.dst_ip):
            return PacketDirectionType.IN
        print(source)
        print(self.src_ip)
        print(self.dst_ip)
        print(source == self.src_ip)
        print(source == self.dst_ip)
        print(repr(source))
        print(repr(self.src_ip))
        print(repr(self.dst_ip))
        print(self.__class__)
        raise Exception("Packet do not belong to session")
    
    def size(self):
        return self._size