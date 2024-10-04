from .base_model import BaseModel, DATASET_TYPES
from torch import nn as nn, optim
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import torch
#https://tinman.cs.gsu.edu/~bhashithe/CRNN_traffic_classifier.pdf


class NeuralNetworkModel(BaseModel):

    def __init__(self, dataset_val, dataset_train, dataset_eval,in_c=32,out_c=4,kernel_size=2,stride=1,padding=1):
        super(NeuralNetworkModel, self).__init__(dataset_val, dataset_train, dataset_eval)

        self.conv_layer = nn.Conv2d(in_channels=in_c, out_channels=out_c, kernel_size=kernel_size, stride=stride, padding=padding)

        self.batchnorm_layer = nn.BatchNorm2d(4)

        self.lstm_layer = nn.LSTM(input_size=4, hidden_size=100, batch_first=True)

        self.dropout1 = nn.Dropout(0.2)

        self.linear1 = nn.Linear(100, 100)
        self.dropout2 = nn.Dropout(0.4)
        self.linear2 = nn.Linear(100, 2)
        self.softmax = nn.Softmax(dim=1)

    def training(self, mode=True, num_epochs=80, learning_rate=0.02):
        criterion = nn.CrossEntropyLoss()

        # Define the optimizer
        optimizer = optim.Adam(self.parameters(), lr=learning_rate)

        for epoch in range(num_epochs):
            # Set the model to training mode
            self.train()

            running_loss = 0.0
            correct = 0
            total = 0

            for inputs, labels in self.batchify(DATASET_TYPES.TRAINING):
                # Zero the parameter gradients
                optimizer.zero_grad()

                # Convert input and labels to torch tensors
                inputs = inputs.float()
                labels = labels.long()

                # Forward pass
                outputs = self.forward(inputs)

                # Calculate loss
                loss = criterion(outputs, labels)

                # Backward pass and optimize
                loss.backward()
                optimizer.step()

                # Statistics
                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

            train_loss = running_loss / total
            train_accuracy = correct / total

    def optimize(self):
        pass

    def save(self):
        pass

    @staticmethod
    def load(cls, model):
        raise Exception("Not Yet Implemented")

    def evaluate(self):
        # Set the model to evaluation mode
        self.eval()

        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        y_true = []
        y_pred = []

        with torch.no_grad():
            for inputs, labels in self.batchify(DATASET_TYPES.EVALUATION):
                # Convert input and labels to torch tensors

                # Forward pass
                outputs = self.forward(inputs)

                # Calculate loss
                loss = F.cross_entropy(outputs, labels)

                # Total loss
                total_loss += loss.item() * inputs.size(0)

                # Get the predicted class labels
                _, predicted = torch.max(outputs, 1)

                # Total correct predictions
                total_correct += (predicted == labels).sum().item()

                # Total samples
                total_samples += inputs.size(0)

                # Collecting true and predicted labels for metrics
                y_true.extend(labels.tolist())
                y_pred.extend(predicted.tolist())

        # Calculate average loss and accuracy
        avg_loss = total_loss / total_samples
        accuracy = total_correct / total_samples

        # Calculate additional metrics
        precision = precision_score(y_true, y_pred, average='macro')
        recall = recall_score(y_true, y_pred, average='macro')
        f1 = f1_score(y_true, y_pred, average='macro')

        return avg_loss, accuracy, precision, recall, f1

    def forward(self, features):
        features = self.conv_layer(features)

        features = self.batchnorm_layer(features)

        features = features.view(features.size(0), features.size(1), -1)  # Reshape for LSTM input

        lstm_out, _ = self.lstm_layer(features)

        features = self.dropout1(lstm_out)

        features = features[:, -1, :]  # Taking the output of the last LSTM step

        features = self.linear1(features)
        features = self.dropout2(features)
        features = self.linear2(features)
        features = self.softmax(features)
        return features

    def predict(self, flow_objects,dataset):
        predictions = []
        for obj in flow_objects:
            features = self.featurize(obj,dataset).unsqueeze(0)
            with torch.no_grad():
                result = self.forward(features)
                #chosen_index = torch.argmax(result)
                _, predicted = torch.max(result, 1)
                predictions.append(predicted)
        return predictions



