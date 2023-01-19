#!/usr/local/sbin/charm-env python3
import json
import yaml
import os
import requests
import datetime
import tarfile

from juju import jasyncio
from juju.model import Model, Controller

CONFIG_FILE = "/var/lib/inventory-collector/collector.yaml"
FILES = ['dpkg', 'snap', 'kernel']

def read_config():
    config_yaml = open(CONFIG_FILE, 'r').read()
    config = yaml.safe_load(config_yaml)
    return config

def init():
    config = read_config()
    output_dir = config['settings']['collection_path']
    os.makedirs(output_dir, exist_ok=True)

def create_tars():
    config = read_config()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = config['settings']['collection_path']
    customer = config['settings']['customer']
    site = config['settings']['site']
    models = config['models']
    for model in models:
        tar_name = f'{customer}_@_{site}_@_{model}_@_{timestamp}.tar'
        tar_path = os.path.join(
                output_dir,
                tar_name,
                )
        tar_file = tarfile.open(tar_path,"w")
        tar_file.close()

def collect():
    config = read_config()
    targets = config['targets']
    output_dir = config['settings']['collection_path']
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    for target in targets:
        url = f"http://{target['endpoint']}/"
        hostname = target['hostname']
        customer = target['customer']
        site = target['site']
        model = target['model']
        for file in FILES:
            try:
                content = requests.get(url+file)
            except requests.ConnectionError:
                continue
            path = os.path.join(
                    output_dir,
                    f'{file}_@_{hostname}_@_{timestamp}',
                    )
            with open(path, 'w') as f:
                f.write(content.text)
            tar_name = f'{customer}_@_{site}_@_{model}_@_{timestamp}.tar'
            tar_path = os.path.join(
                    output_dir,
                    tar_name,
                    )
            tar_file = tarfile.open(tar_path,"a:")
            tar_file.add(path)
            tar_file.close()
            os.remove(path)

async def juju_data():
    config = read_config()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    customer = config['settings']['customer']
    site = config['settings']['site']
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
        status_path = os.path.join(
                output_dir,
                f'juju_status_@_{uuid}_@_{timestamp}',
                )
        bundle_path = os.path.join(
                output_dir,
                f'juju_bundle_@_{uuid}_@_{timestamp}',
                )
        with open(status_path, 'w') as f:
            f.write(status.to_json())
        tar_name = f'{customer}_@_{site}_@_{uuid}_@_{timestamp}.tar'
        tar_path = os.path.join(
                output_dir,
                tar_name,
                )
        tar_file = tarfile.open(tar_path,"a:")
        tar_file.add(status_path)
        tar_file.close()
        os.remove(status_path)

        bundle_yaml = yaml.load_all(bundle, Loader=yaml.FullLoader)
        for data in bundle_yaml:
            bundle_json = json.dumps(data)
            # skip SAAS; multiple documents, we need to import only the bundle
            if 'offers' in bundle_json:
                continue
            with open(bundle_path, 'w') as f:
                f.write(bundle_json)
            tar_name = f'{customer}_@_{site}_@_{uuid}_@_{timestamp}.tar'
            tar_path = os.path.join(
                    output_dir,
                    tar_name,
                    )
            tar_file = tarfile.open(tar_path,"a:")
            tar_file.add(bundle_path)
            tar_file.close()
            os.remove(bundle_path)

    await controller.disconnect()

def main():
    init()
    create_tars()
    collect()
    jasyncio.run(juju_data())

if __name__ == "__main__":        
    main()
