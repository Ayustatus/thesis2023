class TransformerInterface:
    def __init__(self,start=None,end=None,args=None):
        self.start = start
        self.end = end
        self.args = args
    

    def set_time(self,start=None,end=None):
        self.start = start
        self.end = end
    
    def set_start(self,start=None):
        self.set_time(start)
    
    def set_end(self,end=None):
        self.set_time(end=end)


    def transform(self,use_given):
        raise Exception("Not Yet Implemented")