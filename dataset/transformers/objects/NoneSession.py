from dataset.transformers.objects.Session import Session,PacketDirectionType


class NoneSession(Session):
    def __init__(self,src_ip=None,src_port=None,dest_ip=None,dest_port=None,protocol_string=None,start=None,end=None,attack=None):
        Session.__init__(self,src_ip,src_port,dest_ip,dest_port,protocol_string,start,end,attack)
    
    def add_packet(self,ts,src,pck_len,protocol_sting):
        if self.protocol == None:
            self.protocol = protocol_sting
        self.num_pck += 1
        self._size += pck_len
        direction = self._get_dir(src)
        self.packets.append((ts,direction,pck_len)) # TODO dir not existsant FIX
        #print("adding packet to nonesession")

    def _get_dir(self,source):
        if str(source) == str(self.src_ip):
            return PacketDirectionType.OUT
        if str(source) == str(self.dst_ip):
            return PacketDirectionType.IN
        return 3
        