#!/usr/bin/env python3
import json

import paho.mqtt.client as mqtt
import yaml

CONFIG_FILE = "config.yaml"
MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_METRIC = "sensors/cellar/drinks_scale_measurements_metric"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"
MQTT_TOPIC_ERRORS = "errors"

config = yaml.safe_load(open(CONFIG_FILE, "r"))
cache = {}

try:
    AUTO_TARE = True
    AT_MAX_DIFF_RAW = config["auto_tare"]["max_diff_raw"]
    AT_REWRITE_CFG = config["auto_tare"]["rewrite_cfg"]
except:
    AUTO_TARE = False


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)


def on_message(client, userdata, message):
    # Collect variables' values
    try:
        msg_content = yaml.safe_load(message.payload)
        scale_value = msg_content["scale_value"]
        scale_config = config["scales"][msg_content["esp_id"]]
        scale_name = scale_config["scale_name"]
        scale_crate_raw = scale_config["crate_raw"]
        scale_raw_tared = scale_value - scale_config["tare_raw"]
        scale_kg_raw = scale_config["kilogram_raw"]
        scale_value_kg = scale_raw_tared / scale_kg_raw
        scale_tolerance_kg = scale_config["tolerance_kg"]
    except KeyError as key:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "message": "unknown scale / values missing " + str(key),
            "msg_content": msg_content,
        }
        client.publish(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    # Publish metric data based on config
    output_json = {
        "scale_name": scale_name,
        "scale_value_kg": scale_value_kg,
        "scale_raw_tared": scale_raw_tared,
    }
    client.publish(MQTT_TOPIC_METRIC, json.dumps(output_json))

    # Compute crate count and tolerance
    crates_float = scale_raw_tared / scale_crate_raw
    crates_int = round(crates_float)
    diff_kg = (crates_float - crates_int) * scale_crate_raw / scale_kg_raw
    accuracy = 1 - abs(crates_float - crates_int)

    # Check for negative crate count
    if crates_int < 0:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "scale_name": scale_name,
            "message": f"{scale_name}: Crate count negative: {crates_int}",
        }
        client.publish(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    # Auto tare if enabled and scale value diff to cache within bounds
    if AUTO_TARE:
        # Compute difference to last cached value
        try:
            cache_value = cache[scale_name]["scale_value"]
            scale_diff = scale_value - cache_value
        except:
            cache_value = scale_value
            scale_diff = 0
        # If difference below threshold, retare
        if abs(scale_diff) < AT_MAX_DIFF_RAW:
            # Update cache
            cache[scale_name] = {
                "scale_value": scale_value,
            }
            # Update scale's tare in config
            config["scales"][msg_content["esp_id"]]["tare_raw"] += \
                scale_diff
            # Rewrite config on change
            if AT_REWRITE_CFG and abs(scale_diff) > 0:
                with open(CONFIG_FILE, 'w') as yaml_file:
                    yaml.dump(config, yaml_file, default_flow_style=False)

    # Check for deviation of crate count's ideal values in kg
    if abs(diff_kg) > scale_tolerance_kg:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "crate_probably": crates_float,
            "accuracy": accuracy,
            "message":
            "{}: Measurement not in range, difference = {:.2} kg".format(
                scale_name, diff_kg)
        }
        client.publish(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    # Everything within limits
    output_json = {
        "scale_name": scale_name,
        "crate_count": crates_int,
        "accuracy": accuracy
    }
    client.publish(MQTT_TOPIC_CRATES, json.dumps(output_json))

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(config["mqtt_host"])
    client.loop_forever()
