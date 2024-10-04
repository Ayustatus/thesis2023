import random
from .base_model import BaseModel


class StatisticalModel(BaseModel):
    def __init__(self, dataset_val, dataset_train, dataset_eval):
        BaseModel.__init__(self, dataset_val, dataset_train, dataset_eval)
        self.attack_prob = 0
        self.normal_prob = 0

    def train(self, mode=True):
        self.attack_prob = self.evaluation_dataset.attack_count / self.evaluation_dataset.full_count
        self.normal_prob = self.evaluation_dataset.normal_count / self.evaluation_dataset.full_count
        assert self.normal_prob + self.attack_prob == 1
        return  # No need to do any training since it will return based on how the dataset is divided.

    def predict(self, pcap_frames):
        result = []
        for frame in pcap_frames:
            if random.random() < self.attack_prob:
                result.append(self.evaluation_dataset.get_outcome("attack"))
            else:
                result.append(self.evaluation_dataset.get_outcome("good"))
        return result
