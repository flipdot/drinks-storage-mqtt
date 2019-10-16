#!/usr/bin/env python3
# Plots data collected via mqtt-capture.py
# Data is structured line by line like this:
# 1512292918 {"esp_id":4823672,"scale_value":8267625,"packets_sent":"7261"}

import json
import yaml

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md

# FILENAME = 'log/sensors/cellar/drinks_scale_measurements_raw_sample_10k'
FILENAME = 'log/sensors/cellar/drinks_scale_measurements_raw'
CONFIG_FILE = 'config.yaml'

config = yaml.load(open(CONFIG_FILE, 'r'))
scales = config['scales']

data = {}
with open(FILENAME, 'r') as f:
    for line in f:
        line_data = line.split(' ')
        line_timestamp = datetime.fromtimestamp(int(line_data[0]))
        plt_timestamp = md.date2num(line_timestamp)
        line_json = ' '.join(line_data[1:])
        tmp = json.loads(line_json)
        esp_id = tmp['esp_id']
        scale_value = tmp['scale_value']
        packets_sent = int(tmp['packets_sent'])
        if esp_id not in data:
            data[esp_id] = {
                'timestamps': [plt_timestamp],
                'scale_values': [scale_value],
                'packets_sent': [packets_sent],
            }
        else:
            data[esp_id]['timestamps'].append(plt_timestamp)
            data[esp_id]['scale_values'].append(scale_value)
            data[esp_id]['packets_sent'].append(packets_sent)

avgs = [np.average(esp_data['scale_values']) for esp_data in data.values()]

plt.subplots_adjust(bottom=0.3)
plt.xticks(rotation=45)
ax = plt.gca()
ax.xaxis_date()
ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))
ax.set_xlabel('date/time')
ax.set_ylabel('raw ADC measurement')

i = 0
for esp_id, esp_data in data.items():
    timestamps = esp_data['timestamps']
    scale_values = esp_data['scale_values']
    try:
        scale_name = scales[esp_id]['scale_name']
    except:
        scale_name = esp_id
    plt.plot(
        timestamps,
        scale_values - avgs[i],
        label=scale_name,
    )
    i += 1

plt.legend()
plt.show()
