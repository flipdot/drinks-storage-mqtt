#!/usr/bin/env python3
from flask import Flask
import paho.mqtt.client as mqtt

app = Flask(__name__)

@app.route("/")
def hello():
    return "hello"


def connection(client, userdata, flags, result):
    print("hallo"+str(result))

client = mqtt.Client()
client.on_connect = connection
client.connect("192.168.3.140")

client.loop_forever()

