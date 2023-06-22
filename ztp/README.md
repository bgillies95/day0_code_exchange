
# Staging Infrastructure Switch DHCP and TFTP configuration


## Switch configuration

As the ZTP DHCP server has conflicting options to that of DHCP Autoconfiguration we put the ZTP devices on a separate VLAN. The L3 interface on core switch 'infsw' is:

    interface Vlan4_IOS-XE
     ip address 10.100.104 255.255.254.0
     no shutdown

The TOR switches need both access into VLAN 4 for the provisioning stage, and trunked connecitvity into VLAN 69 for the FAT and configuration stage.

    interface range gi1/0/13 - 24
     switchport trunk native vlan 4
     switchport mode trunk
     switchport nonegotiate
     spanning-tree bpdufilter enable
     spanning-tree bpduguard enable


### DHCP 

The ZTP process requires a separate DHCP pool from the DHCP auto-installation DHCP pool. You'll note that the options "bootfile" and "option 125" are absent from the pool declaration below. If they are present the IOS_XE will fall back to the DHCP aut-installation process and not follow the ZTP process. 

    ip dhcp pool ZTP                
     network 10.100.104.0 255.255.254.0
     default-router 10.100.105.254
     option 150 ip 10.198.33.41
     option 67 ascii http://10.198.33.41:8080/ztp.py        

Note that when the option 67 is applied the switch inserts quotation marks around the file name. If applying the config from a backup, avoid duplicating these quotation marks.

## Server

In addition to the TTP server detailed in the DHCP auto-image process, devbox runs docker containers to server information to the switch being provisioned.


### ztp.py - serve_ztp

The container is a simple nginx http server image with the ztp.py file bound to the root of the webserver. The nginx http server opens port 8080 and listens for requests from the device. 

When the container is running on the devbox, you can test it by opening the URL [http://10.198.33.41:8080/ztp.py](http://10.198.33.41:8080/ztp.py)



### device_map - serve_devicemap

The container is a slim variant of Debian Bullseye with uWSGI running the webapp directly. The webapp reads in the data.csv on load and opens port 8081 and listens for GET requests that reference the device serial number. 

When the ztp script is loaded and running on the device, it makes that http GET call to the devbox to retireve the configuration details. The response is a JSON string with the devices serian number as key:

    {"4BYIA31BCY2":{"sw":"16.12.05b", "ip":"10.100.103.4", "s_id":"1"}}

When the container is running on the devbox, you can test it by opening  [http://10.198.33.41:8081/?device_id=K1GJT31X38M](http://10.198.33.41:8081/?device_id=K1GJT31X38M), where the device_id equals the device serial number listed in data.csv


Each time the data.csv has been updated  it can be saved to the /srv/data/ folder and the docker-compose script used to restart the containers

To bring the containers up:

    docker-compose up -d

To ear the containers down, pass the --rmi flag to ensure the images are rebuilt and incorporate the current code revision:

    docker-compose down


### tacacs+ 

See [github.dxc.com:kjenner/rio_fat_tacacs](github.dxc.com:kjenner/rio_fat_tacacs)
### Notes

- the installer will need to run `default interface gi0/0` during comissioning



### Example

The following is and example of the process. You can see it took just 3 minutes to download and build the three fresh images. 

    13:30:ztp$ docker-compose down --rmi all
    [+] Running 7/7
    ⠿ Container ztp-serve_ztp-1        Removed                   0.5s
    ⠿ Container ztp-serve_devicemap-1  Removed                  10.4s
    ⠿ Container ztp-test_devicemap-1   Removed                   0.0s
    ⠿ Image ztp_serve_ztp              Removed                   0.0s
    ⠿ Image ztp_serve_devicemap        Removed                   0.0s
    ⠿ Network ztp_default              Removed                   0.2s
    ⠿ Image ztp_test_devicemap         Removed                   0.0s

    13:25:ztp$ docker-compose up -d
    [+] Building 179.6s (10/10) FINISHED
    => [internal] load build definition from Dockerfile                                                                   0.0s
    => => transferring dockerfile: 290B                                                                                   0.0s
    => [internal] load .dockerignore                                                                                      0.0s
    => => transferring context: 2B                                                                                        0.0s
    => [internal] load metadata for docker.io/library/ubuntu:18.04                                                       12.6s
    => [auth] library/ubuntu:pull token for registry-1.docker.io                                                          0.0s
    => [internal] load build context                                                                                      0.0s
    => => transferring context: 1.12kB                                                                                    0.0s
    => [1/4] FROM docker.io/library/ubuntu:18.04@sha256:d21b6ba9e19feffa328cb3864316e6918e30acfd55e285b5d3df1d8ca3c7fd3f  0.0s
    => CACHED [2/4] WORKDIR /usr/src/app                                                                                  0.0s
    => [3/4] COPY ./test_ztp.py ./                                                                                        0.0s
    => [4/4] RUN DEBIAN_FRONTEND=noninteractive apt update && apt -yq upgrade && apt install -yq --no-install-recommends python python-requests curl && rm -rf /var/lib/apt/li  166.5s
    => exporting to image                                                                                                                                                         0.4s
    => => exporting layers                                                                                                                                                        0.4s
    => => writing image sha256:ff2c95e3c4565b1177e3c1b4245210ee0cb0277002cdc401182ea3fbffd86e0c                           0.0s
    => => naming to docker.io/library/ztp_test_devicemap                                                                  0.0s
    [+] Running 3/3
    ⠿ Container ztp-test_devicemap-1   Started                                                                            0.5s
    ⠿ Container ztp-serve_devicemap-1  Running                                                                            0.0s
    ⠿ Container ztp-serve_ztp-1        Running                                                                            0.0s


## References

[Cisco Programmability ZTP section](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/173/b_173_programmability_cg/zero_touch_provisioning.html#Cisco_Reference.dita_06865c21-2890-41f7-be09-dd92968570e3)

[Jeremy Cohoe](https://github.com/jeremycohoe/IOSXE-Zero-Touch-Provisioning)

[https://docs.docker.com/](https://docs.docker.com/) 

## ZTP Process Trace

Now outdated... to be updated.

    ZTP-FCW2320G04M#sh install summary 
    [ Switch 1 ] Installed Package(s) Information:
    State (St): I - Inactive, U - Activated & Uncommitted,
                C - Activated & Committed, D - Deactivated & Uncommitted
    -------------------------------------------------------------------------------
    -Type  St   Filename/Version    
    -------------------------------------------------------------------------------
    -IMG   C    16.12.3.0.3752                                                      
    
    -------------------------------------------------------------------------------
    -Auto abort timer: inactive
    -------------------------------------------------------------------------------
    -
    ZTP-FCW2320G04M#sh 
    *Apr 30 03:30:03.510: %CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discove
    rCisco IOS XE Software, Version 16.12.03
    Cisco IOS Software [Gibraltar], Catalyst L3 Switch Software (CAT9K_IOSXE), Vers
    )Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2020 by Cisco Systems, Inc.
    Compiled Mon 09-Mar-20 22:02 by mcpre
    
    
    Cisco IOS-XE software, Copyright (c) 2005-2020 by cisco Systems, Inc.
    All rights reserved.  Certain components of Cisco IOS-XE software are
    licensed under the GNU General Public License ("GPL") Version 2.0.  The
    software code licensed under GPL Version 2.0 is free software that comes
    with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
    GPL code under the terms of GPL Version 2.0.  For more details, see the
    documentation or "License Notice" file accompanying the IOS-XE software,
    or the applicable URL provided on the flyer accompanying the IOS-XE
    software.
    
    
    ROM: IOS-XE ROMMON
    BOOTLDR: System Bootstrap, Version 16.12.2r, RELEASE SOFTWARE (P)
    
    ZTP-FCW2320G04M uptime is 26 minutes
    --More--         
    Uptime for this control processor is 27 minutes
    System returned to ROM by Reload Command
    System image file is "flash:packages.conf"
    Last reload reason: Reload Command
    
    
    
    This product contains cryptographic features and is subject to United
    States and local country laws governing import, export, transfer and
    use. Delivery of Cisco cryptographic products does not imply
    third-party authority to import, export, distribute or use encryption.
    Importers, exporters, distributors and users are responsible for
    compliance with U.S. and local country laws. By using this product you
    agree to comply with applicable laws and regulations. If you are unable
    to comply with U.S. and local laws, return this product immediately.
    
    A summary of U.S. laws governing Cisco cryptographic products may be found at:
    http://www.cisco.com/wwl/export/crypto/tool/stqrg.html
    
    If you require further assistance please contact us by sending email to
    export@cisco.com.
    
    
    --More--         
    Technology Package License Information: 
    
    ------------------------------------------------------------------------------
    Technology-package                                     Technology-package
    Current                        Type                       Next reboot  
    ------------------------------------------------------------------------------
    network-advantage   Smart License                  network-advantage   
    dna-essentials      Subscription Smart License     dna-essentials        
    AIR License Level: AIR DNA Advantage
    Next reload AIR license Level: AIR DNA Advantage
    
    
    Smart Licensing Status: UNREGISTERED/EVAL EXPIRED
    
    cisco C9300-24U (X86) processor with 1343703K/6147K bytes of memory.
    Processor board ID FCW2320G04M
    1 Virtual Ethernet interface
    28 Gigabit Ethernet interfaces
    8 Ten Gigabit Ethernet interfaces
    2 TwentyFive Gigabit Ethernet interfaces
    2 Forty Gigabit Ethernet interfaces
    2048K bytes of non-volatile configuration memory.
    --More--         
    8388608K bytes of physical memory.
    1638400K bytes of Crash Files at crashinfo:.
    11264000K bytes of Flash at flash:.
    0K bytes of WebUI ODM Files at webui:.
    117219783K bytes of USB Flash at usbflash1:.
    
    Base Ethernet MAC Address          : 6c:5e:3b:23:c6:00
    Motherboard Assembly Number        : 73-18272-03
    Motherboard Serial Number          : FOC23180Y8F
    Model Revision Number              : A0
    Motherboard Revision Number        : A0
    Model Number                       : C9300-24U
    System Serial Number               : FCW2320G04M
    
    
    Switch Ports Model              SW Version        SW Image              Mode   
    ------ ----- -----              ----------        ----------            ----   
    *    1 41    C9300-24U          16.12.3           CAT9K_IOSXE           INSTALL
    
    
    Configuration register is 0x102
    
    ZTP-FCW2320G04M#wr erase
    Erasing the nvram filesystem will remove all configuration files! Continue? [co
    ]Erase of nvram: complete
    ZTP-FCW2320G04M#
    *Apr 30 03:30:20.579: %SYS-7-NV_BLOCK_INIT: Initialized the geometry of nvramre
    d
    System configuration has been modified. Save? [yes/no]: 
    *Apr 30 03:30:24.519: %SYS-5-CONFIG_P: Configured programmatically by process E
    nReload command is being issued on Active unit, this will reload the whole stack
    Proceed with reload? [confirm]
    *Apr 30 03:30:54.116: %CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discove
    y*Apr 30 03:30:59.228: %SYS-5-RELOAD: Reload requested by console. Reload Reason
    .Chassis 1 reloading, reason - Reload command
    reload fp action requested
    process exit with reload stack code
    
    
    
    Initializing Hardware...
    
    System Bootstrap, Version 16.12.2r, RELEASE SOFTWARE (P)
    Compiled Wed 10/23/2019 16:35:17.50 by rel
    
    Current ROMMON image : Primary
    Last reset cause     : SoftwareReload
    C9300-24U platform with 8388608 Kbytes of main memory
    
    boot: attempting to boot from [flash:packages.conf]
    boot: reading file packages.conf
    #
    ###############################################################################
    #
    
    %IOSXEBOOT-4-SMART_LOG: (local/local): Sat Apr 30 03:32:59 Universal 2022 INFO:
    n
    Both links down, not waiting for other switches
    Switch number is 1
    
                Restricted Rights Legend
    
    Use, duplication, or disclosure by the Government is
    subject to restrictions as set forth in subparagraph
    (c) of the Commercial Computer Software - Restricted
    Rights clause at FAR sec. 52.227-19 and subparagraph
    (c) (1) (ii) of the Rights in Technical Data and Computer
    Software clause at DFARS sec. 252.227-7013.
    
                Cisco Systems, Inc.
                170 West Tasman Drive
                San Jose, California 95134-1706
    
    
    
    Cisco IOS Software [Gibraltar], Catalyst L3 Switch Software (CAT9K_IOSXE), Vers
    )Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2020 by Cisco Systems, Inc.
    Compiled Mon 09-Mar-20 22:02 by mcpre
    
    
    This software version supports only Smart Licensing as the software licensing m
    .
    
    PLEASE READ THE FOLLOWING TERMS CAREFULLY. INSTALLING THE LICENSE OR
    LICENSE KEY PROVIDED FOR ANY CISCO SOFTWARE PRODUCT, PRODUCT FEATURE,
    AND/OR SUBSEQUENTLY PROVIDED SOFTWARE FEATURES (COLLECTIVELY, THE
    "SOFTWARE"), AND/OR USING SUCH SOFTWARE CONSTITUTES YOUR FULL
    ACCEPTANCE OF THE FOLLOWING TERMS. YOU MUST NOT PROCEED FURTHER IF YOU
    ARE NOT WILLING TO BE BOUND BY ALL THE TERMS SET FORTH HEREIN.
    
    Your use of the Software is subject to the Cisco End User License Agreement
    (EULA) and any relevant supplemental terms (SEULA) found at
    http://www.cisco.com/c/en/us/about/legal/cloud-and-software/software-terms.html
    .
    You hereby acknowledge and agree that certain Software and/or features are
    licensed for a particular term, that the license to such Software and/or
    features is valid only for the applicable term and that such Software and/or
    features may be shut down or otherwise terminated by Cisco after expiration
    of the applicable license term (e.g., 90-day trial period). Cisco reserves
    the right to terminate any such Software feature electronically or by any
    other means available. While Cisco may provide alerts, it is your sole
    responsibility to monitor your usage of any such term Software feature to
    ensure that your systems and networks are prepared for a shutdown of the
    Software feature.
    
    
    % Checking backup nvram
    % No config present. Using default config
    
    FIPS: Flash Key Check : Key Not Found, FIPS Mode Not Enabled
    
    All TCP AO KDF Tests Pass
    cisco C9300-24U (X86) processor with 1343703K/6147K bytes of memory.
    Processor board ID FCW2320G04M
    2048K bytes of non-volatile configuration memory.
    8388608K bytes of physical memory.
    1638400K bytes of Crash Files at crashinfo:.
    11264000K bytes of Flash at flash:.
    0K bytes of WebUI ODM Files at webui:.
    
    Base Ethernet MAC Address          : 6c:5e:3b:23:c6:00
    Motherboard Assembly Number        : 73-18272-03
    Motherboard Serial Number          : FOC23180Y8F
    Model Revision Number              : A0
    Motherboard Revision Number        : A0
    Model Number                       : C9300-24U
    System Serial Number               : FCW2320G04M
    
    
    
            --- System Configuration Dialog ---
    
    Would you like to enter the initial configuration dialog? [yes/no]: 
    *Apr 30 03:32:32.161: %IOSXE-0-PLATFORM: Switch 1 R0/0: udev: usb1: has been in
    dLoading http://10.100.101.3:8080/ztp.py 
    Loading http://10.100.101.3:8080/ztp.py The process for the command is not resp
    eThe process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    day0guestshell installed successfully
    Current state is: DEPLOYED
    day0guestshell activated successfully
    Current state is: ACTIVATED
    day0guestshell started successfully
    Current state is: RUNNING
    Guestshell enabled successfully
    
    
    HTTP server statistics:
    Accepted connections total: 0
    
    **START** ZTP Day0 Python Script Start **START** 
    
    
    Line 1 SUCCESS: hostname ZTP-FCW2320G04M
    Line 2 SUCCESS: ip ssh version 2
    Line 3 SUCCESS: ip ssh logging events
    Line 4 SUCCESS: ip domain name lab
    Line 5 SUCCESS: ip route 0.0.0.0 0.0.0.0 10.100.105.254
    Line 6 SUCCESS: crypto key generate rsa modulus 2048
    **CLI Line # 6: The name for the keys will be: ZTP-FCW2320G04M.lab
    **CLI Line # 6: % The key modulus size is 2048 bits
    **CLI Line # 6: % Generating 2048 bit RSA keys, keys will be non-exportable...
    **CLI Line # 6: [OK] (elapsed time was 1 seconds)
    
    Line 7 SUCCESS: username cisco privilege 15 secret cisco
    Line 8 SUCCESS: enable secret cisco
    Line 9 SUCCESS: line vty 0 15
    Line 10 SUCCESS: login local
    Line 11 SUCCESS: transport input ssh
    Line 12 SUCCESS: interface vlan1
    Line 13 SUCCESS: no shutdown
    Line 14 SUCCESS: ip address 10.100.104.1 255.255.254.0
    
    *update* Software upgrade required *update*
    
    *update* Upgrade is required. Check file exists locally *update*
    
    *update* Checking to see if cat9k_iosxe.16.12.05b.SPA.bin is in flash:/ *update
    *
    *update* cat9k_iosxe.16.12.05b.SPA.bin DOES exist on flash:/ *update*
    
    *update* MD5 hashes match *update*
    
    *update* Deploying EEM upgrade script *update*
    *update* Successfully configured upgrade EEM script on device! *update*
    
    *update* Performing the upgrade - switch will reboot *update*
    
    %IOSXEBOOT-4-BOOTLOADER_UPGRADE: (local/local): Starting boot preupgrade
    MM [1] 
    9
    9
    
    
    !
    
    .
    o
    s
    s
    o
    
    .
    .
    .
    %
    .
    w
    !
    .
    .
    s
    
    
    .Chassis 1 reloading, reason - Reload command
    reload fp action requested
    rp processes exit with reload switch code
    
    
    
    Initializing Hardware...
    
    System Bootstrap, Version 16.12.2r, RELEASE SOFTWARE (P)
    Compiled Wed 10/23/2019 16:35:17.50 by rel
    
    Current ROMMON image : Primary
    Last reset cause     : SoftwareReload
    C9300-24U platform with 8388608 Kbytes of main memory
    
    boot: attempting to boot from [flash:packages.conf]
    boot: reading file packages.conf
    #
    ###############################################################################
    #
    
    %IOSXEBOOT-4-SMART_LOG: (local/local): Sat Apr 30 03:49:41 Universal 2022 INFO:
    n
    Both links down, not waiting for other switches
    Switch number is 1
    
                Restricted Rights Legend
    
    Use, duplication, or disclosure by the Government is
    subject to restrictions as set forth in subparagraph
    (c) of the Commercial Computer Software - Restricted
    Rights clause at FAR sec. 52.227-19 and subparagraph
    (c) (1) (ii) of the Rights in Technical Data and Computer
    Software clause at DFARS sec. 252.227-7013.
    
                Cisco Systems, Inc.
                170 West Tasman Drive
                San Jose, California 95134-1706
    
    
    
    Cisco IOS Software [Gibraltar], Catalyst L3 Switch Software (CAT9K_IOSXE), Vers
    )Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2021 by Cisco Systems, Inc.
    Compiled Thu 25-Mar-21 13:21 by mcpre
    
    
    This software version supports only Smart Licensing as the software licensing m
    .
    
    PLEASE READ THE FOLLOWING TERMS CAREFULLY. INSTALLING THE LICENSE OR
    LICENSE KEY PROVIDED FOR ANY CISCO SOFTWARE PRODUCT, PRODUCT FEATURE,
    AND/OR SUBSEQUENTLY PROVIDED SOFTWARE FEATURES (COLLECTIVELY, THE
    "SOFTWARE"), AND/OR USING SUCH SOFTWARE CONSTITUTES YOUR FULL
    ACCEPTANCE OF THE FOLLOWING TERMS. YOU MUST NOT PROCEED FURTHER IF YOU
    ARE NOT WILLING TO BE BOUND BY ALL THE TERMS SET FORTH HEREIN.
    
    Your use of the Software is subject to the Cisco End User License Agreement
    (EULA) and any relevant supplemental terms (SEULA) found at
    http://www.cisco.com/c/en/us/about/legal/cloud-and-software/software-terms.html
    .
    You hereby acknowledge and agree that certain Software and/or features are
    licensed for a particular term, that the license to such Software and/or
    features is valid only for the applicable term and that such Software and/or
    features may be shut down or otherwise terminated by Cisco after expiration
    of the applicable license term (e.g., 90-day trial period). Cisco reserves
    the right to terminate any such Software feature electronically or by any
    other means available. While Cisco may provide alerts, it is your sole
    responsibility to monitor your usage of any such term Software feature to
    ensure that your systems and networks are prepared for a shutdown of the
    Software feature.
    
    
    % Checking backup nvram
    % No config present. Using default config
    
    FIPS: Flash Key Check : Key Not Found, FIPS Mode Not Enabled
    
    All TCP AO KDF Tests Pass
    cisco C9300-24U (X86) processor with 1343489K/6147K bytes of memory.
    Processor board ID FCW2320G04M
    2048K bytes of non-volatile configuration memory.
    8388608K bytes of physical memory.
    1638400K bytes of Crash Files at crashinfo:.
    11264000K bytes of Flash at flash:.
    0K bytes of WebUI ODM Files at webui:.
    
    Base Ethernet MAC Address          : 6c:5e:3b:23:c6:00
    Motherboard Assembly Number        : 73-18272-03
    Motherboard Serial Number          : FOC23180Y8F
    Model Revision Number              : A0
    Motherboard Revision Number        : A0
    Model Number                       : C9300-24U
    System Serial Number               : FCW2320G04M
    
    
    
            --- System Configuration Dialog ---
    
    Would you like to enter the initial configuration dialog? [yes/no]: 
    *Apr 30 03:49:14.816: %IOSXE-0-PLATFORM: Switch 1 R0/0: udev: usb1: has been in
    dLoading http://10.100.101.3:8080/ztp.py 
    Loading http://10.100.101.3:8080/ztp.py The process for the command is not resp
    eThe process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    The process for the command is not responding or is otherwise unavailable
    day0guestshell installed successfully
    Current state is: DEPLOYED
    day0guestshell activated successfully
    Current state is: ACTIVATED
    day0guestshell started successfully
    Current state is: RUNNING
    Guestshell enabled successfully
    
    
    HTTP server statistics:
    Accepted connections total: 0
    
    **START** ZTP Day0 Python Script Start **START** 
    
    
    Line 1 SUCCESS: hostname ZTP-FCW2320G04M
    Line 2 SUCCESS: ip ssh version 2
    Line 3 SUCCESS: ip ssh logging events
    Line 4 SUCCESS: ip domain name lab
    Line 5 SUCCESS: ip route 0.0.0.0 0.0.0.0 10.100.105.254
    Line 6 SUCCESS: crypto key generate rsa modulus 2048
    **CLI Line # 6: The name for the keys will be: ZTP-FCW2320G04M.lab
    **CLI Line # 6: % The key modulus size is 2048 bits
    **CLI Line # 6: % Generating 2048 bit RSA keys, keys will be non-exportable...
    **CLI Line # 6: [OK] (elapsed time was 2 seconds)
    
    Line 7 SUCCESS: username cisco privilege 15 secret cisco
    Line 8 SUCCESS: enable secret cisco
    Line 9 SUCCESS: line vty 0 15
    Line 10 SUCCESS: login local
    Line 11 SUCCESS: transport input ssh
    Line 12 SUCCESS: interface vlan1
    Line 13 SUCCESS: no shutdown
    Line 14 SUCCESS: ip address 10.100.104.1 255.255.254.0
    
    *update* No software upgrade required *update*
    
    *update* No upgrade is required!!! *update*
    
    *update* Deploying Cleanup EEM Script *update*
    
    *update* Successfully configured cleanup EEM script on device! *update*
    
    *update* Running Cleanup EEM Script *update*
    
    SSH Enabled - version 2.0
    Authentication methods:publickey,keyboard-interactive,password
    Authentication Publickey Algorithms:x509v3-ssh-rsa,ssh-rsa
    Hostkey Algorithms:x509v3-ssh-rsa,ssh-rsa
    Encryption Algorithms:aes128-ctr,aes192-ctr,aes256-ctr
    MAC Algorithms:hmac-sha2-256,hmac-sha2-512,hmac-sha1,hmac-sha1-96
    KEX Algorithms:diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1
    Authentication timeout: 120 secs; Authentication retries: 3
    Minimum expected Diffie Hellman key size : 2048 bits
    IOS Keys in SECSH format(ssh-rsa, base64 encoded): ZTP-FCW2320G04M.lab
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCmsRcp8z6O5YldSVoxm9Wj463CK2k0atVZsdgfhpa
    ThtUQnqwJVYTEikKZWNNi5CXGLDu08rHKjxkyLfTiFuhy+FbR+GMyE69eI+9dwWb+5f0gV7SsyHce2Ru
    /DAyNdLgjujYeqkrcjeMSuGb2N2A5hisGS3hewh8KieNcjMVIc/pd9Gg9SwEX/++1QRio8Bh/K2yR+ga
    WGeyoaHflLK22eUD1O0BSKoT/ovRsiiEo1czvmWFzRHLanu9dNbcdVKRya7cM2SMenXEqyQtkzuXzV04
    LJvR84xQ54b1SiXoNyqgCaXJ6BmvoHie7tJ7ViLoIAiXVV3eDgfI8hlgKekvF                   
    Interface              IP-Address      OK? Method Status                Protoco
    lVlan1                  10.100.104.1    YES TFTP   up                    up     
    Vlan4094               192.168.2.1     YES manual up                    up     
    GigabitEthernet0/0     unassigned      YES unset  down                  down   
    GigabitEthernet1/0/1   unassigned      YES unset  up                    up     
    GigabitEthernet1/0/2   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/3   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/4   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/5   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/6   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/7   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/8   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/9   unassigned      YES unset  down                  down   
    GigabitEthernet1/0/10  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/11  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/12  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/13  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/14  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/15  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/16  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/17  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/18  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/19  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/20  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/21  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/22  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/23  unassigned      YES unset  down                  down   
    GigabitEthernet1/0/24  unassigned      YES unset  down                  down   
    GigabitEthernet1/1/1   unassigned      YES unset  down                  down   
    GigabitEthernet1/1/2   unassigned      YES unset  down                  down   
    GigabitEthernet1/1/3   unassigned      YES unset  down                  down   
    GigabitEthernet1/1/4   unassigned      YES unset  down                  down   
    Te1/1/1                unassigned      YES unset  down                  down   
    Te1/1/2                unassigned      YES unset  down                  down   
    Te1/1/3                unassigned      YES unset  down                  down   
    Te1/1/4                unassigned      YES unset  down                  down   
    Te1/1/5                unassigned      YES unset  down                  down   
    Te1/1/6                unassigned      YES unset  down                  down   
    Te1/1/7                unassigned      YES unset  down                  down   
    Te1/1/8                unassigned      YES unset  down                  down   
    Fo1/1/1                unassigned      YES unset  down                  down   
    Fo1/1/2                unassigned      YES unset  down                  down   
    TwentyFiveGigE1/1/1    unassigned      YES unset  down                  down   
    TwentyFiveGigE1/1/2    unassigned      YES unset  down                  down   
    Ap1/0/1                unassigned      YES unset  up                    up     
    'NoneType' object has no attribute 'attrib'
    *update* Wrote to memory *update*
    
    **FINISH** ZTP Day0 Python Script Finished **FINISH** 
    
    
    Guestshell destroyed successfully 
    
    
    
    Press RETURN to get started!
    
    
    *Apr 30 03:55:10.396: %CRYPTO_ENGINE-5-KEY_ADDITION: A key named TP-self-signed
    e*Apr 30 03:55:10.446: %PKI-4-NOCONFIGAUTOSAVE: Configuration was modified.  Iss
    n*Apr 30 03:55:10.447: %SYS-5-CONFIG_P: Configured programmatically by process D
    0*Apr 30 03:55:11.201: %SYS-5-CONFIG_P: Configured programmatically by process P
    0*Apr 30 03:55:12.209: %SYS-5-CONFIG_P: Configured programmatically by process P
    0*Apr 30 03:55:13.224: %SYS-5-CONFIG_P: Configured programmatically by process P
    0*Apr 30 03:55:20.304: %SYS-5-CONFIG_P: Configured programmatically by process P
    0*Apr 30 03:55:21.306: %PNP-6-PNP_TECH_SUMMARY_SAVED_OK: PnP tech summary (pnp-t
    .*Apr 30 03:55:21.306: %PNP-6-PNP_DISCOVERY_STOPPED: PnP Discovery stopped (Conf
    )*Apr 30 03:55:59.796: %INSTALL-5-INSTALL_COMPLETED_INFO: Switch 1 R0/0: install

    .ZTP-FCW2320G04M>en
    Password: 
    ZTP-FCW2320G04M#conf t
    Enter configuration commands, one per line.  End with CNTL/Z.
    ZTP-FCW2320G04M(config)#no logg con
    ZTP-FCW2320G04M(config)#end
    ZTP-FCW2320G04M#sh ver
    Cisco IOS XE Software, Version 16.12.05b
    Cisco IOS Software [Gibraltar], Catalyst L3 Switch Software (CAT9K_IOSXE), Vers
    )Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2021 by Cisco Systems, Inc.
    Compiled Thu 25-Mar-21 13:21 by mcpre
    
    
    Cisco IOS-XE software, Copyright (c) 2005-2021 by cisco Systems, Inc.
    All rights reserved.  Certain components of Cisco IOS-XE software are
    licensed under the GNU General Public License ("GPL") Version 2.0.  The
    software code licensed under GPL Version 2.0 is free software that comes
    with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
    GPL code under the terms of GPL Version 2.0.  For more details, see the
    documentation or "License Notice" file accompanying the IOS-XE software,
    or the applicable URL provided on the flyer accompanying the IOS-XE
    software.
    
    
    ROM: IOS-XE ROMMON
    BOOTLDR: System Bootstrap, Version 16.12.2r, RELEASE SOFTWARE (P)
    
    ZTP-FCW2320G04M uptime is 10 minutes
    --More--         
    Uptime for this control processor is 11 minutes
    System returned to ROM by Image Install
    System image file is "flash:packages.conf"
    Last reload reason: Image Install
    
    
    
    This product contains cryptographic features and is subject to United
    States and local country laws governing import, export, transfer and
    use. Delivery of Cisco cryptographic products does not imply
    third-party authority to import, export, distribute or use encryption.
    Importers, exporters, distributors and users are responsible for
    compliance with U.S. and local country laws. By using this product you
    agree to comply with applicable laws and regulations. If you are unable
    to comply with U.S. and local laws, return this product immediately.
    
    A summary of U.S. laws governing Cisco cryptographic products may be found at:
    http://www.cisco.com/wwl/export/crypto/tool/stqrg.html
    
    If you require further assistance please contact us by sending email to
    export@cisco.com.
    
    
    --More--         
    Technology Package License Information: 
    
    ------------------------------------------------------------------------------
    Technology-package                                     Technology-package
    Current                        Type                       Next reboot  
    ------------------------------------------------------------------------------
    network-advantage   Smart License                  network-advantage   
    dna-essentials      Subscription Smart License     dna-essentials        
    AIR License Level: AIR DNA Advantage
    Next reload AIR license Level: AIR DNA Advantage
    
    
    Smart Licensing Status: UNREGISTERED/EVAL EXPIRED
    
    cisco C9300-24U (X86) processor with 1343489K/6147K bytes of memory.
    Processor board ID FCW2320G04M
    1 Virtual Ethernet interface
    28 Gigabit Ethernet interfaces
    8 Ten Gigabit Ethernet interfaces
    2 TwentyFive Gigabit Ethernet interfaces
    2 Forty Gigabit Ethernet interfaces
    2048K bytes of non-volatile configuration memory.
    --More--         
    8388608K bytes of physical memory.
    1638400K bytes of Crash Files at crashinfo:.
    11264000K bytes of Flash at flash:.
    0K bytes of WebUI ODM Files at webui:.
    117219783K bytes of USB Flash at usbflash1:.
    
    Base Ethernet MAC Address          : 6c:5e:3b:23:c6:00
    Motherboard Assembly Number        : 73-18272-03
    Motherboard Serial Number          : FOC23180Y8F
    Model Revision Number              : A0
    Motherboard Revision Number        : A0
    Model Number                       : C9300-24U
    System Serial Number               : FCW2320G04M
    
    
    Switch Ports Model              SW Version        SW Image              Mode   
    ------ ----- -----              ----------        ----------            ----   
    *    1 41    C9300-24U          16.12.05b         CAT9K_IOSXE           INSTALL
    
    
    Configuration register is 0x102
    
    ZTP-FCW2320G04M#sh inst
    ZTP-FCW2320G04M#sh install sum
    ZTP-FCW2320G04M#sh install summary 
    [ Switch 1 ] Installed Package(s) Information:
    State (St): I - Inactive, U - Activated & Uncommitted,
                C - Activated & Committed, D - Deactivated & Uncommitted
    -------------------------------------------------------------------------------
    -Type  St   Filename/Version    
    -------------------------------------------------------------------------------
    -IMG   C    16.12.05b.0.7                                                       
    
    -------------------------------------------------------------------------------
    -Auto abort timer: inactive
    -------------------------------------------------------------------------------
    -
    ZTP-FCW2320G04M#