from sklearn.svm import SVC

from .base_model import BaseModel


class SupportVectorMachineModel(BaseModel):

    def __init__(self, dataset_val, dataset_train, dataset_eval,input_kernel='rbf',input_c=1.0,input_gamma='scale'):
        super().__init__(dataset_val, dataset_train, dataset_eval)
        self.model = SVC(kernel=input_kernel, C=input_c, gamma=input_gamma)

    def train(self, mode=True):
        self.model.fit(X_train, y_train)

    def optimize(self):
        pass

    def save(self):
        pass

    @staticmethod
    def load(cls, model):
        raise Exception("Not Yet Implemented")

    def predict(self, flow_objects, dataset):
        predict_vector
        for obj in flow_objects:
            features = self.featurize(obj, dataset).unsqueeze(0)
        self.model.predict(X)
