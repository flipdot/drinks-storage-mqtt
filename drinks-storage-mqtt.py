#!/usr/bin/env python3
import json
import logging
logging.basicConfig(level=logging.DEBUG)

import paho.mqtt.client as mqtt
import yaml
from config import config, save_config, ScaleConfig


MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_METRIC = "sensors/cellar/drinks_scale_measurements_metric"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"
MQTT_TOPIC_ERRORS = "errors"


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)


def send_mqtt(topic, message):
    logging.debug(f"Sending MQTT msg: {topic} - {message}")
    client.publish(topic, message)


def on_message(client, userdata, message):
    # Collect variables' values
    try:
        msg_content = yaml.safe_load(message.payload)
        scale_value = msg_content["scale_value"]
        scale_config = config.scales[msg_content["esp_id"]]
    except KeyError as key:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "message": "unknown scale / values missing " + str(key),
            "msg_content": msg_content,
        }
        send_mqtt(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    scale_raw_tared = scale_config.raw_tared(scale_value)

    # Publish metric data based on config
    output_json = {
        "scale_name": scale_config.scale_name,
        "scale_value_kg": scale_config.to_kg(scale_value),
        "scale_raw_tared": scale_raw_tared,
    }
    send_mqtt(MQTT_TOPIC_METRIC, json.dumps(output_json))

    crates_float = scale_config.to_crates(scale_value)
    crates_int = round(crates_float)

    diff = crates_float - crates_int
    accuracy = 1 - abs(diff)

    # Check for negative crate count
    if crates_int < 0:
        error_json = {
            "origin":
            "drinks-storage-mqtt",
            "scale_name":
            scale_config.scale_name,
            "message":
            f"{scale_config.scale_name}: Crate count negative: {crates_int}",
        }
        send_mqtt(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    # Check for deviation of crate count's ideal values in kg
    if abs(diff) > scale_config.tolerance:
        error_json = {
            "origin":
            "drinks-storage-mqtt",
            "crate_probably":
            crates_float,
            "accuracy":
            accuracy,
            "message":
            "{}: Measurement not in range, difference = {:.2} crates".format(
                scale_config.scale_name, diff)
        }
        send_mqtt(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    # Auto tare if enabled
    if config.auto_tare != None:
        # Update scale's tare in config
        scale_config.tare_raw -= (scale_config.from_crates(
            round(crates_float)) - scale_config.from_crates(crates_float)) / 2.0

        # Rewrite config on change
        if config.auto_tare.rewrite_cfg:
            save_config()

    # Everything within limits
    output_json = {
        "scale_name": scale_config.scale_name,
        "crate_count": crates_int,
        "accuracy": accuracy
    }
    send_mqtt(MQTT_TOPIC_CRATES, json.dumps(output_json))


if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(config.mqtt_host)
    client.loop_forever()
