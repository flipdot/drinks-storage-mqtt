from typing import Mapping, MutableMapping, Sequence, Iterable, List, Set, Dict
import ruamel.yaml
import logging
import tempfile
import os

yaml = ruamel.yaml.YAML()
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
                return str(raw_dict[field]).lower() in ["true", "yes", "ja"]

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

    def to_dict(self, raw_dict):
        raw_dict["max_diff_raw"] = self.max_diff_raw
        raw_dict["rewrite_cfg"] = self.rewrite_cfg
        return raw_dict

    def __init__(self, max_diff_raw: int, rewrite_cfg: bool):
        self.max_diff_raw = max_diff_raw
        self.rewrite_cfg = rewrite_cfg


class ScaleConfig:
    @staticmethod
    def from_dict(raw_dict):
        return ScaleConfig(
            scale_name=verify(raw_dict, "scale_name", of_type=str),
            crate_raw=verify(raw_dict, "crate_raw", of_type=int),
            tare_raw=verify(raw_dict, "tare_raw", of_type=int),
            tolerance=verify(raw_dict, "tolerance", of_type=float),
        )

    def to_dict(self, raw_dict):
        raw_dict["scale_name"] = self.scale_name
        raw_dict["crate_raw"] = self.crate_raw
        raw_dict["tare_raw"] = self.tare_raw
        raw_dict["tolerance"] = self.tolerance
        return raw_dict

    def __init__(
        self, scale_name: str, crate_raw: int, tare_raw: int, tolerance: float
    ):
        self.scale_name = scale_name
        self.crate_raw = crate_raw
        self.tare_raw = tare_raw
        self.tolerance = tolerance


class Config:
    @staticmethod
    def from_dict(raw_dict):
        return Config(
            mqtt_host=verify(raw_dict, "mqtt_host", of_type=str),
            scales=dict(
                map(
                    lambda kv: (kv[0], ScaleConfig.from_dict(kv[1])),
                    verify(raw_dict, "scales", of_type=dict).items(),
                )
            ),
            auto_tare=AutoTareConfig.from_dict(
                verify(raw_dict, "auto_tare", of_type=dict)
            ),
        )

    def to_dict(self, raw_dict):
        raw_dict["mqtt_host"] = self.mqtt_host
        raw_dict["scales"] = dict(
            map(
                lambda kv: (kv[0], kv[1].to_dict(raw_dict["scales"][kv[0]])),
                self.scales.items(),
            )
        )
        raw_dict["auto_tare"] = self.auto_tare.to_dict(raw_dict["auto_tare"])
        return raw_dict

    def __init__(
        self,
        mqtt_host: str,
        scales: Mapping[str, ScaleConfig],
        auto_tare: AutoTareConfig,
    ):
        self.mqtt_host = mqtt_host
        self.scales = scales
        self.auto_tare = auto_tare


class YamlConfig:
    config: Config

    def __init__(self, raw_config, config):
        self.raw_config = raw_config
        self.config = config

    @staticmethod
    def load(path):
        with open(path, "r") as f:
            raw_config = yaml.load(f)
            config = Config.from_dict(raw_config)
            return YamlConfig(raw_config=raw_config, config=config)

    def save(self, path):
        """
        Save config to file in atomic maner.
        """

        (tmp_fd, tmp_path) = tempfile.mkstemp()
        with open(tmp_fd, "w") as tmp_file:
            yaml.dump(self.config.to_dict(self.raw_config), tmp_file)

        os.rename(tmp_file, path)
        os.remove(tmp_path)

config: YamlConfig = None


def reload_config():
    global config
    config = YamlConfig.load(CONFIG_FILE)


def save_config():
    config.save(CONFIG_FILE)


if config == None:
    reload_config()
