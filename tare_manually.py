#!/usr/bin/env python3
import asyncio
import json
import math
import threading

import paho.mqtt.client as mqtt
import ruamel.yaml

yaml = ruamel.yaml.YAML()

import warnings
warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)

class AsyncioHelper:
    def __init__(self, loop, client):
        self.loop = loop
        self.client = client
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        #print("Socket opened")

        def cb():
            #print("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        #print("Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        #print("Watching socket for writability.")

        def cb():
            #print("Socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        #print("Stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        #print("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        #print("misc_loop finished")

with open("config.yaml", "r") as fd:
    config = yaml.load(fd)

MQTT_TOPIC_RAW = "sensors/cellar/drinks_scale_measurements_raw"
MQTT_TOPIC_METRIC = "sensors/cellar/drinks_scale_measurements_metric"
MQTT_TOPIC_CRATES = "sensors/cellar/drinks_crate_counts"
MQTT_TOPIC_ERRORS = "errors"


def on_connect(client, userdata, flags, result):
    client.subscribe(MQTT_TOPIC_RAW)

future = None

def on_message(client, userdata, message):
    global future
    fut = future
    future = None
    if fut != None:
        fut.set_result(message)


async def get_value(loop, scale_id):
    while True:
        global future
        my_future = loop.create_future()
        future = my_future
        await my_future
        msg_content = yaml.load(my_future.result().payload)
        if msg_content.get('esp_id') == scale_id:
            print(msg_content)
            return msg_content

async def main(loop):
    print("Please select stack:")
    scale_id = await select_entry(config['scales'], lambda stack: stack['scale_name'])

    stack = config['scales'][scale_id]
    print("selected", stack['scale_name'])

    while True:
        map = {
            'tare': 'Tare (set zero point)',
            'value': 'Set value (put some kisten on it)',
            'save': 'Save new calibration',
            'abort': 'Exit!'
        }
        print("What do you want to do?")
        action = await select_entry(map, lambda k: k)
        if action == 'tare':
            await tare(loop, scale_id, stack)
        elif action == 'value':
            await value(loop, scale_id, stack)
        elif action == 'save':
            with open("config.yaml", "w") as fd:
                yaml.dump(config, fd)
        else:
            return


async def tare(loop, scale_id, stack):
    msg = await get_value(loop, scale_id)
    value = msg['scale_value']
    print("setting tare to", value, "old value:", stack['tare_raw'], "difference:", value - stack['tare_raw'])
    config['scales'][scale_id]['tare_raw'] = value

async def value(loop, scale_id, stack):
    measurements = {}

    while True:
        for key in measurements:
            val = measurements[key]
            print("{key} crates: {sum: 6.0f}, {val: 6.0f} per crate".format(key=key,
                val=val, sum=val*key))

        print("[ 0]: Finish")
        print("[ n]: I have n kisten on the stack")
        n = await read_int(loop)
        if n <= 0:
            value = int(sum(measurements.values()) / len(measurements))
            print("new crate value:", value, "old value:", stack['crate_raw'],
                'difference:', stack['crate_raw'] - value)
            config['scales'][scale_id]['crate_raw'] = int(value)
            return
        else:
            msg = await get_value(loop, scale_id)
            value = msg['scale_value']
            tared = value - stack['tare_raw']
            tared_scaled = tared / n
            measurements[n] = tared_scaled
            print("raw:", value, 'tared:', tared, 'scaled:', tared_scaled)



async def select_entry(map, name_func):
    stack_idxs = []
    for idx, scale_id in enumerate(map):
        stack = map[scale_id]
        stack_idxs.append(scale_id)
        print("[{idx: 2d}] {name}".format(idx=idx + 1, name=name_func(stack)))
    selected = await read_int(loop)
    return stack_idxs[selected - 1]


async def read_int(loop):
    global read_int_future
    read_int_future = loop.create_future()
    t = threading.Thread(target=actual_read)
    t.start()
    await read_int_future
    return read_int_future.result()

def actual_read():
    while True:
        try:
            val = int(input("number please: "))
            read_int_future.set_result(val)
            return
        except:
            pass

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    loop = asyncio.get_event_loop()
    aioh = AsyncioHelper(loop, client)

    client.connect(config["mqtt_host"])
    loop.run_until_complete(main(loop))
    loop.close()


