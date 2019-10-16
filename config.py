from typing import Mapping, MutableMapping, Sequence, Iterable, List, Set, Dict
import yaml
import logging

log = logging.getLogger(__name__)

CONFIG_FILE = "config.yaml"


def verify(raw_dict: dict, field: str, of_type: type = None, required: bool = True):
    if field not in raw_dict.keys():
        if required:
            raise KeyError(f"Config field '{field}' is missing")
        else:
            return None

    if of_type != None:
        try:
            # accept booleans as string
            if of_type == bool:
                return str(raw_dict[field]).lower() in ['true', 'yes', 'ja']

            return of_type(raw_dict[field])
        except ValueError:
            raise ValueError(
                f"Config field '{field}' could not be read as {of_type.__name__}, it is of type {type(raw_dict[field]).__name__}"
            )

    return raw_dict[field]


class AutoTareConfig:
    @staticmethod
    def from_dict(raw_dict):
        return AutoTareConfig(
            max_diff_raw=verify(raw_dict, "max_diff_raw", of_type=int),
            rewrite_cfg=verify(raw_dict, "rewrite_cfg", of_type=bool),
        )

    def __init__(self, max_diff_raw: int, rewrite_cfg: bool):
        self.max_diff_raw = max_diff_raw
        self.rewrite_cfg = rewrite_cfg


class ScaleConfig:
    @staticmethod
    def from_dict(raw_dict):
        return ScaleConfig(
            scale_name= verify(raw_dict, "scale_name", of_type=str),
            crate_raw=verify(raw_dict, "crate_raw", of_type=int),
            tare_raw=verify(raw_dict, "tare_raw", of_type=int),
            kilogram_raw=verify(raw_dict, "kilogram_raw", of_type=int),
            tolerance=verify(raw_dict, "tolerance", of_type=float),
        )

    def __init__(self, scale_name: str, crate_raw: int, tare_raw: int, kilogram_raw: int, tolerance: float):
        self.scale_name = scale_name
        self.crate_raw = crate_raw
        self.tare_raw = tare_raw
        self.kilogram_raw = kilogram_raw
        self.tolerance = tolerance

    def raw_tared(self, raw_value: int):
        return raw_value - self.tare_raw

    def to_kg(self, raw_value: int):
        return self.raw_tared(raw_value) / self.kilogram_raw

    def to_crates(self, raw_value: int):
        return self.raw_tared(raw_value) / self.crate_raw

    def relative_to_crates(self, raw_value: int):
        return raw_value / self.crate_raw

    def from_crates(self, crates: int):
        return crates * self.crate_raw + self.tare_raw

    def calc_crates(self, raw_value: int):
        crates_float = self.to_crates(raw_value)
        crates_int = round(crates_float)

        diff = (crates_float - crates_int)

        if abs(diff) > self.tolerance:
            raise ValueError(f"Crate weight out of tolerance. difference: {diff} crates")

        return crates_int


class Config:
    @staticmethod
    def from_dict(raw_dict):
        return Config(
            mqtt_host =  verify(raw_dict, "mqtt_host", of_type=str),
            scales = dict(
                map(
                    lambda kv: (kv[0], ScaleConfig.from_dict(kv[1])),
                    verify(raw_dict, "scales", of_type=dict).items(),
                )
            ),
            auto_tare =  AutoTareConfig.from_dict(
                verify(raw_dict, "auto_tare", of_type=dict)
            )
        )


    def __init__(self, mqtt_host: str, scales: Mapping[str, ScaleConfig], auto_tare: AutoTareConfig):
        self.mqtt_host = mqtt_host
        self.scales = scales
        self.auto_tare = auto_tare


config: Config = None
raw_config: Config = None


def reload_config():
    global config
    global raw_config
    with open(CONFIG_FILE, "r") as f:
        raw_config = yaml.safe_load(f)
        config = Config.from_dict(raw_config)
        log.debug("Config loaded: %s", vars(config))


def save_config():
    with open(CONFIG_FILE, "w") as yaml_file:

        yaml.dump(config, yaml_file, default_flow_style=False)


if config == None:
    reload_config()
