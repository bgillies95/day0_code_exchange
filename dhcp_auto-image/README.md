
# Staging Infrastructure Switch DHCP and TFTP configuration

## Switch configuration 

### VLAN SVI

    interface Vlan3
      ip address 10.100.103.254 255.255.255.0

    interface VLAN69
    ip address 10.198.104.254 255.255.255.0 secondary
    ip address 10.216.176.254 255.255.255.0 secondary
    ip address 10.216.128.254 255.255.255.0 secondary
    ip address 10.216.168.254 255.255.255.0 secondary
    ip address 10.198.96.254 255.255.255.0 secondary
    ip address 10.216.162.126 255.255.255.0 secondary
    ip address 10.198.72.254 255.255.255.0 secondary
    ip address 10.46.24.254 255.255.255.0 secondary
    ip address 10.100.106.254 255.255.255.0 



### DHCP configuration


Create a DHCP pool on the core switch infsw for the IOS devices. This need to be a separate VLAN from 
the IOS_XE devices and see the device through the image load and initial config push.

    ip dhcp pool VLAN3_IOS15.2(7)E2
     network 10.100.103.0 255.255.255.0
     bootfile config-boot.txt
     default-router 10.100.103.254
     option 150 ip 10.100.101.3
     option 125 hex 00:00:00:09:0B:05:09:61:75:74:6f:69:6e:73:74:61 # parses to a file named 'autoinsta'


The VLAN 69 DHCP pool is SITE SPECIFIC CONFIGURATION. The network and default router lines will need 
to be adjusted to suit the site. Here is an example for Brockman2:

    ip dhcp vlan69
     network 10.198.104.0 255.255.255.0
     bootfile config-boot.txt
     default-router 10.198.104.254
     option 150 ip 10.198.33.41
     option 125 hex 0000.0009.0b05.0961.7574.6f69.6e73.7461



### config-boot.txt

This is the config that will be applied to the switch to allow the automation scripting to connect and test the hardware, and load the final config.
A reference file is provided [here](config-boot.txt).

This file contains SITE SPECIFIC CONFIGURATION. The following lines will need to be adjusted to suit the site at a minimum:

    ip default-gateway 10.198.104.254
    ntp server 10.198.104.254 prefer
    vtp domain brockman
    vtp mode client
    vtp password brironore
    vtp version 2
    snmp-server location [BUILDING, <site name>, AU]
    ip access-list standard VTYACCESS
     permit 10.198.104.0 0.0.0.255
    


### autoinsta

This file containes the location and filename of the image to be loaded. As you can see from the [reference](autoinsta), its simply a leading slash and image name. THis must be a .tar file.

### trunks to other ASW

As we need different VLANS for IOS and IOS_XE devices, the links from the core switch 'infsw' to the top-of-rack switch will need to be
configured mode trunk. This config will also apply to For example:

    int Gi1/0/1
    switchport mode trunk

### ASW config

Other than a matching interface uplinking between the core and top-of-rack switches, ASW port drops will need to be configured to access one of two vlans depending if the device is IOS or IOS_XE. Because we have 24+ port switches and 12 devices per rack, that means 12x interfaces can be one vlan, and 12x interface an altenrate vlan.

    interface range gi1/0/1 - 12
     switchport trunk native vlan 3
     switchport mode trunk
     switchport nonegotiate
     spanning-tree bpdufilter enable
     spanning-tree bpduguard enable


## tftpd configuration

This tftp server configuration does not change from ZTP. 

Install and configure

    sudo apt update && sudo apt install tftpd-hpa

Set tftpd options

    TFTP_DIRECTORY="/srv/tftp"
    TFTP_OPTIONS="--secure --create -B 1468"

Start the service

    sudo systemctl enable --now tftpd-hpa
    
Set disk permissions

    sudo chown -R tftp:tftp /srv/tftp/
    sudo chmod 664 /srv/tftp/*
    sudo adduser -aG tftp <usernames>

