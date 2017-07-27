#!/usr/bin/env python3
import paho.mqtt.client as mqtt

tara = 9024900


def on_connect(client, userdata, flags, result):
    client.subscribe("drinks_storage/scale_measurements/#")


def on_message(client, userdata, message):
    raw_value = int(message.payload)
    output_value = round((raw_value - tara) / -263600)
    topic = remove_prefix("drinks_storage/scale_measurements/", message.topic)
    client.publish("drinks_storage/crate_counts/" + topic, str(output_value))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.3.140")
client.loop_forever()


def remove_prefix(prefix, text):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text
