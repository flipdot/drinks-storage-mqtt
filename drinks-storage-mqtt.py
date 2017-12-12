#!/usr/bin/env python3
import json

import paho.mqtt.client as mqtt
import yaml

config = yaml.load(open("config.yaml", "r"))

MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_METRIC = "sensors/cellar/drinks_scale_measurements_metric"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"
MQTT_TOPIC_ERRORS = "errors"


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)


def on_message(client, userdata, message):
    try:
        msg_content = yaml.load(message.payload)

        scale_config = config["scales"][msg_content["esp_id"]]
        scale_value_kg = (msg_content["scale_value"] - scale_config["tare_raw"]) \
                         / scale_config["kilogram_raw"]

        output_json = {
            "scale_name": scale_config["scale_name"],
            "scale_value_kg": scale_value_kg,
        }
        client.publish(MQTT_TOPIC_METRIC, json.dumps(output_json))

        crates_float = (msg_content["scale_value"] - scale_config["tare_raw"]) \
                       / scale_config["crate_raw"]
        crates_int = round(crates_float)
        diff_kg = (crates_float - crates_int
                   ) * scale_config["crate_raw"] / scale_config["kilogram_raw"]
        if diff_kg > scale_config["tolerance_kg"]:
            error_json = {
                "origin":
                "drinks-storage-mqtt",
                "message":
                "{}: Measurement not in range, difference = {:.2} kg".format(
                    scale_config["scale_name"], diff_kg)
            }
            client.publish(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        else:
            output_json = {
                "scale_name": scale_config["scale_name"],
                "crate_count": crates_int,
            }
            client.publish(MQTT_TOPIC_CRATES, json.dumps(output_json))

    except KeyError as key:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "message": "unknown scale " + str(key),
            "msg_content": msg_content,
        }
        client.publish(MQTT_TOPIC_ERRORS, json.dumps(error_json))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(config["mqtt_host"])
client.loop_forever()
