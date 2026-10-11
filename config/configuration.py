import json
import os
from functools import lru_cache
import yaml


@lru_cache(maxsize=None)
def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'properties.yml'), 'r') as file:
        configs_dict = yaml.safe_load(file)
    return configs_dict


def flatten_config(configs_dict, parent_key='', sep='.'):
    items = []
    for k, v in configs_dict.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


configs = flatten_config(load_config())
print(f'Loaded configurations are {json.dumps(configs, indent=4)}')

