import os
import pymongo
import pandas as pd

class DataBase:
    def __init__(self):
        self.csv_path = '/home/slavoliu/report.csv'
        self.name_of_the_table = 'Cloud'
        self.name_of_the_data = 'TestSet'
        self.client = pymongo.MongoClient("mongodb://localhost:27017")
    
    def start_DB(self):
        os.system('sudo systemctl start mongod')

    def stop_DB(self):
        os.system('sudo systemctl stop mongod')

    def add_and_filter_csv(self):
        df = pd.read_csv(self.csv_path, skiprows=[0], usecols=[2, 3, 27])
        data = df.to_dict(orient="records")
        return data

    def enter_data_from_csv_in_db(self):
        data = self.add_and_filter_csv()
        db = self.client[self.name_of_the_table]
        db[self.name_of_the_data].insert_many(data)
        return self.client

    def total_number_of_elements_from_db(self):
        db = self.client[self.name_of_the_table]
        mycollection = db[self.name_of_the_data]
        count = mycollection.count_documents({})
        return count

    def print_total_number_of_elements_from_db(self):
        count = self.total_number_of_elements_from_db()
        print(f'There are {count} documents in this collection')

    def check_collection_exists(self):
        db = self.client[self.name_of_the_table]
        collection_list = db.list_collection_names() 
        return self.name_of_the_data in collection_list
        