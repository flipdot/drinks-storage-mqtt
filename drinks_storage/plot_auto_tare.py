#!/usr/bin/env python3
import json
import unittest
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime

from .scale_calc import handle_scale_value
from .config import ScaleConfig


# Calculate stuff

with open('test_values.csv', newline='') as csvfile:
    test_data = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
    times = list(map(lambda row: datetime.fromisoformat(row[1]), test_data))
    values = list(map(lambda row: float(row[2]), test_data))

scale_config = ScaleConfig(
    scale_name='mio_mate',
    tare_raw=7820000,
    crate_raw=-276490,
    tolerance=0.04,
)

def mapCalcCrates(scale_value):
    (error_code, result) = handle_scale_value(scale_config, scale_value, auto_tare=True)
    return (None if error_code > 0 else result['crate_count_float'], result['crate_count'])

vals = list(map(mapCalcCrates, values))


# Plot stuff

fig, (ax1) = plt.subplots(1, 1)
ax1.set_title('Raw')
ax1.plot(times, values, marker='.')
ax1.set_yticks(np.arange(6000000, 7000000, 50000))

fig2, (ax2) = plt.subplots(1, 1)
ax2.set_title('Crates')
ax2.plot(times, list(map(lambda val: val[0], vals)), marker='.', label="Raw")
ax2.plot(times, list(map(lambda val: val[1], vals)), marker='.', label="Smart")
ax2.fill_between(times,
                 list(map(lambda val: round(val[0]) + scale_config.tolerance, vals)),
                 list(map(lambda val: round(val[0]) - scale_config.tolerance, vals)),
                 color='g',
                 alpha=0.2)
ax2.legend()

fig.tight_layout()
fig2.tight_layout()
plt.show()
