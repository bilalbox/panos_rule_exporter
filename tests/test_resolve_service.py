import xmltodict
import logging
from sys import path
path.append('..')
from export import resolve_service
# Disable logging of all severity level 'CRITICAL' and below
logging.disable(logging.CRITICAL)

with open('get_config_panorama.xml', 'r') as f:
    CFG = xmltodict.parse(f.read())['response']['result']

DG = 'child_dg_lab01'

def test_nonexistent_object():
    assert resolve_service('nobody_knows_me', CFG, DG) == ['unknown']


def test_any():
    assert resolve_service('any', CFG, DG) == 'any'


def test_application_default():
    assert resolve_service('application-default', CFG, DG) == 'application-default'


def test_single_port():
    assert resolve_service('udp_4500', CFG, DG) == 'udp_4500'


def test_port_range():
    assert resolve_service('tcp_40000-65535', CFG, DG) == 'tcp_40000-65535'


def test_service_group():
    assert resolve_service('sg_random_mix', CFG, DG) == ['tcp_2', 'tcp_161', 'udp_2', 'udp_40000-65535']


def test_service_group_nested():
    assert resolve_service('sg_nested_mix_01', CFG, DG) == [
        'udp_53', 'udp_69', 'udp_500', 'udp_4500', 'tcp_16', 'tcp_34',
        'tcp_36', 'tcp_229', 'tcp_1109', 'tcp_40000-65535'
    ]
