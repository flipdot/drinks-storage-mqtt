# drink-storage-mqtt

## Installation

Prerequisites (install via your distros package manager):

* python3
* pip

```sh
# Install dependencies
pip3 install --user --requirement requirements.txt

# Either start directly...
./drinks-storage-mqtt.py

# ... or install the service file
sudo install -m644 drinks-storage-mqtt.service /etc/systemd/system/drinks-storage-mqtt.service

# you might need to update the paths in it
sudo $EDITOR /etc/systemd/system/drinks-storage-mqtt.service

# then you can start and enable the service
sudo systemctl start drinks-storage-mqtt
sudo systemctl enable drinks-storage-mqtt
```

## Code style

Please use `yapf` to format the code after editing it.
