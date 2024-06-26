from pymongo import MongoClient, errors, cursor
import pandas as pd
import os
import re
import json


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
        df = pd.read_csv(self.csv_path, skiprows=[0], usecols=[0, 1, 2, 3, 27])
        data = df.to_dict(orient="records")

        for document in data:
            query = {
                "QC_ID_CSV": document["QC ID"],
                "Test_Lab_Path":document["Test Lab Path"],
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
                'QC_ID_CSV': doc['QC ID'],
                "Test_Lab_Path": doc["Test Lab Path"],
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
            print("We already found the test names in files")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            cloudification_false = db['cloudification_false']
            found = db['found']
            not_found = db['not_found']

            # found.create_index([("File Name", 1), ("Name", 1), ("Test Set", 1), ("Path of Test Set", 1)], unique=True)
            # not_found.create_index([("File Name", 1), ("Name", 1), ("Test Set", 1), ("Path of Test Set", 1)], unique=True)

            documents = cloudification_false.find()

            for doc in documents:
                name = doc['Name']
            
                cleared_names= re.sub(r"\[\d+\.\d+\]\[\d+\]|\[\d+\]|\[\d+\.\d+\]|\[\d+\.\d+\] \[\d+\.\d+\]",'',name)
                cleared_names=cleared_names.strip()
                cloudification_false.update_one({'_id': doc['_id']}, {'$set': {'Name' : cleared_names}},upsert=True)
            
                updated_doc = cloudification_false.find_one({'_id': doc['_id']})
                updated_name = updated_doc['Name']  
            
                path_of_test_set = doc['Path of Test Set']
                testset=doc['Test Set']
                qc_id=doc['QC_ID_CSV']
                lab_path=doc['Test_Lab_Path']

                if os.path.exists(path_of_test_set):
                    for dirpath, dirnames, filenames in os.walk(path_of_test_set):
                        for filename in filenames:
                            if filename.endswith('.robot'):
                                file_path = os.path.join(dirpath, filename)

                                with open(file_path, 'r') as file:
                                    content = file.read()
                                
                                    if updated_name in content:
                                        found.update_one({'File Name': filename, 'Name': updated_name, 'Test Set': testset, 'Path of Test Set': path_of_test_set, 'QC_ID_CSV': qc_id, 'Test Lab Path' : lab_path}, {'$setOnInsert': {'File Name': filename, 'Name': updated_name, 'Test Set': testset, 'Path of Test Set': path_of_test_set, 'QC_ID_CSV': qc_id, 'Test Lab Path' : lab_path}}, upsert=True)
                                    else:
                                        not_found.update_one({'File Name': filename, 'Name': updated_name, 'Test Set': testset, 'Path of Test Set': path_of_test_set, 'QC_ID_CSV': qc_id, 'Test Lab Path' : lab_path}, {'$setOnInsert': {'File Name': filename, 'Name': updated_name, 'Test Set': testset, 'Path of Test Set': path_of_test_set,'QC_ID_CSV': qc_id,'Test Lab Path' : lab_path }}, upsert=True)


    def QC_tags_in_files(self):
        if self.datab.run:
            print("We searched the QC tags in files")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            cloudification_false=db['cloudification_false']
            found=db['found']

            documents=cloudification_false.find()
            
            for doc in documents:
                TC_name_cloudification=cloudification_false.find({'Name':doc['Name']})
                for name_cloudification in TC_name_cloudification:
                    TC_name_found=found.find({'Name':doc['Name']})
                    for name_found in TC_name_found:
                        if name_cloudification['Name']==name_found['Name']:
                            print(name_cloudification['Name'])
                            print(name_found['Name'])
                            path_of_test=name_found['Path of Test Set']
                            file_name=name_found['File Name']
                            qc_id_csv=name_found['QC_ID_CSV']
                            file_path=os.path.join(path_of_test,file_name)
                            print(file_path)

                            with open(file_path,'r') as file:
                                lines=file.read()

                            
                            if str(qc_id_csv) in lines:
                                found.update_one({'_id':name_found['_id']},{'$set':{'QC id from file':'True'}})
                            else:
                                found.update_one({'_id':name_found['_id']},{'$set':{'QC id from file':'False'}})

    def QC_files_exists(self):
        if self.datab.run:
            print("We searched the QC file in files")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            found=db['found']

            # condition={'QC id from file':"True"}

            documents=found.find()

            for doc in documents:
                print(doc['Name'])
                path_of_test_set=doc['Path of Test Set']
                file_name=doc['File Name']
                file_name_without_extension=os.path.splitext(file_name)[0]
                ext='.qc'
                full_path=os.path.join(path_of_test_set,file_name_without_extension + ext)
                print(full_path)

                if os.path.isfile(full_path):
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file':"True"}})
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file path':full_path}})
                else:
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file':"False"}})


    def test_lab_path_qc_file(self):
        if self.datab.run:
            print("Test lab path from qc file was verified")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            found=db['found']

            condition={'QC file':"True"}

            documents=found.find(condition)

            for doc in documents:
                qc_file_path=doc['QC file path']
                test_lab_path=doc['Test Lab Path']
                test_lab_path = test_lab_path.replace("\\", "\\\\")
                found.update_one({'_id':doc['_id']},{'$set':{'Test Lab Path':test_lab_path}})
                test_lab_path=doc['Test Lab Path']
                with open(qc_file_path,'r') as f:
                    data=json.load(f)
                pattern=re.compile('SBTS00.*')

                for key in data.keys():
                    if pattern.match(key):
                        if test_lab_path in data[key]:
                            found.update_one({'_id':doc['_id']},{'$set':{'QC file - lab path':"True"}})
                        else:
                            found.update_one({'_id':doc['_id']},{'$set':{'QC file - lab path':"False"}})
                

                

    def test_set_qc_file(self):
        if self.datab.run:
            print("Test test set from qc file was verified")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            found=db['found']

            condition={'QC file':"True"}

            documents=found.find(condition)

            for doc in documents:
                qc_file_path=doc['QC file path']
                test_set=doc['Test Set']
                with open(qc_file_path,'r') as f:
                    content= f.read()

                data=json.dumps(content)

                if test_set in data:
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file - Test Set':"True"}})
                else:
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file - Test Set':"False"}})

    def TC_name_qc_file(self):
        if self.datab.run:
            print("Test name from qc file was verified")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            found=db['found']

            condition={'QC file':"True"}

            documents=found.find(condition)

            for doc in documents:
                qc_file_path=doc['QC file path']
                test_name=doc['Name']
                with open(qc_file_path,'r') as f:
                    content= f.read()

                data=json.dumps(content)
               
                if test_name in data:
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file - TC Name':"True"}})
                else:
                    found.update_one({'_id':doc['_id']},{'$set':{'QC file - TC Name':"False"}})

    def is_TC_tracked_by_QC(self):
        if self.datab.run:
            print("The QC tracking for TC's was verified")
        else:
            client = MongoClient('localhost', 27017)
            db = client[self.datab.table_name]
            found = db['found']
            NotOkQC = db['NotOkQC']
            OkQC = db['OkQC']

            documents = found.find()

            for doc in documents:
                name = doc['Name']
                qc_id = doc['QC_ID_CSV']
                testset = doc['Test Set']
                path = doc['Path of Test Set']

                isQCID = doc['QC id from file']
                isQCFile = doc['QC file']

                data = {'Name': name, 'QC ID': qc_id, 'Test Set': testset, 'Path of Test Set': path, 'QC id from file': isQCID, 'QC file': isQCFile}

                if (str(isQCID) == 'False' or str(isQCFile) == 'False') and str(isQCFile) == 'False':
                    NotOkQC.insert_one(data)
                else:
                    isQCpath = doc['QC file - lab path']
                    isQCtestset = doc['QC file - Test Set']
                    isQCTCname = doc['QC file - TC Name']

                    data.update({'QC file - lab path': isQCpath if str(isQCpath) == 'False' else "True",
                                'QC file - Test Set': isQCtestset if str(isQCtestset) == 'False' else "True",
                                'QC file - TC Name': isQCTCname if str(isQCTCname) == 'False' else "True"})
                    
                    found.update_one({'_id': doc['_id']}, {'$set': data})

                    if 'False' in data.values():
                        NotOkQC.insert_one(data)
                    else:
                        OkQC.insert_one(data)


                    





            








            



