#!/usr/bin/env python

"""
Author: Nasir Bilal
Email: nbilal@paloaltonetworks.com
"""

##############################################################
# IMPORTS
##############################################################
from utils.config import Config
import xmltodict
import requests
from datetime import datetime
from ipaddress import ip_network, ip_address
import re
from openpyxl import Workbook
import logging
from copy import copy

##############################################################
# GLOBAL VARIABLES
##############################################################
PAN_CFG_FILE = 'tests/get_config_panorama.xml'
DEVICE_GROUP = 'child_dg_lab01'


##############################################################
# FUNCTIONS
##############################################################
def get_config(url: str, api_key: str) -> str:
    # Returns API response as a string.
    get_call_dict = {
        'key': api_key,
        'type': 'config',
        'action': 'show',
    }
    try:
        r = requests.get(url, get_call_dict, verify=False)
        return r.text
    except BaseException as e:
        return f"Failed to retrieve configuration due to {e}"


def flatten(c: list) -> list:
    # Checks if input is a list and returns the value.
    if not isinstance(c, str):
        for i in c:
            try:
                for j in flatten(i):
                    yield j
            except AttributeError:
                yield i
    else:
        yield c


def validate_ip(address: str) -> bool:
    # Validates the IP address.
    try:
        ip_network(address)
        return True
    except ValueError:
        return False


def extract_ip_range(start: str, end: str) -> list:
    # If IP address is a range, extracts and returns the range of individual IPs.
    start = ip_address(start)
    end = ip_address(end)
    result = []
    while start <= end:
        result.append(str(start))
        start += 1
    return result


def resolve_service(service: str, pan_cfg: dict) -> list:
    # Queries services and service-groups for object matching this string.

    def singleton(x):
        return x in ('any', 'unknown', 'application-default') \
               or bool(re.search(r'(^tcp|udp)_[\d\-,]+$', str(x))) \
               or not x

    def inner_resolve(service):
        sh_svc_tree = pan_cfg['config']['shared'].get('service', {}).get('entry')
        sh_sg_tree = pan_cfg['config']['shared'].get('service-group', {}).get('entry')
        device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
        dg_tree = [a for a in device_groups if a['@name'] == DEVICE_GROUP][0]
        dg_svc_tree = dg_tree.get('service', {}).get('entry')
        dg_sg_tree = dg_tree.get('service-group', {}).get('entry')
        try:
            if dg_svc_tree:
                for svc in dg_svc_tree:
                    if svc['@name'] == service:
                        if svc.get('protocol'):
                            if svc['protocol'].get('tcp'):
                                s = "tcp_{}".format(svc['protocol']['tcp'].get('port'))
                            elif svc['protocol'].get('udp'):
                                s = "udp_{}".format(svc['protocol']['udp'].get('port'))
                        return [s]
        except BaseException as e:
            logging.exception("Couldn't search device-group services due to {}".format(e))
        try:
            if sh_svc_tree:
                for svc in sh_svc_tree:
                    if svc['@name'] == service:
                        if svc.get('protocol'):
                            if svc['protocol'].get('tcp'):
                                s = "tcp_{}".format(svc['protocol']['tcp'].get('port'))
                            elif svc['protocol'].get('udp'):
                                s = "udp_{}".format(svc['protocol']['udp'].get('port'))
                        return [s]
        except BaseException as e:
            logging.exception("Couldn't search shared services due to {}".format(e))
        try:
            if dg_sg_tree:
                for svc in dg_sg_tree:
                    if svc['@name'] == service:
                        return svc.get('members').get('member')
        except BaseException as e:
            logging.exception("Unable to search dg_ag_tree due to {}".format(e))

        try:
            if sh_sg_tree:
                for svc in sh_sg_tree:
                    if svc['@name'] == service:
                        return svc.get('members').get('member')
        except BaseException as e:
            logging.exception("Unable to search dg_ag_tree due to {}".format(e))

        return ['unknown']

    while not singleton(service) and sum(map(singleton, service)) < len(list(service)):
        if type(service) == list:
            dp_list = []
            for dp in service:
                dp = inner_resolve(dp)
                dp_list.append(dp)
            service = list(dp_list)
        # Otherwise, try to resolve single service/service-group to list of ports
        else:
            service = inner_resolve(service)
        service = list(flatten(service))

    return service


def resolve_address(address: str, pan_cfg: dict) -> list:
    # Queries address-group for object matching this string.

    def singleton(x):
        if x in ('panw-highrisk-ip-list', 'panw-known-ip-list'):
            x = 'dynamic'
        return validate_ip(x) or x in ('any', 'dynamic', 'unknown')

    def inner_resolve(address, pan_cfg):
        sh_add_tree = pan_cfg['config']['shared'].get('address', {}).get('entry')
        sh_ag_tree = pan_cfg['config']['shared'].get('address-group', {}).get('entry')
        sh_edl_tree = pan_cfg['config']['shared'].get('external-list', {}).get('entry')
        device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
        dg_tree = [a for a in device_groups if a['@name'] == DEVICE_GROUP][0]
        dg_add_tree = dg_tree.get('address', {}).get('entry')
        dg_ag_tree = dg_tree.get('address-group', {}).get('entry')

        try:
            if dg_tree.get('external-list', {}).get('entry'):
                dg_edls = dg_tree.get('external-list', {}).get('entry')
                if type(dg_edls) == list:
                    for edl in dg_edls:
                        if edl['@name'] == address:
                            return ['dynamic']
                else:
                    if dg_edls.get('@name'):
                        if dg_edls['@name'] == address:
                            return ['dynamic']
            if sh_edl_tree:
                if type(sh_edl_tree) == list:
                    for edl in sh_edl_tree:
                        if edl['@name'] == address:
                            return ['dynamic']
                else:
                    if sh_edl_tree['@name'] == address:
                        return ['dynamic']
            if dg_add_tree:
                for add in dg_add_tree:
                    if add['@name'] == address:
                        if add.get('ip-netmask'):
                            addr = add.get('ip-netmask')
                        elif add.get('ip-range'):
                            addr = extract_ip_range(*add.get('ip-range').split('-'))
                        elif add.get('fqdn'):
                            addr = 'dynamic'
                        return [addr]
        except BaseException as e:
            logging.exception("Unable to search dg_add_tree due to {}".format(e))
        try:
            if sh_add_tree:
                for add in sh_add_tree:
                    if add['@name'] == address:
                        if add.get('ip-netmask'):
                            addr = add.get('ip-netmask')
                        elif add.get('ip-range'):
                            addr = 'ip-range'
                        elif add.get('fqdn'):
                            addr = 'dynamic'
                        return [addr]
        except BaseException as e:
            logging.exception("Unable to search sh_add_tree due to {}".format(e))

        try:
            if dg_ag_tree:
                if type(dg_add_tree) == list:
                    for add in dg_ag_tree:
                        if add['@name'] == address:
                            return add.get('static', {}).get('member')
                else:
                    if dg_ag_tree['@name'] == address:
                        return dg_ag_tree('static', {}).get('member')
        except BaseException as e:
            logging.exception("Unable to search dg_ag_tree due to {}".format(e))
        try:
            if sh_ag_tree:
                if type(sh_ag_tree) == list:
                    for add in sh_ag_tree:
                        if add['@name'] == address:
                            return add.get('static', {}).get('member')
                else:
                    if sh_ag_tree['@name'] == address:
                        return sh_ag_tree.get('static', {}).get('member')
        except BaseException as e:
            logging.exception("Unable to search sh_ag_tree due to {}".format(e))

        return ['unknown']

    while not singleton(address) and sum(map(singleton, address)) < len(list(address)):
        if type(address) == list:
            address_list = []
            for a in address:
                a = inner_resolve(a, pan_cfg)
                address_list.append(a)
            address = list(address_list)
        # Otherwise, try to resolve single address
        else:
            address = inner_resolve(address, pan_cfg)
        address = list(flatten(address))

    return address


##############################################################
# MAIN FUNCTION
##############################################################
def main():
    # Initialize log file for exceptions
    logging.basicConfig(level=logging.INFO, filename='exceptions.log')

    with open(PAN_CFG_FILE, 'r') as f:
        pan_cfg = xmltodict.parse(f.read())['response']['result']

    device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
    dg_tree = [a for a in device_groups if a['@name'] == DEVICE_GROUP][0]
    nat_tree = dg_tree['post-rulebase']['nat']['rules']['entry']
    sec_tree = dg_tree['post-rulebase']['security']['rules']['entry']

    # BUILD CSV FILE FOR SUMMARIZED RESULTS
    wb = Workbook()
    ws = wb.active
    ws.append([
        'NAME',
        'FROM',
        'SOURCE',
        'RESOLVED SRC',
        'TO',
        'DESTINATION',
        'RESOLVED DST',
        'APP',
        'SERVICE',
        'RESOLVED PT',
        'CATEGORY',
        'ACTION',
        'PROFILE-SETTING',
        'LOG-SETTING',
    ])

    for r in sec_tree:
        try:
            # resolve source address(es)
            src_ip = resolve_address(r['source'].get('member'), pan_cfg)

            # resolve destination address(es)
            dst_ip = resolve_address(r['destination'].get('member'), pan_cfg)

            # Resolve destination port object(s) to a list of ports
            if type(r['service']) == list:
                dport = r['service'][0].get('member')
            else:
                dport = r['service'].get('member')
            dst_port = resolve_service(dport, pan_cfg)

            # Fill out table row with all rule details
            row = (
                str(r['@name']),
                str(r['from'].get('member')),
                str(r['source'].get('member')),
                str(src_ip),
                str(r['to'].get('member')),
                str(r['destination'].get('member')),
                str(dst_ip),
                str(r['application'].get('member')),
                str(r['service'].get('member')),
                str(dst_port),
                str(r['category'].get('member')),
                str(r['action']),
                str(r.get('profile-setting', {}).get('group', {}).get('member', 'none')),
                str(r['log-setting']),
            )
            ws.append(row)
        except BaseException as e:
            logging.exception("UNABLE TO EXPORT RULE {} DUE TO {}".format(r, e))

    wb.save('{}_{}.xlsx'.format(DEVICE_GROUP, datetime.now().strftime('%Y%m%d_%H%M%S')))


##############################################################
# RUN IT
##############################################################
if __name__ == '__main__':
    main()
