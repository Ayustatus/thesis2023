from .frame import Frame
from .base_dataset import BaseDataset


class CSVDataset(BaseDataset):
    def __init__(self, file):
        BaseDataset.__init__(self, file)

    def parse(self):
        id_val = 0
        with open(self.file, "r") as file_ptr:
            for line in file_ptr:

                csv_objs = line.split(',')
                frame = Frame(csv_objs, id_val,self)
                self.objects.append(frame)
                if frame.malicious:
                    self.attack_count += 1
                else:
                    self.normal_count += 1
                id_val += 1

        self.full_count = len(self.objects)
