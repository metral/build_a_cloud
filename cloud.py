#!/usr/bin/python
#===============================================================================
from novaclient.v1_1 import client as nova_client
import optparse
import subprocess
import sys
from time import time, sleep
from utils import Utils
from utils import RackspaceNetworks
#-------------------------------------------------------------------------------
# Globals


USERNAME = os.environ["OS_USERNAME"]
TENANT_NAME = os.environ["OS_TENANT_NAME"]
API_KEY = os.environ["OS_PASSWORD"]
REGION = os.environ["OS_REGION_NAME"]

# mikemetral
#USERNAME = os.environ["OS_USERNAME"]
#TENANT_NAME = os.environ["OS_TENANT_NAME"]
#API_KEY = os.environ["OS_PASSWORD"]
#REGION = os.environ["OS_REGION_NAME"]

AUTH_SYSTEM = os.environ["OS_AUTH_SYSTEM"]
AUTH_URL = os.environ["OS_AUTH_URL"]
#-------------------------------------------------------------------------------
def setup_parser_options():
    parser = optparse.OptionParser("usage: " + \
        "%prog [options] username " + \
        "\n\nDescription:" + \
        "\n------------" + \
        "\n'%prog' Allows for management of partner accounts on alamo." + \
        "\n\nFor help, use %prog -h or %prog --help")
    parser.add_option("-c","--create", \
        dest='username_to_create', \
        help="The username of the partner to create.")
    parser.add_option("-r","--remove", \
        dest='username_to_remove', \
        help="The username of the partner to remove.")

    return parser
#-------------------------------------------------------------------------------
def remove_user_networks(rax_nova_client):
    # rax default public & private networks
    blacklist = [
            "00000000-0000-0000-0000-000000000000", \
            "11111111-1111-1111-1111-111111111111"
            ]
    
    networks = RackspaceNetworks.list(rax_nova_client)
    
    for network in networks:
        if network.id not in blacklist:
            while network in RackspaceNetworks.list(rax_nova_client):
                try:
                    RackspaceNetworks.delete(rax_nova_client, network.id)
                except Exception,e:
                    print str(e)
                    print "Retrying in 5 secs..."
                    sleep(5)
                if network not in RackspaceNetworks.list(rax_nova_client):
                    print "Removed network: %s -- %s" \
                            % (network.label, network.id)
#-------------------------------------------------------------------------------
def get_ram_usage(rax_nova_client):            
    flavor_map = {
            '2' : 512,
            '3' : 1024,
            '4' : 2048,
            '5' : 4096,
            '6' : 8192,
            '7' : 15360,
            '8' : 30720,
            }
    
    ram_usage = 0
    
    for server in rax_nova_client.servers.list():
        flavor_id = server.flavor['id']
        ram_usage += flavor_map[flavor_id]
        
    return ram_usage
#-------------------------------------------------------------------------------
def has_enough_ram(rax_nova_client, ram_gb_needed):
    max_ram = 66560 # default rackspace max ram - 65GB
    
    tentative_total = get_ram_usage(rax_nova_client) + (ram_gb_needed * 1024)
    
    if tentative_total <= max_ram:
        return True
    
    return False
#-------------------------------------------------------------------------------
def get_user_networks_usage(rax_nova_client):            
    networks = RackspaceNetworks.list(rax_nova_client)
    return len(networks) - 2  # remove 2: default RAX public & private network
#-------------------------------------------------------------------------------
def has_not_hit_networks_quota(rax_nova_client, networks_needed):
    max_networks = 3 # default rackspace max cloud networks
    
    tentative_total = get_user_networks_usage(rax_nova_client) + networks_needed
    
    if tentative_total <= max_networks:
        return True
    
    return False
#-------------------------------------------------------------------------------
def create_opencenter_server(rax_nova_client, name, network_id):
    image = "5cebb13a-f783-4f8c-8058-c4182c724ccd"  # Ubuntu 12.04
    flavor = 2      # 512MB

    server = rax_nova_client.servers.create(
            name = name,
            image = image,
            flavor = flavor,
            nics = [
                    {"net-id": "00000000-0000-0000-0000-000000000000"},
                    {"net-id": "11111111-1111-1111-1111-111111111111"},
                    {"net-id": network_id},
                ],
            files = {
                "/root/.ssh/authorized_keys": \
                        Utils.read_data("/root/.ssh/id_rsa.pub"),
                "/etc/prep.sh": Utils.read_data("vm_scripts/prep.sh"),
                "/root/upgrade.sh": Utils.read_data("vm_scripts/upgrade.sh"),
                "/root/install_server.sh": \
                    Utils.read_data("vm_scripts/install_server.sh"),
                }
            )

    print "Server ID: '%s' | Name: '%s' is being scheduled..." \
            % (server.id, server.name)
    return server.id
#-------------------------------------------------------------------------------
def check_server_status(rax_nova_client, server_id):
    server = rax_nova_client.servers.get(server_id)
    
    while (server.status != "ACTIVE"):
        print "\n"
        print "Server Status: ",  server.status
        print "Server Progress: %s%%" % server.progress
        server = rax_nova_client.servers.get(server_id)

        for network in server.networks:
            try:
                print "here 1"
                print network.ipv4
            except:
                pass
            try:
                print "here 2"
                print network.address
            except:
                pass
            try:
                print "here 3"
                print network.fixed_ip
            except:
                pass
            try:
                print "here 4"
                print network.floating_ip
            except:
                pass
            try:
                print "here 5"
                print network.public_address
            except:
                pass
            
        sleep(5)
        
    # subprocess an SSH command to kick things off"
    # ssh server.public_address "chmod +x /etc/prep.sh ; /etc/prep.sh"

    print "Server ID: '%s' | Name: '%s' is now built" % (server.id, server.name)
    print "Server Public IP: ", server.public_address
    print "Server Root Password: ", server.adminPass
#-------------------------------------------------------------------------------
def main():
    # Setup parser options & parse them
    parser = setup_parser_options()
    (options, args) = parser.parse_args()

    rax_nova_client = nova_client.Client(USERNAME, API_KEY, \
            TENANT_NAME, AUTH_URL, service_type="compute", \
            auth_system = AUTH_SYSTEM, region_name = REGION)

    # Clean up user networks
    #remove_user_networks(rax_nova_client)
    
    # Check enough ram & networks
#    if has_enough_ram(rax_nova_client, 26) and \
#                    has_not_hit_networks_quota(rax_nova_client, 1):
        #network = RackspaceNetworks.create(\
        #        rax_nova_client, "bac", "192.168.3.0/24")

    name = "_".join(["bac-opencenter-server", Utils.random_number()])
    #server_id = create_opencenter_server(rax_nova_client, name, network.id)
    server_id = create_opencenter_server(rax_nova_client, name, "7ff68cc1-696c-4501-bddb-963f52ee0c5e")
    check_server_status(rax_nova_client, server_id)
    #else:
    #    print False
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
#===============================================================================
