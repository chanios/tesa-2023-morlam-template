# python3.8

import random
import json
import time
import os

from datetime import datetime

from paho.mqtt import client as mqtt_client
from mongodb import db as mongodb


broker = os.environ["BROKER_HOST"]
port = int(os.environ["BROKER_PORT"])
topic = os.environ['TOPIC']
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'

uri = os.environ["MONGODB_URI"]
client = mongodb.connect_db(uri)
db = client.get_database(os.environ["MONGODB_DB"])
water_level_collection = db.get_collection("water-levels")

water_level_collection.create_index(["sensor_id","time"])

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.tls_set(ca_certs='./server-ca.crt')
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        data = json.loads(msg.payload.decode())
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        water_level_collection.insert_one({
            "level": data["level"],
            "sensor_id": data["sensor_id"],
            "time": datetime.fromtimestamp(time.time())
        })
    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()
    

if __name__ == '__main__':
    run()