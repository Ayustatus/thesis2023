import os
import argparse
import importlib
import time
from ml_model.dataset_creators import csv_dataset
from ml_model.dataset_creators.empty_dataset import EmptyDataset
from gen_utils import convert_sec_to_milli, get_folder

folder = get_folder(__file__)
def dynamic_import(subfolder,ignored_arr,result_object,name_arr):
    files = [f for f in os.listdir(os.path.join(folder,subfolder)) if
                os.path.isfile(os.path.join(folder, subfolder, f)) and f.endswith(".py") and f not in ignored_arr]
    print(files)
    for file in files:  # dynamically import each manager to allow easy additions of managers
        try:
            name, extension = file.rsplit('.', 1)
            fullname = str.format("{0}.{1}",subfolder,name)
            module = importlib.import_module(fullname,"ml_model")
            print(module)
            result_object[name.lower()] = getattr(module, name)
            name_arr.append(name.lower())
        except Exception as e:
            print(e)
    return result_object,name_arr

training_models = {}
training_names = []
training_models,training_names = dynamic_import("training_models",["__init__.py","base_model.py"],training_models,training_names)


def main(arg_dict):
    
    start_time = convert_sec_to_milli(time.time())
    model_name = arg_dict["model"]
    if arg_dict["predict"]:
        pass # parse data and then use existing model to predict result.
    else:
        dataset_one = EmptyDataset()
        dataset_two = EmptyDataset()
        dataset_three = EmptyDataset()
        #parse_data
        if arg_dict["validation_file"] is not None:
            datset_load_start_1 = convert_sec_to_milli(time.time())
            dataset_one = csv_dataset.CSVDataset(arg_dict["validation_file"])
            dataset_one.parse()
            dataset_load_end_1 = convert_sec_to_milli(time.time())
            print(str.format("validation dataset loading,start,end,elapsed: {0} , {1}, {2}",datset_load_start_1,dataset_load_end_1,dataset_load_end_1-datset_load_start_1))
            print(str.format("validation dataset statistics:atk,full,norm: {0}, {1}, {2}",dataset_one.attack_count,dataset_one.full_count,dataset_one.normal_count))
    
        if arg_dict["training_file"] is not None:
            datset_load_start_2 = convert_sec_to_milli(time.time())
            dataset_two = csv_dataset.CSVDataset(arg_dict["training_file"])
            dataset_two.parse()
            dataset_load_end_2 = convert_sec_to_milli(time.time())
            print(str.format("training dataset loading,start,end,elapsed: {0} , {1}, {2}",datset_load_start_2,dataset_load_end_2,dataset_load_end_2-datset_load_start_2))
            print(str.format("training dataset statistics:atk,full,norm: {0}, {1}, {2}",dataset_two.attack_count,dataset_two.full_count,dataset_two.normal_count))
        
        if arg_dict["eval_file"] is not None:
            datset_load_start_3 = convert_sec_to_milli(time.time())
            dataset_three = csv_dataset.CSVDataset(arg_dict["eval_file"])
            dataset_three.parse()
            dataset_load_end_3 = convert_sec_to_milli(time.time())
            print(str.format("evaluation dataset loading,start,end,elapsed: {0} , {1}, {2}",datset_load_start_3,dataset_load_end_3,dataset_load_end_3-datset_load_start_3))
            print(str.format("evaluation dataset statistics:atk,full,norm: {0}, {1}, {2}",dataset_three.attack_count,dataset_three.full_count,dataset_three.normal_count))
       
        model = training_models[model_name](dataset_one,dataset_two,dataset_three)
        val_start = convert_sec_to_milli(time.time())
        model.optimize()
        val_end = convert_sec_to_milli(time.time())
        print(str.format("validation,start,end,elapsed:{0}, {1}, {2}",val_start,val_end,val_end-val_start))


        train_start = convert_sec_to_milli(time.time())
        model.train()
        trained_time = convert_sec_to_milli(time.time())
        print(str.format("training,start,end,elapsed:{0}, {1}, {2}",train_start,trained_time,trained_time-train_start))


        start_eval = convert_sec_to_milli(time.time())
        report = model.evaluate()
        end_eval = convert_sec_to_milli(time.time())
        print(str.format("eval ,start,end,elapsed:{0}, {1}, {2}",start_eval,end_eval,end_eval-start_eval))

        if not arg_dict["dry_run"]:
            model.save()
        print(report)
        write_file_obj = open("report.txt", "w")
        write_file_obj.write(str(report))
        write_file_obj.close()

        end_time = convert_sec_to_milli(time.time())
        print(str.format("start,end elapsed:{0}, {1}, {2}",start_time,end_time,end_time-start_time))
        print("Program is done")

def start():
    parser = argparse.ArgumentParser("Either trains a model or uses a trained model to predict the outcome of new data.")
    parser.add_argument("-vf","--validation-file",help="first dataset file, used for validation(optimizing hyperparameters)",default=None)
    parser.add_argument("-tf","--training-file",help="second dataset file, used for training",default=None)
    parser.add_argument("-ef","--eval-file",help="third dataset file, used for evaluation",default=None)
    parser.add_argument("-m","--model",help="Which model to use, has to exist in either training_models or output_models",required=True)
    parser.add_argument("-p","--predict",help="If the model should predict based on the data instead of training on it",default=False)
    parser.add_argument("-d","--dry-run",help="True If the model should not be saved when training is complete",default=False)

    args = parser.parse_args()

    arg_dict = vars(args)
    if arg_dict["validation_file"] is None and arg_dict["training_file"] is None and arg_dict["eval_file"] is None:
        print("Error Missing argument. No dataset file argument was used")
        return -1
    main(arg_dict)
    return 0



if __name__ == "__main__":
    code = start()
    print("Return code: ",code)