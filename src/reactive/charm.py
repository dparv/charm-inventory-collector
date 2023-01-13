#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import logging

from charms.reactive import set_flag, when, when_not, hook, endpoint_from_flag
from charms.layer import snap
from charmhelpers.core import hookenv
from charmhelpers.core.host import service_running

logger = logging.getLogger(__name__)

@when_not("inventory-collector.installed")
def install():
    """Install hook."""
    hookenv.status_set("maintenance", "Installing charm...")
    hookenv.status_set("active", "Unit is ready.")
    set_flag("inventory-collector.installed") 

@when("config.changed")
def config_changed():
    #TODO: render config here
    hookenv.status_set("active", "Unit is ready.")

@hook("update-status")
def update_status():
    hookenv.status_set("active", "Unit is ready.")

@hook("stop")
def stop():
    # cleanup scripts maybe? dunno..
    pass

@hook('inventory-exporter-joined')
def configure_inventory_exporter_relation(relation_id=None, remote_unit=None):
    for relation_id in hookenv.relation_ids("inventory-exporter"):
        for relation_data in hookenv.relations_for_id(relation_id):
            target = relation_data.get("target")
            port = relation_data.get("port")
            if not (hostname and port):
                continue
            hostname = "{}:{}".format(hostname, port)
            hookenv.log(hostname, level='DEBUG')
    hookenv.status_set('active', 'Unit is ready.')

