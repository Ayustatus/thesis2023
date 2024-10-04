from .base_model import BaseModel

class AllBadModel(BaseModel):
    
    def train(self):
        return # No need to do any training since no matter what it will return attack

    def predict(self,pcap_frames):
        return [self.evaluation_dataset.get_outcome("attack") for i in range(len(pcap_frames))]  # 0 is normal, 1 is attack
    

    