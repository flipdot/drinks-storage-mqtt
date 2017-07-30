#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import yaml

config = yaml.load(open("config.yaml", "r"))

def remove_prefix(prefix, text):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text


def on_connect(client, userdata, flags, result):
    client.subscribe("drinks_storage/scale_measurements/#")


def on_message(client, userdata, message):
    try:
        topic = remove_prefix("drinks_storage/scale_measurements/", message.topic)
        tare = config[topic]["tare"]
        crate_weight = config[topic]["crate_weight"]
        raw_value = int(message.payload)
        output_value = round((raw_value - tare) / crate_weight)
        client.publish("drinks_storage/crate_counts/" + topic, str(output_value))
    except KeyError as e:
        print("unknown scale " + str(e))
    

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.3.189")
client.loop_forever()