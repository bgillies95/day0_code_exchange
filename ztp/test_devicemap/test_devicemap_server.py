#!/usr/bin/python3

import requests

def test_device_map(ip_addr):
    data = requests.get('http://{}:8081/?device_id=TESTSERIAL'.format(ip_addr))
    assert data.status_code == 200
