import yaml
import os

# in here function is responsible for loading a configuration file (in YAML format) and returning its contents as a Python object
def load_config(path="config.yaml"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file {path} not found.")
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config