#usr/bin/python3
import csv

# init list at start of script
device_map = {}

# read data.csv into memory
with open('./data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        device_id, ip_val, sw_val, s_val, hn_val, pip_val = row[0] , row[1], row[2], row[3], row[4], row[5]
        device_vals = {'ip':ip_val, 'sw':sw_val, 's_id':s_val, 'p_hn':hn_val, 'p_ip':pip_val}
        device_map[device_id] = (device_vals)


# define json response body
json = '{"%(device_id)s":{"sw":"%(sw_val)s", "ip":"%(ip_val)s", "s_id":"%(s_val)s", "p_hn":"%(hn_val)s", "p_ip":"%(pip_val)s"}}'

# define wsgi app
def application(environ, start_response):

    query_string = (environ['QUERY_STRING'])

    device_id = query_string.split("=")[1]

    response_body = json % {
        'device_id': device_id,
        'sw_val': device_map.get(device_id)['sw'],
        'ip_val': device_map.get(device_id)['ip'],
        's_val': device_map.get(device_id)['s_id'],
        'hn_val': device_map.get(device_id)['p_hn'],
        'pip_val': device_map.get(device_id)['p_ip']
    }
    
    status = '200 OK'

    response_headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(response_body)))
        ]

    start_response(status, response_headers)
    return [response_body.encode()]
