#!/usr/bin/python

from cli import configure, cli, execute, executep, configurep
import time
import urllib2
import json
import re


############### DEVICE VALUES #################
tftp_server = '10.198.33.41'
img_cat9k = 'cat9k_iosxe.16.12.05b.SPA.bin'
img_cat9k_md5 = '9910bcc37a08cea74b595f9c998e24f4'
software_version = 'Cisco IOS XE Software, Version 16.12.05b'
###############################################





def get_sw_version():   
    
    '''
    ***
        DESCRIPTION:
                Returns the current software version of the device in the format A.B.C
        
        INPUT PARAMETERS:
                No input parameters.

        RETURNS:
                current_version (string): Returns a string of the current software version in the format A.B.C
    ***
    '''

    version_output = execute("show version | include Cisco IOS XE Software")
    current_version = version_output.split(" ")[-1]  # The [-1] returns the last element of the array after splitting the string
    return current_version


def get_device_map(serial_number):
    
    '''
    ***
        DESCRIPTION:
                Using the serial number, the function returns a device map, which is a nested dictionary with the key as the serial number and the value as an inner dictionary with technical details of the device.
        
        INPUT PARAMETERS:
                serial_number (string): Imports in a string of the device's serial number.

        RETURNS:
                device_map (dictionary): Returns a nested dictionary containing serial number as the key, and the value as another dictionary containing: staging IP address, upgrade software version, and stack number.
    ***
    '''

    url = 'http://{}:8081/?device_id={}'.format(tftp_server, serial_number)
    req_url = urllib2.Request(url)
    req_url.add_header('Accept', 'application/json')
    data = urllib2.urlopen(req_url)
    device_map = json.loads(data.read())
    return device_map


def get_serial_num():
    
    '''
    ***
        DESCRIPTION:
                Returns the serial number of the device.
        
        INPUT PARAMETERS:
                 No input parameters.
               
        RETURNS:
                serial_number (string): Returns the serial number of the device.
    ***
    '''

    serial_output = execute("show version | include Processor")
    serial_number = serial_output.split(" ")[-1]
    return serial_number


def get_device_values(serial_number):
    
    '''
    ***
        DESCRIPTION:
                Using the serial number, the function returns five device values, which being the: staging IP address, upgrade software version, stack number, hostname and the vl69ip (Vlan 69 IP address = management IP address). If there are no device values found, an error statement is raised.  
        
        INPUT PARAMETERS:
                serial_number (string): Imports in a string of the device's serial number. 
               
        RETURNS:
                staging_ip (string), upgrade_version (string), stack_number (string), hostname (string), vl69ip (string): Returns the staging IP address, the upgrade software version, the stack number of the device, the hostname and the vl69ip (Vlan 69 IP address, same as Management IP address), in this order.
    ***
    '''

    device_values = device_map.get(serial_number)
    if device_values:
        staging_ip = str(device_values['ip'])
        upgrade_version = str(device_values['sw'])
        stack_number = str(device_values['s_id'])
        hostname = str(device_values['p_hn'])
        vl69ip = str(device_values['p_ip'])
    else:
         raise ValueError("#ERROR# Device not found in device mapping. Ensure \
         data.csv is updated  process #ERROR#\n")
    return staging_ip, upgrade_version, stack_number, hostname, vl69ip


def apply_base_config(staging_ip, hostname, vl69ip):
    
    '''
    ***
        DESCRIPTION:
                Applies base configurations to the device such as adding the: hostname, interface configuration, rsa key generation, etc.
        
        INPUT PARAMETERS:
               staging_ip (string), hostname (string), vl69ip (string): Imports the staging IP address, the hostname of the device, and the vl69ip (Vlan 69 IP address = Management IP address) in this order. 

        RETURNS:
                No return statement.
    ***
    '''

    gateway_list = vl69ip.split(".")
    gateway = '10.{}.{}.254'.format(gateway_list[1], gateway_list[2])

    config_cmds = [
    "hostname {}".format(hostname),
    "ip ssh version 2",
    "ip ssh logging events",
    "line vty 0 15",
    "login local",
    "transport input ssh",
    "ip default-gateway {}".format(gateway),
    "interface G0/0",
    "no shutdown",
    "ip address {} 255.255.254.0".format(staging_ip),
    "vlan 69",
    "no shutdown",
    "name RT_MGMT_NET",
    "interface vlan 69",
    "ip address {} 255.255.255.0".format(vl69ip),
    "no shutdown",
    "description Switch Management Interface",
    "no ip redirects",
    "no ip unreachables",
    "no ip proxy-arp",
    "no ip mask-reply",
    "no ip directed-broadcast",
    "interface TenGigabitEthernet1/1/1",
    "description TEST DESC",
    "switchport mode trunk",
    "switchport trunk native vlan 999",
    "logging event link-status",
    "switchport nonegotiate",
    "power inline never",
    "ip dhcp snooping trust",
    "no shutdown"
    ]
    configurep(config_cmds)


def upgrade_sw_version(current_version, upgrade_version):
   
    '''
    ***
        DESCRIPTION:
                Using the current and the upgrade software version, the function returns a boolean as to answer the question "Is an upgrade to the software required?" If the two software versions are the same, upgrade is not required, otherwise it is required.
        
        INPUT PARAMETERS:
               current_version (string), upgrade_version (string): Imports two strings, which being the current and the upgrade software version, in this order.

        RETURNS:
                upgrade_required (boolean): Returns False if an upgrade to software is not required, or returns True if an upgrade to software is required. 
    ***
    '''

    upgrade_required = False

    if current_version == upgrade_version:
        print("\n *update* Software upgrade IS NOT required \n")
    else:
        print("\n *update* Software upgrade IS required \n")
        upgrade_required = True

    return upgrade_required


def check_file_exists(file, file_system='flash:/'):
   
    '''
    ***
        DESCRIPTION:
                The function imports a file Object and an optional "file system path" parameter, and  returns a boolean as to answer the question "Does the file exist at the given path?" If an unexpected problem occurs while checking the file, an error statement is raised. 
        
        INPUT PARAMETERS:
               file (Object), file_system (string) [Default = 'flash:/']: Imports a file Object and an optional string parameter containing the file system path, which has a default value of 'flash:/', in this order.  

        RETURNS:
                file_exists (boolean): Returns False if the file does not exist at the given file path, or returns True if the file does exist at the file path. 
    ***
    '''

    file_exists = False

    print('*update* Checking to see if %s is in %s \n') % (file, file_system)
    dir_check = 'dir ' + file_system + file
    results = cli(dir_check)

    if 'No such file or directory' in results:
        print('*update*  %s does NOT exist on %s \n' % (file, file_system))
    elif 'Directory of %s%s' % (file_system, file) in results:
        print('*update* %s DOES exist on %s \n') % (file, file_system)
        file_exists = True
    else:
        raise ValueError("#ERROR# Unexpected output from check_file_exists #ERROR#\n")

    return file_exists 


def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
   
    '''
    ***
        DESCRIPTION:
                The function imports a binary disk image file, a MD5 checksum and an optional "file system path" parameter, and returns a boolean as to answer the question "Does the import MD5 checksum match with the MD5 checksum produced from the file in the filepath?" 
        
        INPUT PARAMETERS:
               image (string), src_md5 (string), file_system (string) [Default = 'flash:/']: Imports a binary disk image file, a MD5 32-character checksum and an optional string parameter containing the file system path, which has a default value of 'flash:/', in this order.  

        RETURNS:
                md5_match (boolean): Returns False if the source (import) MD5 checksum does not match with the MD5 checksum produced by the file in the filepath, or returns True if the MD5 checksums of the import and the one produced do match. 
    ***
    '''

    md5_match = False

    verify_md5 = 'verify /md5 ' + file_system + image
    dst_md5 = cli(verify_md5)

    if src_md5 in dst_md5:
        print('*update* MD5 hashes DO match \n')
        md5_match = True
    else:
        print('*update* MD5 hashes DO NOT match \n')

    return md5_match


def file_transfer(tftp_server, file, file_system='flash:/'):
    
    '''
    ***
        DESCRIPTION:
                Using a tftp server IP address, a file Object and an optional "file system path" parameter, the function transfers a file from the tftp server to the destination file system path. If an unexpected problem occurs while transferring the file, an error statement is raised. 
        
        INPUT PARAMETERS:
               tftp_server (string), file (Object), file_system (string) [Default = 'flash:/']: Imports a tftp server IP address, a file Object and an optional string parameter containing the file system path, which has a default value of 'flash:/', in this order.  

        RETURNS:
                No return statement.           
    ***
    '''

    destination = file_system + file
    commands = ['file prompt quiet',
                'ip tftp blocksize 1468',
                'ip tftp source-interface vlan 1'
               ]
    results = configure(commands)
    print('*update* Successfully set "file prompt quiet" on switch \n')
    # Next two lines offer transfer options - one MUST be commented out
    transfer_file = "copy tftp://%s/%s %s" % (tftp_server, file, destination) 
#    transfer_file = "copy http://%s:8080/%s %s" % (tftp_server, file, destination) 
    print('*update* Transferring %s to %s \n' % (file, file_system))
    transfer_results = cli(transfer_file)
    if 'OK' in transfer_results:
        print('*update* %s was transferred successfully!!! \n' % (file))
    elif 'Error opening' in transfer_results:
        raise ValueError("#ERROR# Error in file transfer #ERROR#\n")


def delete_failed_file(img_cat9k):

    '''
    ***
        DESCRIPTION:
                The function imports a binary disk image file and deletes this respective file.  
        
        INPUT PARAMETERS:
               img_cat9k (string): Imports a string of a binary disk image file.  

        RETURNS:
                No return statement.           
    ***
    '''

    print('\n*update* deleting flash:/{} \n'.format(img_cat9k))
    cli('delete flash:/{}'.format(img_cat9k))


def deploy_eem_upgrade_script(image):
    
    '''
    ***
        DESCRIPTION:
                The function imports a binary disk image file and configuresseveral commands to the Embedded Event Manager (EEM) in the device to activate the Software Maintenance Updates (SMU) packages, which is a prerequisite to an upgrade of a device; i.e. functions deploys the EEM upgrade script, which is required to trigger the upgrade.
        
        INPUT PARAMETERS:
               image (string): Imports a string of a binary disk image file.  
        RETURNS:
                No return statement.           
    ***
    '''

    print('*update* Configuring EEM upgrade script \n')
    install_command = 'install add file flash:' + image + ' activate commit'
    eem_commands = ['event manager applet upgrade',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\/q\]"' % install_command,
                    'action 2.1 cli command "n" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configure(eem_commands)
    print('*update* Successfully configured upgrade EEM script \n')


def do_upgrade():

    '''
    ***
        DESCRIPTION:
                The function triggers the upgrade of the device, which performs the upgrade of the software version.  
        
        INPUT PARAMETERS:
                No input parameters. 

        RETURNS:
                No return statement.           
    ***
    '''

    print('*update* Upgrade triggered - switch will reboot now \n')
    cli('event manager run upgrade')
    time.sleep(600)


def deploy_eem_cleanup_script():

	'''
    ***
        DESCRIPTION:
                The function configures several commands to the Embedded Event Manager (EEM) to "clean" the device. This is a prerequisite to triggering the cleanup procedure of removing inactive binary disk image files.
        
        INPUT PARAMETERS:
             	No input parameters.  

        RETURNS:
                No return statement.           
    ***
    '''

	print('*update* Configuring cleanup EEM Script \n')
	install_command = 'install remove inactive'
	eem_commands = ['event manager applet cleanup',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\]"' % install_command,
                    'action 2.1 cli command "y" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
	results = configure(eem_commands)
	print('*update* Successfully configured cleanup EEM script \n')


def do_cleanup():
    
	'''
    ***
        DESCRIPTION:
                The function triggers the cleanup of the device which removes inactive disk image files.  
        
        INPUT PARAMETERS:
                No input parameters. 

        RETURNS:
                No return statement.           
    ***
    '''

	cli('event manager run cleanup')
	time.sleep(30)
    

def apply_stack_numbering(stack_number):
    '''
    ***
        DESCRIPTION:
                The function imports a stack number. If the device's current stack number is different to the import, then the function renumbers it to the new import stack number, otherwise if it is the same, then no update is necessary.  
        
        INPUT PARAMETERS:
                stack_number (string): Inputs a string representing a stack number from "1" to "16".

        RETURNS:
                No return statement.           
    ***
    '''
    priority = 16 - int(stack_number)
    switch = execute('show switch')
    match = re.findall(r'(\d)\s+\S+\s+\S+\s+(\d+)', switch)
    if stack_number != match[0][0]:
        try:
            configure('switch {} renumber {}'.format(match[0][0], stack_number))
            configure('switch {} priority {}'.format(stack_number, priority))
            print('*update* Configured switch from {} to {}\n'.format(match[0][0], stack_number))
            print('*update* Reloading to apply switch stack config \n')
            execute('reload')
        except Exception as e:
            #execute('hw-module beacon slot %d on' % int(match[0][0]))
            #raise ValueError('#ERROR# Failed to change switch stack number or priority #ERROR#\n')
            print('*update* Switch stack number doesn\'t need updating \n')
    else:
        print('*update* Switch stack number doesn\'t need updating \n')


def do_save():
    
	'''
    ***
        DESCRIPTION:
                The function saves the running configurations.  
        
        INPUT PARAMETERS:
                No input parameters. 

        RETURNS:
                No return statement.           
    ***
    '''

	print("*update* Writing to memory \n")
	execute("write memory")


def show_commands():

	'''
    ***
        DESCRIPTION:
                The function shows the summary of various configurations (configs), which are: ssh configs, interface configs, DHCP configs, version details and install summary.  
        
        INPUT PARAMETERS:
                No input parameters. 

        RETURNS:
                No return statement.           
    ***
    '''

	show_cmds = [
    "show ip ssh",
    "show ip interface brief",
    "show dhcp lease",
    "show version",
    "show install summary"
    ]
	for show_cmd in show_cmds:
		print('Running :{}\n'.format(show_cmd))
		executep(show_cmd)


if __name__ == "__main__":
    print("\n**START** ZTP Day0 Python Script Start **START** \n")

    device_map = {}

    serial_number = get_serial_num()
    device_map = get_device_map(serial_number)
    staging_ip, upgrade_version, stack_number, hostname, vl69ip = get_device_values(serial_number)
    apply_base_config(staging_ip, hostname, vl69ip)

    current_version = get_sw_version()
    if upgrade_sw_version(current_version, upgrade_version):
        if check_file_exists(img_cat9k):
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                delete_failed_file(img_cat9k)
                raise ValueError('#ERROR# Existing file failed Md5sum #ERROR#\n')
        else:
            file_transfer(tftp_server, img_cat9k)
            if not verify_dst_image_md5(img_cat9k, img_cat9k_md5):
                delete_failed_file(img_cat9k)
                raise ValueError('#ERROR# Failed Xfer and MD5sum #ERROR#\n')

        deploy_eem_upgrade_script(img_cat9k)
        do_upgrade()
    else:
        print('*update* Verison is correct, no upgrade is required \n')
        deploy_eem_cleanup_script()
        do_cleanup()

    apply_stack_numbering(stack_number)

    do_save()

    show_commands()

    print("\n **FINISH** ZTP Day0 Python Script Finished **FINISH** \n")

