from typing import Mapping, MutableMapping, Sequence, Iterable, List, Set, Dict
import yaml

CONFIG_FILE = "config.yaml"


class AutoTareConfig:
    max_diff_raw: int
    rewrite_cfg: bool


class ScaleConfig:
    scale_name: str
    crate_raw: int
    tare_raw: int
    kilogram_raw: int
    tolerance_kg: float


class Config:
    mqtt_host: str
    scales: Mapping[str, ScaleConfig]
    auto_tare: AutoTareConfig

    def __init__(self, raw_dict):
        self.__dict__.update(**raw_dict)


config: Config = None

def reload_config():
    global config
    with open(CONFIG_FILE, "r") as f:
        config = Config(yaml.safe_load(f))

def save_config():
    with open(CONFIG_FILE, 'w') as yaml_file:
        yaml.dump(config, yaml_file, default_flow_style=False)

if config == None:
    reload_config()
