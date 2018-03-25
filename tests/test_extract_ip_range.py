from export import extract_ip_range
import logging

# Disable logging of all severity level 'CRITICAL' and below
logging.disable(logging.CRITICAL)


def test_small_ipv4_range():
    assert (
            extract_ip_range('1.1.1.1', '1.1.1.3') ==
            ['1.1.1.1', '1.1.1.2', '1.1.1.3']
    )


def test_spanned_ipv4_range():
    assert (
            extract_ip_range('10.1.1.254', '10.1.2.1') ==
            ['10.1.1.254', '10.1.1.255', '10.1.2.0', '10.1.2.1']
    )
