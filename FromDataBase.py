import pymongo
import pandas as pd

client=pymongo.MongoClient("mongodb://localhost:27017")

db=client["TestCases"]

mycollection=db['cloudification']

count=mycollection.count_documents({})


print(f'There are {count} document in  this collection')

count1 = mycollection.count_documents({'Last Run on UTE Cloud': True})

print(f'There are {count1} document in  this collection')

cloudification=(count1/count)*100

print(f'The cloudification is {cloudification}%')
