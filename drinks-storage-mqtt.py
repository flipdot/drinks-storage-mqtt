#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import yaml

config = yaml.load(open("config.yaml", "r"))

MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)


def on_message(client, userdata, message):
    try:
        msg_content = yaml.load(message.payload)

        scale_config = config["scales"][msg_content["esp_id"]]
        output_value = round((msg_content["scale_value"]
                             - scale_config["tare"])
                             / scale_config["crate_weight"])

        client.subscribe(MQTT_TOPIC_RAW)
        # TODO Spoof ID for each scale to be able to publish to a single topic?
        client.publish("{}/{}".format(MQTT_TOPIC_CRATES,
                                      scale_config["scale_name"]),
                       str(output_value))
    except KeyError as e:
        print("unknown scale " + str(e))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(config["mqtt_host"])
client.loop_forever()
