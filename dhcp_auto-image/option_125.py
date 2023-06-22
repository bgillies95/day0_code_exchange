#!/usr/bin/python
from re import sub

cisco_vendor_code = '00000009'
cisco_subcode = '05'

filename = input("Enter the filename you want to hex for option 125: ")
hex_len = hex(len(filename))[2:]
encoded = filename.encode('utf-8').hex()
sub_plus_hex = int(cisco_subcode) + int(hex_len)
full_string = cisco_vendor_code + f"{sub_plus_hex}" + cisco_subcode + encoded
isc_dhcp_format = ":".join(map("".join, zip(*[iter(full_string)]*2))).upper()

print(f"Option 125 will be: \n option 123 hex {full_string}")
print('\n')
print(f"ISC DHCPD format is: \n {isc_dhcp_format}")
