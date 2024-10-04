from .frame import Frame
from .base_dataset import BaseDataset
class EmptyDataset(BaseDataset):
    def __init__(self):
        BaseDataset.__init__(self,None)
    
    def parse(self):
        pass