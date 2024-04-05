from pymongo import MongoClient, errors, cursor
import pandas as pd
import os
import re

class DataBase:
    def __init__(self):
        self.csv_path = '/home/slavoliu/report.csv'
        self.table_name = 'Cloud'
        self.collection_name = 'TestSet'
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client[self.table_name]
        self.collection = self.db[self.collection_name]
        self.data=None
        self.count=None
        self.list_of_new_collection_name=[]

    def my_decorator(func):
        def wrapper():
            print("<-------------------------------------------->")
            func()
            print("<-------------------------------------------->")
        return wrapper
        
    @my_decorator
    def start_mongodb_service(self):
        os.system('sudo systemctl start mongod')
        print("Start mongod service")

    @my_decorator
    def stop_mongodb_service(self):
        os.system('sudo systemctl stop mongod')
        print("Stop mongod service")

    @my_decorator
    def add_data_to_database(self):
        self.start_mongodb_service()
        df = pd.read_csv(self.csv_path, skiprows=[0], usecols=[2, 3, 27])
        self.data = df.to_dict(orient="records")
        data = self.add_and_filter_csv()
        self.collection.insert_many(data)
        print(f'inserting data in table {self.table_name}, inside the collection {self.collection_name}')

    @my_decorator
    def total_number_of_elements_from_db(self):
        self.count = self.collection.count_documents({})
        print(f'There are {self.count} documents in this collection')

    def check_collection_exists(self):
        print("Checking if collection exists in database")
        collection_list = self.db.list_collection_names() 
        if(self.collection_name in collection_list):
            return True
        else:
            return False

    def create_test_set_collections(self):
        if len(self.list_of_new_collection_name) != 0:
            return self.list_of_new_collection_name
            print("Create collections for each Test Set")
        else:
            unique_test_sets = self.collection.distinct("Test Set")

            for test_set_name in unique_test_sets:
                new_collection_name = f"test_set_{test_set_name}"
                new_collection = self.db[new_collection_name]
                self.list_of_new_collection_name.append(new_collection_name)

                filter_query = {"Test Set": test_set_name}
                matching_documents = self.collection.find(filter_query)

                for doc in matching_documents:
                    new_doc = {"name": doc["Name"], "last_run": doc["Last Run on UTE Cloud"]}
                    new_collection.insert_one(new_doc)
        print("Create collections for each Test Set")
        return self.list_of_new_collection_name

    
    
    def get_name_counts(self):
        name_counts = []

        list_of_new_collection_name = self.create_test_set_collections()

        for new_collection_name in list_of_new_collection_name:
            try:
                count = self.db[new_collection_name].count_documents({})
                name_counts.append(count)
            except errors.OperationFailure:
                print(f"\"{new_collection_name}\" is not a valid collection name.")
                continue
            except Exception as e:
                print(f"An error occurred while getting the count of documents in {new_collection_name}: {e}")
                continue

        return name_counts

    def get_true_last_run_counts(self):
        true_last_run_counts = []

        list_of_new_collection_name = self.create_test_set_collections()

        for new_collection_name in list_of_new_collection_name:
            try:
                count = self.db[new_collection_name].count_documents({"last_run": True})
                true_last_run_counts.append(count)
            except errors.OperationFailure:
                print(f"\"{new_collection_name}\" is not a valid collection name.")
                continue
            except Exception as e:
                print(f"An error occurred while getting the count of documents in {new_collection_name} where 'last_run' is true: {e}")
                continue

        return true_last_run_counts

    def calculate_cloudification_ratios(self):
        name_counts = self.get_name_counts()
        true_last_run_counts = self.get_true_last_run_counts()

        cloudification_ratios = []

        for i in range(len(name_counts)):
            if name_counts[i] != 0:
                ratio = (true_last_run_counts[i] / name_counts[i]) * 100
                cloudification_ratios.append(round(ratio, 2))
            else:
                cloudification_ratios.append(0)

        return cloudification_ratios

    def print_cloudification_ratios(self):
        list_of_new_collection_name = self.create_test_set_collections()
        cloudification_ratios = self.calculate_cloudification_ratios()

        cloudification_ratio_strings = []

        for i in range(len(list_of_new_collection_name)):
            cloudification_ratio_string = f"The {list_of_new_collection_name[i]} have a cloudification ratio of {cloudification_ratios[i]}%"
            cloudification_ratio_strings.append(cloudification_ratio_string)

        for j in range(len(cloudification_ratio_strings)):
            print(f'{cloudification_ratio_strings[j]}\n')
#-------------------------------------------------------------------------------------------------------------------------
    def get_false_last_run_names(self):
        false_last_run_names = {}

        list_of_new_collection_name = self.create_test_set_collections()

        for new_collection_name in list_of_new_collection_name:
            try:
                false_last_run_names[new_collection_name] = []
                
                cursor = self.db[new_collection_name].find({"last_run": False})
                
                documents = list(cursor)
                
                if documents:
                    for doc in documents:
                        false_last_run_names[new_collection_name].append(doc["name"])
            except Exception as e:
                print(f"An error occurred while processing {new_collection_name}: {e}")

        return false_last_run_names
    
    def print_false_last_run_names(self):
        false_last_run_names = self.get_false_last_run_names()

        for collection_name, names in false_last_run_names.items():
            if names:
                dir_path='/home/slavoliu/test_line_specific'
                found=[]
                notfound=[]
                pattern=re.compile(rf'{names}')

                for root,dirs,files in os.walk(dir_path):
                    for file in files:
                        if file.endswith('.robot'):
                            with open(os.path.join(root,file),'r') as f:
                                content=f.read()
                                if pattern.search(content):
                                    found.append(file)
                                else:
                                    notfound.append(file)
                print(f'Fisiere in care a fost gasit {names}:',found)
                print('\n')
                print(f'Fisiere in care nu a fost gasit {names}:',notfound)
                print('\n')



