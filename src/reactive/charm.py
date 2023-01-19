#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import os
import shutil
import logging

from charms.reactive import set_flag, clear_flag, when, when_not, hook, endpoint_from_flag
from charmhelpers.core import hookenv
from charmhelpers.core.templating import render
from charmhelpers.core.host import service_running

from jinja2 import Template

logger = logging.getLogger(__name__)

APP_PATH = "/var/lib/inventory-collector"
CONFIG_TEMPLATE = "collector.j2"
CONFIG_FILE = os.path.join(APP_PATH, "collector.yaml")
COLLECTOR_PATH = os.path.join(APP_PATH, "collector.py")
DEFAULT_COLLECTION_PATH = os.path.join(APP_PATH, "output")

@when_not("inventory-collector.installed")
def install():
    """Install hook."""
    hookenv.status_set("maintenance", "Installing charm...")
    if not os.path.exists(APP_PATH):
        os.mkdir(APP_PATH)
    # copy files over, render config
    src = os.path.join(
        hookenv.charm_dir(),
        "files/collector.py"
    )
    shutil.copyfile(src, COLLECTOR_PATH)
    os.chmod(COLLECTOR_PATH , 0o755)
    hookenv.status_set("active", "Unit is ready.")
    set_flag("inventory-collector.installed") 

@hook("upgrade-charm")
def upgrade_charm():
    clear_flag('inventory-collector.installed')
    clear_flag('inventory-exporter.targets.rendered')

@when("config.changed")
def config_changed():
    if not validate_configs():
        return
    clear_flag('inventory-exporter.targets.rendered')
    hookenv.status_set("active", "Unit is ready.")

@hook("update-status")
def update_status():
    hookenv.status_set("active", "Unit is ready.")

@hook("stop")
def stop():
    shutil.rmtree(APP_PATH)

#@when('endpoint.inventory-exporter.joined')
@hook('inventory-exporter-relation-joined')
def inventory_exporter_joined():
    clear_flag('inventory-exporter.targets.rendered')

#@when('endpoint.inventory-exporter.changed')
@hook('inventory-exporter-relation-changed')
def inventory_exporter_changed():
    clear_flag('inventory-exporter.targets.rendered')

#@when('endpoint.inventory-exporter.departed')
@hook('inventory-exporter-relation-departed')
def inventory_exporter_departed():
    clear_flag('inventory-exporter.targets.rendered')

@when_not('inventory-exporter.targets.rendered')
def render_targets():
    targets = []
    customer = hookenv.config("customer")
    site = hookenv.config("site")
    models = set()
    for rid in hookenv.relation_ids("inventory-exporter"):
        for unit in hookenv.related_units(rid):
            relation_data = hookenv.relation_get(rid=rid, unit=unit)
            ip = relation_data.get("private-address")
            port = relation_data.get("port")
            hostname = relation_data.get("hostname")
            model = relation_data.get("model")
            models.add(model)
            targets.append({
                'ip': ip,
                'port': port,
                'hostname': hostname,
                'customer': customer,
                'site': site,
                'model': model,
                })
    collection_path = hookenv.config('collection_path') or DEFAULT_COLLECTION_PATH
    juju_data = hookenv.config('juju_data')
    context = {
        'collection_path': collection_path,
        'juju_data': juju_data,
        'targets': targets,
        'customer': customer,
        'site': site,
        'models': list(models),
        }
    render(
        source=CONFIG_TEMPLATE,
        target=CONFIG_FILE,
        context=context,
    )
    set_flag('inventory-exporter.targets.rendered')

def validate_configs():
    """Validate the charm config options."""
    customer = hookenv.config("customer")
    site = hookenv.config("site")
    if not customer:
        hookenv.status_set("blocked", "Need to set 'customer' config")
        return False
    if not site:
        hookenv.status_set("blocked", "Need to set 'site' config")
        return False
    return True
