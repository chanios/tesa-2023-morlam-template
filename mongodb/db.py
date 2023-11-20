
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi



def connect_db(uri):
    # Set the Stable API version when creating a new client
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(e)