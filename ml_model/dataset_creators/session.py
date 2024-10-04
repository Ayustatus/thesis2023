class Session:
    def __init__(self,identity):
        self.start = None
        self.end = None
        self.length = 0
        self._flow = []
        self.flow=None
        self.id = identity


    def update(packet):
        if self.start == None:
            self.start = None # packet,start
        self.end = None # TODO packet.end

        self.length = self.end-self.start
        self._flow.append((packet.size,packet.timestamp))