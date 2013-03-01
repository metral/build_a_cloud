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

AUTH_SYSTEM = os.environ["OS_AUTH_SYSTEM"]
AUTH_URL = os.environ["OS_AUTH_URL"]
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
            RackspaceNetworks.delete(rax_nova_client, network)
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
def get_ipv4(addresses):
    ipv4 = ""
    
    for ip in addresses:
        if ip["version"] == 4:
            ipv4 = ip["addr"]

    return ipv4
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

    print "Scheduled server creation: %s | %s" % (server.id, server.name)
    return server
#-------------------------------------------------------------------------------
def print_server_status(server):
    print "\nServer Status:", server.status
    print "Server Progress: %s%%" % server.progress
#-------------------------------------------------------------------------------
def print_server_info(server, refreshed_server):
    print "\nServer Status:",  refreshed_server.status
    print "Server Public IP:", get_ipv4(refreshed_server.addresses["public"])
    print "Server Root Password:", server.adminPass
#-------------------------------------------------------------------------------
def main():
    # Create nova client to Rackspace account
    rax_nova_client = nova_client.Client(USERNAME, API_KEY, \
            TENANT_NAME, AUTH_URL, service_type="compute", \
            auth_system = AUTH_SYSTEM, region_name = REGION)

    # Clean up user networks
    remove_user_networks(rax_nova_client)
    
    # Create new network
    network = RackspaceNetworks.create(rax_nova_client, "bac", "192.168.5.0/24")
    
    # Create new server
    name = "_".join(["bac-opencenter-server", Utils.random_number()])
    server = create_opencenter_server(rax_nova_client, name, network.id)
    
    # Check server status until active
    refreshed_server = server
    while (refreshed_server.status != "ACTIVE"):
        print_server_status(refreshed_server)
        refreshed_server = rax_nova_client.servers.get(refreshed_server.id)
        sleep(5)
        
    # Print server info, once ACTIVE. orig server is only server with adminPass
    print_server_info(server, refreshed_server)
    
    # Run payloads via SSH
    Utils.do_ssh(get_ipv4(refreshed_server.addresses["public"]))
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
#===============================================================================
