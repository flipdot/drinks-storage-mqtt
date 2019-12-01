#!/usr/bin/env python3
import json
import logging

logging.basicConfig(level=logging.INFO)

import paho.mqtt.client as mqtt
import yaml

from .config import config, save_config, ScaleConfig
from .scale_calc import handle_scale_value, ERROR_COUNT_NEGATIVE, ERROR_OUT_OF_RANGE

MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"
MQTT_TOPIC_ERRORS = "errors"

client = None


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)


def send_mqtt(topic, message):
    logging.debug(f"Sending MQTT msg: {topic} - {message}")
    client.publish(topic, message)


ERROR_MESSAGES = {
    ERROR_OUT_OF_RANGE: lambda config, res: "{}: Measurement not in range, difference = {:.2} crates".format(
        config.scale_name, res.diff
    ),
    ERROR_COUNT_NEGATIVE: lambda config, res: f"{config.scale_name}: Crate count negative: {res['crate_count_float']}",
}


def on_message(client, userdata, message):
    logging.debug("Received message")
    # Collect variables' values
    try:
        msg_content = yaml.safe_load(message.payload)
        scale_value = msg_content["scale_value"]
        scale_config = config.config.scales[msg_content["esp_id"]]
    except KeyError as key:
        error_json = {
            "origin": "drinks-storage-mqtt",
            "message": "unknown scale / values missing " + str(key),
            "msg_content": msg_content,
        }
        send_mqtt(MQTT_TOPIC_ERRORS, json.dumps(error_json))
        return

    (error_code, result) = handle_scale_value(
        scale_config, scale_value, auto_tare=config.config.auto_tare != None
    )

    if error_code < 0:
        send_mqtt(
            MQTT_TOPIC_ERRORS,
            json.dumps(
                {
                    "origin": "drinks-storage-mqtt",
                    "message": ERROR_MESSAGES[error_code](config, result),
                    "crate_count_float": result["crate_count_float"],
                    "accuracy": result["accuracy"],
                    "diff": result["diff"],
                }
            ),
        )
    else:
        send_mqtt(
            MQTT_TOPIC_CRATES,
            json.dumps(
                {
                    "scale_name": scale_config.scale_name,
                    "crate_count": result["crate_count"],
                    "crate_count_float": result["crate_count_float"],
                    "accuracy": result["accuracy"],
                    "diff": result["diff"],
                }
            ),
        )

    # Rewrite config on auto tare
    if config.config.auto_tare.rewrite_cfg and result["auto_tared"]:
        logging.debug("Autotare changed config, saving...")
        save_config()


def main():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(config.config.mqtt_host)

    logging.info("Started")
    client.loop_forever()
