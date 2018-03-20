#!/usr/bin/env python

"""
Author: Nasir Bilal
Email: nbilal@paloaltonetworks.com
"""

import xmltodict
from ipaddress import ip_network, ip_address
import re
from openpyxl import Workbook
import logging
from copy import copy


PAN_CFG_FILE = 'Inputs/get_config_panorama.xml'
DEVICE_GROUP = 'Crewe'


##############################################################
# FUNCTIONS
##############################################################
def flatten(c):
    if not isinstance(c, str):
        for i in c:
            if hasattr(i, '__iter__'):
                for j in flatten(i):
                    yield j
            else:
                yield i
    else:
        yield c


def validate_ip(address):
    try:
        ip_network(address)
        return True
    except ValueError:
        return False


def findIPs(start, end):
    start = ip_address(start)
    end = ip_address(end)
    result = []
    while start <= end:
        result.append(str(start))
        start += 1
    return result


def resolve_address(address, pan_cfg):
    """
    Queries address-group for object matching this string.
    :param address: address object being searched for
    :param add_tree: etree built from address section of PANOS XML
    :return: string of object's IP address
    """
    if address in ('any', 'dynamic', 'unknown') or validate_ip(address):
        return [address]
    elif address in ('panw-highrisk-ip-list', 'panw-known-ip-list'):
        return ['dynamic']
    else:
        sh_add_tree = pan_cfg['config']['shared']['address']['entry']
        sh_ag_tree = pan_cfg['config']['shared']['address-group']['entry']
        sh_edl_tree = pan_cfg['config']['shared']['external-list']['entry']
        device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
        dg_tree = [a for a in device_groups if a['@name'] == DEVICE_GROUP][0]
        dg_add_tree = dg_tree['address']['entry']
        dg_ag_tree = dg_tree['address-group']['entry']

        try:
            if dg_tree.get('external-list', {}).get('entry'):
                for edl in dg_tree['external-list']['entry']:
                    if edl['@name'] == address:
                        return ['dynamic']
            if pan_cfg['config']['shared']['external-list'].get('entry'):
                for edl in pan_cfg['config']['shared']['external-list']['entry']:
                    if edl['@name'] == address:
                        return ['dynamic']
            if dg_add_tree:
                for add in dg_add_tree:
                    if add['@name'] == address:
                        if add.get('ip-netmask'):
                            addr = add.get('ip-netmask')
                        elif add.get('ip-range'):
                            addr = findIPs(*add.get('ip-range').split('-'))
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
                for add in dg_ag_tree:
                    if add['@name'] == address:
                        return add.get('static', {}).get('member')
        except BaseException as e:
            logging.exception("Unable to search dg_ag_tree due to {}".format(e))
        try:
            if sh_ag_tree:
                for add in sh_ag_tree:
                    if add['@name'] == address:
                        return add.get('static', {}).get('member')
        except BaseException as e:
            logging.exception("Unable to search sh_ag_tree due to {}".format(e))

        return 'unknown'



def resolve_service(service, pan_cfg):
    """
    Queries services and service-groups for object matching this string.
    :param service: address object being searched for
    :param pan_cfg: nested dictionary built from address section of PANOS XML
    :return: protocol_port value for given service if found, else 'unknown'
    """
    if service == 'any' or service == 'application-default' or bool(re.search(r'(tcp|udp)_\d+$', str(service))):
        return service
    else:
        sh_svc_tree = pan_cfg['config']['shared']['service']['entry']
        sh_sg_tree = pan_cfg['config']['shared']['service-group']['entry']
        device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
        dg_tree = [a for a in device_groups if a['@name'] == DEVICE_GROUP][0]
        dg_svc_tree = dg_tree['service']['entry']
        dg_sg_tree = dg_tree['service-group']['entry']
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

        return 'unknown'



def main():

    # Initialize log file for exceptions
    logging.basicConfig(level=logging.INFO, filename='exceptions.log')

    with open(PAN_CFG_FILE, 'r') as f:
        pan_cfg = xmltodict.parse(f.read())

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
            # If "source" field is a list of address(es)/address-group(s), iterate over each
            # Return a list of IPs
            add_check = lambda x: validate_ip(x) or x in ('any', 'dynamic', 'unknown')
            if add_check(r['source'].get('member')):
                src = copy(r['source'].get('member'))
            else:
                src = copy(r['source'].get('member'))
                while not add_check(src) and sum(map(add_check, src)) < len(list(src)):
                    if type(src) == list:
                        src_list = []
                        for s in src:
                            s = resolve_address(s, pan_cfg)
                            src_list.append(s)
                        src = list(src_list)
                    # Otherwise, try to resolve single address in "source" field into list of one IP
                    else:
                        src = resolve_address(src, pan_cfg)
                    src = list(flatten(src))

            if add_check(r['destination'].get('member')):
                dst = copy(r['destination'].get('member'))
            else:
                dst = copy(r['destination'].get('member'))
                while not add_check(dst) and sum(map(add_check, dst)) < len(list(dst)):
                    if type(dst) == list:
                        dst_list = []
                        for d in dst:
                            d = resolve_address(d, pan_cfg)
                            dst_list.append(d)
                        dst = list(dst_list)
                    # Otherwise, try to resolve single address in "source" field into list of one IP
                    else:
                        dst = resolve_address(dst, pan_cfg)
                    dst = list(flatten(dst))

            # Resolve services to a list of ports
            port_check = lambda x: x in ('any', 'unknown', 'application-default') or bool(re.search(r'(tcp|udp)_[\d\-,]+$', str(x))) or not x
            if type(r['service']) == list:
                dport = copy(r['service'][0].get('member'))
            else:
                dport = copy(r['service'].get('member'))
            if not port_check(dport):
                while not port_check(dport) and sum(map(port_check, dport)) < len(list(dport)):
                    if type(dport) == list:
                        dp_list = []
                        for dp in dport:
                            dp = resolve_service(dp, pan_cfg)
                            dp_list.append(dp)
                        dport = list(dp_list)
                    # Otherwise, try to resolve single address in "source" field into list of one IP
                    else:
                        dport = resolve_service(dport, pan_cfg)
                    dport = list(flatten(dport))

            rule = (
                str(r['@name']),
                str(r['from'].get('member')),
                str(r['source'].get('member')),
                str(src),
                str(r['to'].get('member')),
                str(r['destination'].get('member')),
                str(dst),
                str(r['application'].get('member')),
                str(r['service'].get('member')),
                str(dport),
                str(r['category'].get('member')),
                str(r['action']),
                str(r.get('profile-setting', {}).get('group', {}).get('member', 'none')),
                str(r['log-setting']),
            )
            ws.append(rule)
        except BaseException as e:
            logging.exception("UNABLE TO EXPORT RULE {} DUE TO {}".format(r, e))

    wb.save('{}_rules.xlsx'.format(DEVICE_GROUP))


if __name__ == '__main__':
    main()

