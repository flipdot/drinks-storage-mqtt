#!/usr/bin/env python3
# Plots data collected via
#   mosquitto_sub -h $host -t 'sensors/cellar/drinks_scale_measurements_raw' \
#     >> drinks-storage-$(date -I).log

import json
import yaml

import numpy as np
import matplotlib.pyplot as plt

FILENAME = 'drinks-storage-2017-11-30.log'
CONFIG_FILE = 'config.yaml'

config = yaml.load(open(CONFIG_FILE, 'r'))
scales = config['scales']

data = {}
with open(FILENAME, 'r') as f:
    for line in f:
        tmp = json.loads(line)
        esp_id = tmp['esp_id']
        scale_value = tmp['scale_value']
        if esp_id not in data:
            data[esp_id] = [scale_value]
        else:
            data[esp_id].append(scale_value)

avgs = [np.average(scale_values) for scale_values in data.values()]

i = 0
for esp_id, scale_values in data.items():
    scale_name = scales[esp_id]['scale_name']
    plt.plot(scale_values - avgs[i],
             label=scale_name)
    i += 1

plt.legend()
plt.show()
