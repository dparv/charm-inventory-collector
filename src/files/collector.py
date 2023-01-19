#!/usr/local/sbin/charm-env python3
import json
import yaml
import os
import requests
import datetime

from juju import jasyncio
from juju.model import Model, Controller

CONFIG_FILE = "/var/lib/inventory-collector/collector.yaml"
FILES = ['hostname', 'apt', 'snap', 'kernel']

def collect():
    config = read_config()
    targets = config['targets']
    output_dir = config['settings']['collection_path']
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    for target in targets:
        url = f"http://{target['endpoint']}/"
        for file in FILES:
            content = requests.get(url+file)
            path = os.path.join(
                    output_dir,
                    target['customer'],
                    target['site'],
                    target['model'],
                    f'{file}.json'
                    )
            with open(path, 'w') as f:
                f.write(content.text)

def read_config():
    config_yaml = open(CONFIG_FILE, 'r').read()
    config = yaml.safe_load(config_yaml)
    return config

async def juju_data():
    config = read_config()
    os.environ['JUJU_DATA'] = config['settings']['juju_data']
    output_dir = config['settings']['collection_path']

    controller = Controller()
    await controller.connect()

    models = await controller.get_models()
    model_uuids = await controller.model_uuids()

    for uuid in model_uuids:
        model = await controller.get_model(uuid)
        await model.connect()
        status = await model.get_status()
        bundle = await model.export_bundle()
        await model.disconnect()
        path = os.path.join(
                output_dir,
                f'{file}.json'
                )
        with open(f'status_{uuid}.json', 'w') as f:
            f.write(status.to_json())
        bundle_json = yaml.safe_load(bundle)
        with open(f'bundle_{uuid}.json', 'w') as f:
            f.write(json.dumps(bundle_json))

    await controller.disconnect()

def main():
    collect()
    jasyncio.run(juju_data())

if __name__ == "__main__":        
    main()
