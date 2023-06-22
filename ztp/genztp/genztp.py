#!/usr/bin/python3

import csv
import pprint

'''
    This script reads in 'data.csv' and prints the device_map string required 
    in the ztp.py file.

'''
device_map = {}

with open('./data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        key, ip_val, sw_val, s_val = row[0] , row[1], row[2], row[3]
        ip_ver = {'ip':ip_val, 'sw':sw_val, 's_id':s_val}
        device_map[key] = (ip_ver)

print('Reading data.csv...')
print('Paste this into /srv/tftp/ztp.py before connecting the switch :\n')
pp = pprint.PrettyPrinter(indent=4)
print('device_map =')
pp.pprint(device_map)