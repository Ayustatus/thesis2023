import enum
from ml_model.dataset_creators.empty_dataset import EmptyDataset
from torch import nn as nn
from sklearn.metrics import classification_report
import torch

class DATASET_TYPES(enum):
    VALIDATION: 1
    TRAINING: 2
    EVALUATION: 3


class BaseModel(nn.Module):
    def __init__(self,dataset_val,dataset_train,dataset_eval):
        super().__init__()
        self.model = None
        self.layers = None
        self.pipeline = None
        self.validation_dataset = dataset_val
        self.training_dataset = dataset_train
        self.evaluation_dataset = dataset_eval

    def optimize(self):
        pass

    def train(self, mode=True):
        raise Exception("Not yet implemented")
    
    def featurize(self, flow_object,dataset):
        raise Exception("Not Yet Implemented")
    
    def eval2(self):
        if self.validation_dataset is not None:
            return classification_report(self.evaluation_dataset.gold(), self.predict_all(self.evaluation_dataset.objects,self.evaluation_dataset))
        return "No evauation dataset to evaluate"

    def evaluate(self):
        raise Exception("Not Yet Implemented")

    def save(self):
        # Extract the embedding vectors as a NumPy array
        # embeddings = self.model.w.weight.detach().numpy()

        raise Exception("Not Yet Implemented")

    @staticmethod
    def load(cls,model):
        raise Exception("Not Yet Implemented")
        
    def forward(self,features):
        raise Exception("Not yet implemented")
    
    def predict(self,pcap_objects,dataset):
        raise Exception("Not yet implemented")
    
    def get_session_count(self,dataset_choice):
        return self._get_dataset(dataset_choice).session_count
    
    def get_session(self,id,dataset_choice):
        raise Exception("Not yet implemented")
    
    def get_attack_count(self,dataset_choice):
        return self._get_dataset(dataset_choice).attack_count
    
    def get_normal_count(self,dataset_choice):
        return self._get_dataset(dataset_choice).normal_count
    
    def get_session_statistics(self,dataset_choice):
        raise Exception("Not yet implemented")
    
    def get_attack_statistics(self,dataset_choice):
        raise Exception("Not yet implemented")
    
    def get_normal_statistics(self,dataset_choice):
        raise Exception("Not yet implemented")
    
    def get_set_count(self,dataset_choice):
        return self._get_dataset(dataset_choice).full_count
    
    def get_set_statistics(self,dataset_choice):
        raise Exception("Not yet implemented")

    def featurize(self, flow_object,dataset):

        src_ip_feature = dataset.getIPFeature(flow_object.origin_ip)
        dest_ip_feature = dataset.getIPFeature(flow_object.destination_ip)
        src_port_feature = dataset.getPortFeature(flow_object.origin_port)
        dest_port_feature = dataset.getPortFeature(flow_object.destination_port)
        type_feature = dataset.getTypeFeature(flow_object.protocol)
        time_of_day_feature = dataset.getDayFeature(flow_object.start,flow_object.end)
        features = [src_ip_feature,dest_ip_feature,src_port_feature,dest_port_feature,type_feature,time_of_day_feature]
        counter = 0
        for packet in flow_object.packets:
            pck_feature = dataset.getPacketFeature(packet)
            features.append(pck_feature)
            counter += 1
            if counter >= 20:
                break
        if len(features) < 26:
            for i in range(26-len(features)):
                features.append(dataset.getPacketFeature())
        return torch.tensor(features)

    def batchify(self, data_type,batch_size=100):
        dataset = self._get_dataset(data_type)
        batch = torch.tensor([[]])
        gold_batch = torch.tensor([])
        for obj in dataset.objects:
            example = self.featurize(obj,dataset)
            if batch.shape == torch.Size([1, 0]):
                batch = example
            else:
                batch = torch.cat((batch, example), dim=0)
            if gold_batch.shape == torch.Size([0]):
                gold_batch = torch.tensor([dataset.get_outcome(obj.outcome)])
            else:
                gold_batch = torch.cat((gold_batch, torch.tensor([dataset.get_outcome(obj.outcome)])), dim=0)
            if len(batch) >= batch_size:
                yield batch[:batch_size], gold_batch[:batch_size]
                batch = batch[batch_size:]
                gold_batch = gold_batch[batch_size:]
        if len(batch) > 0:
            yield batch, gold_batch
    
    def _get_dataset(self,VAL_TYPE):
        if VAL_TYPE == DATASET_TYPES.EVALUATION:
            return self.evaluation_dataset
        if VAL_TYPE == DATASET_TYPES.VALIDATION:
            return self.validation_dataset
        if VAL_TYPE == DATASET_TYPES.TRAINING:
            return self.training_dataset
        raise Exception("Unkown dataset type please use the DATASET_TYPES enum.")
    