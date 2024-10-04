import json



class Frame:
    """
    A Container for a packet.

    Used to uniformly parse each packet into a form any dataset can handle.
    """
    def __init__(self,csv_objs,id_val,dataset):
        self.protocol = csv_objs[4]
        self.session_len = csv_objs[8]
        self.session_flow =None
        self.pck_amount = csv_objs[7]
        self.malicious = csv_objs[9]
        self.id = id_val
        self.packets = json.load(csv_objs[-1])
        self._set_outcome()
        self.origin_ip = csv_objs[0]
        self.origin_port = csv_objs[1]
        self.destination_ip = csv_objs[2]
        self.destination_port = csv_objs[3]
        self.start = csv_objs[5]
        self.end = csv_objs[6]

        if self.origin_ip not in dataset.ids["ip"]:
            dataset.ids["ip"][self.origin_ip] = len(dataset.ids["ip"])
        if self.destination_ip not in dataset.ids["ip"]:
            dataset.ids["ip"][self.destination_ip] = len(dataset.ids["ip"])
        if self.origin_port not in dataset.ids["port"]:
            dataset.ids["port"][self.origin_port] = len(dataset.ids["port"])
        if self.destination_port not in dataset.ids["port"]:
            dataset.ids["port"][self.destination_port] = len(dataset.ids["port"])
        if self.protocol not in dataset.ids["type_str"]:
            dataset.ids["type_str"][self.protocol] = len(dataset.ids["type_str"])
        for packet_tuple in self.packets:
            if packet_tuple[2] not in dataset.ids["packet_size"]:
                dataset.ids["packet_size"][packet_tuple[2]] = len(dataset.ids["packet_size"])
    def _set_outcome(self):
        self.outcome = "attack" if self.malicious else "good"
    

