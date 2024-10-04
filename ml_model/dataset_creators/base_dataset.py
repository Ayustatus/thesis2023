from datetime import datetime

GOOD = 0
ATTACK = 1

class BaseDataset:
    """
    The Dataset interface/base class. All other dataset classes should inherit from this class.

    """
    def __init__(self,file):
        self.file = file
        self.objects = []
        self.attack_count = 0
        self.normal_count = 0
        self.session_count = 0
        self.full_count = 0
        self.ids = {'port':{0:0},'ip':{0:0},'type_str':{0:0},"packet_size":{0:0}}
        self._outcomes = {"good":GOOD,"attack":ATTACK}

    def set_file(self,new_file):
        """
        Changes the file that the dataset is to be built upon.

        Note that while the file reference is changed the dataset in not 
        reset or parsed so make sure to clear old objects and reparse after using this method.
        :param str new_file The name of the new file that is to be used as basis for the dataset. 
        :return: None
        """
        self.file = new_file

    def get_outcome(self,string_choice):
        """
        Fetches an outcome based on input parameters.

        Fetches the int that represents the outcome given by the parameter sting_choice.
        If no such outcome exists a Exception is raised.
        :param str string_choice The given outcome.
        :return: The int representing the outcome
        :rtype: int
        :raises Exception If input parameter does not exist in the map between string outcomes and int outcomes.
        """
        if string_choice in self._outcomes:
            return self._outcomes[string_choice]
        raise Exception("unknown outcome")
    
    def gold(self):
        """
        Returns the gold value of each object.

        iterates over all objects and extracts the actual outcome. Then it converts that outcome into a int and
        adds it to a list. This list is then returned. Useful for evaluation.
        :return: A array of ints representing the outcomes.
        :rtype: list
        """
        result = []
        for frame in self.objects:
            result.append(self.get_outcome(frame.outcome))
        return result
    
    def parse(self):
        """
        Parses the file that the dataset is to be built on.

        Parses the file that is referenced by self.file and turns it into objects stored in self.objects.
        Should update the counters. Default behaviour is expected to be that each object should be a Frame.
        If default behaviour is not followed other methods will need to be overwritten as well to ensure proper
        handling in those cases. Specifically the gold() method.
        :return: None
        """
        raise Exception("Not Yet Implemented")

    def getIpFeature(self,ip):
        val = self.ids["ip"][0]
        if ip in self.ids["ip"]:
            return self.ids["ip"][ip]
        return val

    def getPortFeature(self,port):
        val = self.ids["port"][0]
        if port in self.ids["port"]:
            return self.ids["port"][port]
        return val

    def getTypeFeature(self,type_str):
        val = self.ids["type_str"][0]
        if type_str in self.ids["type_str"]:
            return self.ids["type_str"][type_str]
        return val

    def getDayFeature(self,start,end):
        dt = datetime.fromtimestamp(int(start)/1000)
        if dt.weekday() > 4: # weekend
            return 24 + dt.time().hour
        return dt.time().hour

    def getPacketFeature(self,packet=None):
        if packet is None:
            return self.ids["packet_size"][0]
        val = self.ids["packet_size"][0]
        if packet[2] in self.ids["packet_size"]:
            return packet[1]*len(self.ids["packet_size"])+self.ids["packet_size"][packet[2]]
        return val
