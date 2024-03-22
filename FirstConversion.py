import pymongo
import pandas as pd
import json

#connection to pyMongo DataBase

client=pymongo.MongoClient("mongodb://localhost:27017")
  
df = pd.read_csv('/home/slavoliu/report.csv',skiprows=[0],usecols=[3,27])

data=df.to_dict(orient="records")

print(data)

db=client["TestCases"]

db.cloudification.insert_many(data)