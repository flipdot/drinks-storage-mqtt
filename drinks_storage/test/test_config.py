from drinks_storage.config import ScaleConfig, config, CONFIG_FILE
import json
import ruamel.yaml
import logging
from ruamel.yaml.compat import StringIO

yaml = ruamel.yaml.YAML()


def test_load_config():
    with open(CONFIG_FILE, "r") as f:
        file_content = f.read()

    stream = StringIO()
    yaml.dump(config.config.to_dict(config.raw_config), stream)

    # saved config equals loaded config
    assert file_content == stream.getvalue()
