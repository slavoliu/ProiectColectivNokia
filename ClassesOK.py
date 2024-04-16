from pymongo import MongoClient, errors, cursor
import pandas as pd
import os
import re


class DataBase:
    def __init__(self):
        self.csv_path = '/home/slavoliu/report.csv'
        self.table_name = "Cloud"
        self.collection_name = "TestSet"
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client[self.table_name]
        self.collection = self.db[self.collection_name]
        self.data=None
        self.count=None
        self.list_of_TestSet_collection_name=[]
        self.run=False
        

    def start_mongodb_service(self):
        os.system('sudo systemctl start mongod')
        print("Start mongod service")


    def stop_mongodb_service(self):
        os.system('sudo systemctl stop mongod')
        print("Stop mongod service")


    def add_data_to_database(self):
        self.start_mongodb_service()
        df = pd.read_csv(self.csv_path, skiprows=[0], usecols=[2, 3, 27])
        data = df.to_dict(orient="records")

        for document in data:
            query = {
                "Test Set": document["Test Set"],
                "Name": document["Name"],
                "Last Run on UTE Cloud": document["Last Run on UTE Cloud"]
         }

            if self.collection.count_documents(query) == 0:
               self.collection.insert_one(document)


        print(f'inserting data in table {self.table_name}, inside the collection {self.collection_name}')

    def run_checker(self):
        self.run=True
        return self.run
 
    def total_number_of_elements_from_db(self):
        if(self.count==None):
            self.count = self.collection.count_documents({})
            print(f'There are {self.count} documents in this collection')
        else:
            print(f'There are {self.count} documents in this collection')

    def check_collection_exists(self):
        print("Checking if collection exists in database")
        collection_list = self.db.list_collection_names()
        if self.collection_name in collection_list:
            return True
        else:
            return False

    def create_test_set_collections(self):
        if self.run:
            print("TestSet collections are there")
        else:
            unique_test_sets = self.collection.distinct("Test Set")

            for test_set_name in unique_test_sets:
                new_collection_name = f"test_set_{test_set_name}"
                new_collection = self.db[new_collection_name]
                self.list_of_TestSet_collection_name.append(new_collection_name)

                filter_query = {"Test Set": test_set_name}
                matching_documents = self.collection.find(filter_query)

                for doc in matching_documents:
                    new_doc = {"name": doc["Name"], "last_run": doc["Last Run on UTE Cloud"]}
                    new_collection.insert_one(new_doc)
            print("Create collections for each Test Set")
            return self.list_of_TestSet_collection_name


class Processing(DataBase):
    def __init__(self, datab):
        self.datab = datab
        self.count_TestSets = []
        self.count_TrueLastRun = []
        self.cloudification_of_each_TestSet = []
        self.show_cloudification = []
        self.root_folder="/home/slavoliu/test_line_specific"

    def count_TestSet(self):
        for TestSets in self.datab.list_of_TestSet_collection_name:
            try:
                counts=self.datab.db[TestSets].count_documents({})
                self.count_TestSets.append(counts)
            except errors.OperationFailure:
                print(f"\"{TestSets}\" is not a valid collection name.")
                continue
            except Exception as e:
                print(f"An error occured while getting the count of documents in {TestSets}: {e}")
                continue
    
    def count_last_run_true(self):
        for TestSets1 in self.datab.list_of_TestSet_collection_name:
            try:
                counts1=self.datab.db[TestSets1].count_documents({"last_run": True})
                self.count_TrueLastRun.append(counts1)
            except errors.OperationFailure:
                 print(f"\"{TestSets1}\" is not a valid collection name.")
                 continue
            except Exception as e:
                print(f"An error occurred while getting the count of documents in {TestSets1} where 'last_run' is true: {e}")
                continue

    def calculate_cloudification_ratio(self):
        self.count_TestSet()
        self.count_last_run_true()

        for i in range(len(self.count_TestSets)):
            if self.count_TestSets[i] != 0:
                ratio = (self.count_TrueLastRun[i] / self.count_TestSets[i]) * 100
                self.cloudification_of_each_TestSet.append(round(ratio, 2))
            else:
                self.cloudification_of_each_TestSet.append(0)

    from pymongo import MongoClient

    def show_cloudification_of_each_TestSet(self):
        if self.datab.run:
            print("Cloudification was made")
            client = MongoClient('localhost', 27017)


            db = client[self.datab.table_name]


            cloudification = db['cloudification']


            documents = cloudification.find()


            for doc in documents:
                print(f"The {doc['TestSetName']} have a cloudification ratio of {doc['CloudificationRatio']}%")


            client.close()
        else:
            self.calculate_cloudification_ratio()

            client = MongoClient('localhost', 27017)

            db = client[self.datab.table_name]

            cloudification = db['cloudification']

            for i in range(len(self.datab.list_of_TestSet_collection_name)):
                cloudification_ratio_string = f"The {self.datab.list_of_TestSet_collection_name[i]} have a cloudification ratio of {self.cloudification_of_each_TestSet[i]}%"
                self.show_cloudification.append(cloudification_ratio_string)

                cloudification.insert_one({
                    'TestSetName': self.datab.list_of_TestSet_collection_name[i],
                    'CloudificationRatio': self.cloudification_of_each_TestSet[i]
                })

            for j in range(len(self.show_cloudification)):
                print(f'{self.show_cloudification[j]}\n')

            client.close()

        
    def cloudification_false(self):
        if self.datab.run:
            print("Test Cases from clodification false was executed")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            cloudification_false=db['cloudification_false']
            TestSet_collection=db[self.datab.collection_name]
            documents=TestSet_collection.find({"Last Run on UTE Cloud":False})

            for doc in documents:
                cloudification_false.insert_one({
                'Test Set': doc['Test Set'],
                'Name': doc['Name']
            })
            
            client.close()




    def add_path_to_cloudification_false(self):
        client = MongoClient('localhost', 27017)
        db = client[self.datab.table_name]
        cloudification_false = db['cloudification_false']

        documents = cloudification_false.find()

        pattern = re.compile('.*(\d{3}).*')

        for doc in documents:
            test_set = doc['Test Set']
            match = pattern.match(test_set)

            path_of_test_set = 'Nothing' 

            if match:
                test_set_last_three_digits = match.group(1)

                for dirpath, dirnames, filenames in os.walk(self.root_folder):
                    for dirname in dirnames:
                        dirname_match = pattern.match(dirname)

                        if dirname_match and dirname_match.group(1) == test_set_last_three_digits:
                            path_of_test_set = os.path.join(dirpath, dirname)

            cloudification_false.update_one({'_id': doc['_id']}, {'$set': {'Path of Test Set': path_of_test_set}}, upsert=True)

        client.close()




    def find_test_name_in_files(self):
        if self.datab.run:
            print("We found the test names in files")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            cloudification_false = db['cloudification_false']
            found = db['found']
            not_found = db['not_found']

            documents = cloudification_false.find()

            for doc in documents:
                name = doc['Name']
                path_of_test_set = doc['Path of Test Set']
                testset=doc['Test Set']

                if os.path.exists(path_of_test_set):
                    for dirpath, dirnames, filenames in os.walk(path_of_test_set):
                        for filename in filenames:
                            if filename.endswith('.robot'):
                                file_path = os.path.join(dirpath, filename)

                                with open(file_path, 'r') as file:
                                    content = file.read()

                                    if name in content:
                                        found.insert_one({'File Name': filename,'Name': name,'Test Set':testset})
                                    else:
                                        not_found.insert_one({'File Name': filename, 'Name': name,'Test Set':testset})

            client.close()





