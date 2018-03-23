#!/usr/bin/env python

"""
Author: Nasir Bilal
Email: nbilal@paloaltonetworks.com
"""

##############################################################
# IMPORTS
##############################################################
from time import sleep
import xmltodict
import random
import pytz
from utils.config import Config
import requests

##############################################################
# GLOBAL VARIABLES
##############################################################
URL = Config.URL
API_KEY = Config.API_KEY
DG = 'child_dg_lab01'
LOC_DICT = {
    'shared': '/config/shared',
    'dg': "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{}']".format(DG),
}
XPATH_DICT = {
    'address': "/address/entry[@name='{}']",
    'address-group': "/address-group/entry[@name='{}']",
    'service': "/service/entry[@name='{0}_{1}']",
    'service-group': "/service-group/entry[@name='{}']",
    'security': "/post-rulebase/security/rules/entry[@name='{}']",
    'nat': "/post-rulebase/security/nat/entry[@name='{}']",
}
EL_DICT = {
    'ip-netmask': '<ip-netmask>{}</ip-netmask>',
    'ip-range': '<ip-range>{}</ip-range>',
    'fqdn': '<fqdn>{}</fqdn>',
    'address-group': '',
    'service': '<protocol><{0}><port>{1}</port></{0}></protocol>',
    'service-group': '',
    'security': '<target><negate>no</negate></target><to><member>{to}</member></to>'\
                '<profile-setting><group><member>{profile-setting}</member></group></profile-setting>'\
                '<from><member>{from}</member></from><source><member>{source}</member></source>'\
                '<destination><member>{destination}</member></destination>'\
                '<source-user><member>any</member></source-user>'\
                '<category><member>any</member></category><application><member>any</member></application>'\
                '<service><member>{service}</member></service><hip-profiles><member>any</member></hip-profiles>'\
                '<action>{action}</action><log-setting>{log-setting}</log-setting>',
    'dnat': '<destination-translation><translated-address>{translated-address}'\
            '</translated-address></destination-translation>'\
            '<target><negate>no</negate></target><to><member>{to}</member></to>'\
            '<from><member>{from}</member></from><source><member>{source}</member></source>'\
            '<destination><member>{destination}</member></destination><service>any</service></request>',
    'snat': '<source-translation><static-ip><bi-directional>yes</bi-directional>'\
            '<translated-address>{translated-address}</translated-address>'\
            '</static-ip></source-translation>'
            '<target><negate>no</negate></target><to><member>{to}</member></to>' \
            '<from><member>{from}</member></from><source><member>{source}</member></source>' \
            '<destination><member>{destination}</member></destination><service>any</service></request>',
    '2nat': '',
    '0nat': '<target><negate>no</negate></target><to><member>{to}</member></to>'\
            '<from><member>{from}</member></from><source><member>{source}</member></source>'\
            '<destination><member>{destination}</member></destination><service>{service}</service>',
    'pat': '<source-translation><dynamic-ip-and-port><translated-address><member>{source-translation}</member>'\
            '</translated-address></dynamic-ip-and-port></source-translation><target><negate>no</negate></target>'\
            '<to><member>{to}</member></to><from><member>{from}</member></from><source>'\
            '<member>{source}</member></source><destination><member>{destination}</member>'\
            '</destination><service>{service}</service>',
}
COUNTRIES = list(pytz.country_names)
ZONES = ['inside', 'outside', 'dmz', 'vpn_l2l', 'vpn_ra']


##############################################################
# FUNCTIONS
##############################################################
def run_cmd(cmd: str) -> str:
    # Convert CLI commands into API calls
    # TODO: add support for commands that take args like 'show interface X'
    c1 = cmd.split()
    c2 = list(reversed(c1))
    cmd_xml = ''.join((
        ''.join('<{}>'.format(w) for w in c1[:len(c1)-1]),
        '<{}/>'.format(c2[0]),
        ''.join('</{}>'.format(w) for w in c2[1:len(c2)]),
        ))
    op_call_dict = {
        'key': API_KEY,
        'type': 'op',
        'cmd': cmd_xml,
    }
    try:
        r = requests.get(URL, op_call_dict, verify=False)
        return r.text
    except BaseException as e:
        return f'Failed to run cmd due to {e}'


def create_svc(prot: str, port: int, loc: str) -> str:
    pp = (prot, port)
    set_call_dict = {
        'key': API_KEY,
        'type': 'config',
        'action': 'set',
        'xpath': LOC_DICT[loc] + XPATH_DICT['service'].format(*pp),
        'element': EL_DICT['service'].format(*pp),
    }
    try:
        r = requests.get(URL, set_call_dict, verify=False)
        return r.text
    except BaseException as e:
        return f'Failed to create service due to {e}'


def create_addr(name: str, type: str, addr: str, loc: str) -> str:
    # Create address of type 'ip-netmask'
    set_call_dict = {
        'key': API_KEY,
        'type': 'config',
        'action': 'set',
        'xpath': LOC_DICT[loc] + XPATH_DICT['address'].format(name),
        'element': EL_DICT[type].format(addr),
    }
    try:
        r = requests.get(URL, set_call_dict, verify=False)
        return r.text
    except BaseException as e:
        return f'Failed to create address due to {e}'


def create_rule(**kwargs) -> str:
    # Create security rule in post-rulebase of given device-group
    set_call_dict = {
        'key': API_KEY,
        'type': 'config',
        'action': 'set',
        'xpath': LOC_DICT[kwargs['loc']] + XPATH_DICT[kwargs['type']].format(kwargs['name']),
        'element': EL_DICT[kwargs['type']].format(**kwargs),
    }
    try:
        r = requests.get(URL, set_call_dict, verify=False)
        return r.text
    except BaseException as e:
        return f"Failed to create {kwargs['type']} rule due to {e}"


def get_objects(object_type, location) -> list:
    # Return list of all address object names from given location
    get_call_dict = {
        'key': API_KEY,
        'type': 'config',
        'action': 'get',
        'xpath': LOC_DICT[location] + "/" + object_type,
    }
    try:
        r = requests.get(URL, get_call_dict, verify=False)
        parsed = xmltodict.parse(r.text)['response']['result'][object_type].get('entry')
        return parsed
    except BaseException as e:
        return f"Failed to retrieve objects due to {e}"

##############################################################
# MAIN FUNCTION
##############################################################
def main():
    # suppress warnings from requests library
    requests.packages.urllib3.disable_warnings()

    # # Create some shared objects
    # location = 'shared'
    # for protocol in ('tcp', 'udp'):
    #     for port in range(3000, 5000, 100):
    #         create_svc(protocol, port, location)
    #         sleep(0.05)

    # # Create some device-group 'ip-netmask' address objects
    # location = 'dg'
    # t = 'ip-netmask'
    # for c in COUNTRIES:
    #     name = '{0}_{1}_{2:03d}'.format(
    #         c.lower(),
    #         random.choice(['web', 'file', 'db']),
    #         random.randrange(1, 100)
    #     )
    #     addr = '{}.{}.{}.{}/{}'.format(
    #         random.randrange(1, 224),
    #         random.randrange(255),
    #         random.randrange(255),
    #         random.randrange(1, 255),
    #         32,
    #     )
    #     print(f'name = {name}\naddr = {addr}')
    #     create_addr(name, t, addr, location)
    #     sleep(0.05)

    # # Create some device-group 'ip-range' address objects
    # location = 'dg'
    # t = 'ip-range'
    # for c in COUNTRIES:
    #     name = '{0}_{1}_{2:03d}'.format(
    #         c.lower(),
    #         random.choice(['wan', 'lan', 'vpn', 'dmz', 'wlan']),
    #         random.randrange(1, 100)
    #     )
    #     (o1, o2, o3, o4) = (
    #         random.randrange(1, 224),
    #         random.randrange(255),
    #         random.randrange(255),
    #         random.choice((0, 100)),
    #     )
    #     addr = f'{o1}.{o2}.{o3}.{o4}-{o1}.{o2}.{o3}.{o4+100}'
    #     create_addr(name, t, addr, location)
    #     sleep(0.05)

    # # Create some device-group 'fqdn' address objects
    # location = 'dg'
    # t = 'fqdn'
    # for _ in range(20):
    #     name = '{0}{1:03d}.{2}.{3}'.format(
    #         random.choice(COUNTRIES).lower(),
    #         random.randrange(1, 100),
    #         random.choice(['lab', 'example']),
    #         random.choice(['com', 'org', 'net', 'local']),
    #     )
    #     print(f'name = {name}\naddr = {name}')
    #     create_addr(name, t, name, location)
    #     sleep(0.05)

    # Create some device-group security post-rules
    address_list = [a['@name'] for a in get_objects('address', 'dg')]
    service_list = [s['@name'] for s in get_objects('service', 'shared')]
    location = 'dg'
    for _ in range(1000):
        source = random.choice(address_list)
        destination = random.choice(address_list)
        service = random.choice(service_list)
        sz = random.choice(ZONES)
        dz = random.choice(ZONES)
        if sz == dz:
            continue
        else:
            action = random.choice(('allow', 'deny'))
            name = f'{sz}_{dz}_{action}_{_:05d}'
            sec_rule_dict = {
                'name': name,
                'to': dz,
                'profile-setting': 'spg_default',
                'from': sz,
                'source': source,
                'destination': destination,
                'service': service,
                'action': action,
                'log-setting': 'default',
                'loc': location,
                'type': 'security',
            }
            create_rule(**sec_rule_dict)
            sleep(0.05)

    # # Run CLI command via API
    # cmd = 'show clock'
    # print(run_cmd(cmd))


##############################################################
# RUN IT!
##############################################################
if __name__ == '__main__':
    main()
