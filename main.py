from typing import Union
from fastapi import FastAPI
from mongodb import db as mongodb
from datetime import datetime,timezone

import os
import pymongo

uri = os.environ["MONGODB_URI"]

app = FastAPI()

client = mongodb.connect_db(uri)
db = client.get_database(os.environ["MONGODB_DB"])
water_level_collection = db.get_collection("water-levels")


@app.get("/")
def read_root():
    return {"Hacked By": "Arka Hacker"}

@app.get("/waters")
def getAllWatersLevels(resolution: int = 5000):
    cursor = water_level_collection.aggregate([
        {
            '$project': {
                'level': 1, 
                'sensor_id': 1, 
                'time': 1, 
                'interval': {
                    '$trunc': {
                        '$divide': [
                            {
                                '$subtract': [
                                    '$time', datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                                ]
                            }, 5000
                        ]
                    }
                }
            }
        }, {
            '$group': {
                '_id': {
                    'sensor_id': '$sensor_id', 
                    'interval': '$interval'
                }, 
                'avgLevel': {
                    '$avg': '$level'
                }, 
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'sensor_id': '$_id.sensor_id', 
                'levels': [
                    {
                        'timestamp': {
                            '$add': [
                                datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc), {
                                    '$multiply': [
                                        '$_id.interval', resolution
                                    ]
                                }
                            ]
                        }, 
                        'level': '$avgLevel'
                    }
                ]
            }
        }, {
            '$group': {
                '_id': '$sensor_id', 
                'levels': {
                    '$push': '$levels'
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'sensor_id': '$_id', 
                'levels': 1
            }
        }, {
            '$sort': {
                'sensor_id': 1
            }
        }
    ])
    result = {}
    for sensor in cursor:
        result[sensor["sensor_id"]] = sensor["levels"]
    return result

@app.get("/waters/latest")
def get():
    latest_waters = water_level_collection.aggregate([
        {
            '$sort': {
                'time': -1
            }
        }, {
            '$group': {
                '_id': '$sensor_id', 
                'latest_level': {
                    '$first': '$level'
                }, 
                'lastest_time': {
                    '$first': '$time'
                }
            }
        }
    ])
    return list(latest_waters)
    
@app.get("/waters/{sensor_id}")
def getLatestWaterLevelBySensorId(sensor_id: int):
    try:
        cursor = water_level_collection.find({
            "sensor_id": sensor_id
        }).sort("time", pymongo.DESCENDING).limit(1)
        record = cursor.next()
        del record["_id"]
        return record
    except StopIteration:
        return {
            "error": "Empty cursor!"
        }