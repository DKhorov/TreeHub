from pymongo import MongoClient

def load_db_config(filepath="dataApi.txt"):
    config = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

cfg = load_db_config()
MONGO_URI = cfg["MONGO_URI"]
DB_NAME = cfg["DB_NAME"]
COLLECTION = cfg["COLLECTION"]

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[COLLECTION]

# TreeHub API - Source Code
# This language is Python
# This file is: databasedll.py
# Author: Dmitry Khorov
# GitHub: https://github.com/DKhorov/TreeHub.git
