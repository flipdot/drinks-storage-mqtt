#!/usr/bin/env python3
import json
import unittest
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime

from config import ScaleConfig, config

with open('test_values.csv', newline='') as csvfile:
    test_data = list(csv.reader(csvfile, delimiter=',', quotechar='"'))
    times = list(map(lambda row: datetime.fromisoformat(row[1]), test_data))
    values = list(map(lambda row: float(row[2]), test_data))

scale_config = ScaleConfig(
    scale_name='mio_mate',
    tare_raw=7820000,
    crate_raw=-276490,
    kilogram_raw=-24400,
    tolerance=0.04,
)

fig, (ax1, ax2) = plt.subplots(2, 1)

fig2, (ax3) = plt.subplots(1, 1)

ax1.set_title('Raw')
ax1.plot(times, values, marker='.')
ax1.set_yticks(np.arange(6000000, 7000000, 50000))

ax2.set_title('Weight')
ax2.plot(times,
         list(map(lambda val: scale_config.to_kg(val), values)),
         marker='.')


def mapCalcCrates(scale_value):
    crates_float = scale_config.to_crates(scale_value)

    try:
        crates = scale_config.calc_crates(scale_value)
    except:
        crates = None

    # Auto tare if enabled
    if crates != None and config.auto_tare != None:
        scale_config.tare_raw -= (
            scale_config.from_crates(round(crates_float)) -
            scale_config.from_crates(crates_float)) / 2.0

    return (crates_float, crates)


ax3.set_title('Crates')

vals = list(map(mapCalcCrates, values))

ax3.plot(times, list(map(lambda val: val[0], vals)), marker='.', label="Raw")
ax3.plot(times, list(map(lambda val: val[1], vals)), marker='.', label="Smart")
ax3.fill_between(times,
                 list(map(lambda val: round(val[0]) + scale_config.tolerance, vals)),
                 list(map(lambda val: round(val[0]) - scale_config.tolerance, vals)),
                 color='g',
                 alpha=0.2)
ax3.legend()

fig.tight_layout()

fig2.tight_layout()
fig2.savefig('figure_name.svg')
plt.show()
