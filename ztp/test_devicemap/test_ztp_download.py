#!/usr/bin/python3

import requests


def test_get_ztp(ip_addr):
    ztp = requests.get('http://{}}:8080/ztp.py'.format(ip_addr))
    assert ztp.status_code == 200

