from export import validate_ip
import logging

# Disable logging of all severity level 'CRITICAL' and below
logging.disable(logging.CRITICAL)


def test_ipv4_host_with_mask():
    assert validate_ip('1.1.1.1/32') == True


def test_ipv4_host_without_mask():
    assert validate_ip('1.1.1.1') == True


def test_ipv4_start_with_zero():
    assert validate_ip('0.1.1.1') == True


def test_ipv4_net():
    assert validate_ip('10.1.1.0/24') == True


def test_invalid_ip_with_mask():
    assert validate_ip('10.255.256.0/24') == False


def test_invalid_ip_without_mask():
    assert validate_ip('11.2.300.1') == False


def test_random_string():
    assert validate_ip('what is this') == False
