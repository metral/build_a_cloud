#===============================================================================
from time import sleep
from utils import Utils
from rackspace import CloudServers
import os
#-------------------------------------------------------------------------------
# Globals


USERNAME = os.environ["OS_USERNAME"]
TENANT_NAME = os.environ["OS_TENANT_NAME"]
API_KEY = os.environ["OS_PASSWORD"]
REGION = os.environ["OS_REGION_NAME"]

AUTH_SYSTEM = os.environ["OS_AUTH_SYSTEM"]
AUTH_URL = os.environ["OS_AUTH_URL"]
#-------------------------------------------------------------------------------
def main():
    # Create CloudServers object to connect with Rackspace CloudServers
    cloudservers = CloudServers.create(USERNAME, API_KEY, TENANT_NAME,
            AUTH_URL, AUTH_SYSTEM, REGION)
    nc = cloudservers.nova_client
    
    # Clean up user networks
    CloudServers.remove_user_networks(nc)
    
    # Create new network
    network = CloudServers.create_network(nc, "bac", "192.168.5.0/24")
    
    # Create new server
    name = Utils.generate_unique_name("bac-opencenter-server")
    oc_server = CloudServers.create_opencenter_server(nc, name, network.id)
    
    # Check server status until active
    updated_oc_server = nc.servers.get(oc_server.id)
    while (updated_oc_server.status != "ACTIVE"):
        Utils.print_server_status(updated_oc_server)
        updated_oc_server = nc.servers.get(updated_oc_server.id)
        sleep(5)
    updated_oc_server.adminPass = oc_server.adminPass
        
    # Print server info, once ACTIVE. orig server is only server with adminPass
    Utils.print_server_info(updated_oc_server)
    
    # Run payloads via SSH
    Utils.do_ssh_work(Utils.get_ipv4(updated_oc_server.addresses["public"]))
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
#===============================================================================
