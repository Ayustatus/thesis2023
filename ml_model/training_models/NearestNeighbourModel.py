from .base_model import BaseModel
from torch import nn as nn


class NearestNeighbourModel(BaseModel):

    def __init__(self, dataset_val, dataset_train, dataset_eval):
        super().__init__(dataset_val, dataset_train, dataset_eval)


    def train(self, mode=True):
        pass

    def optimize(self):
        pass

    def save(self):
        pass

    @staticmethod
    def load(cls, model):
        raise Exception("Not Yet Implemented")

    def forward(self, features):
        raise Exception("Not yet implemented")

    def predict(self, pcap_objects):
        raise Exception("Not yet implemented")

    def featurize(self, pcap_object):
        raise Exception("Not Yet Implemented")