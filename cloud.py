#!/usr/bin/python
#===============================================================================
from novaclient.v1_1 import client as nova_client
import optparse
import subprocess
import sys
from utils import RackspaceNetworks
#-------------------------------------------------------------------------------
# Globals
USERNAME = os.environ["OS_USERNAME"]
TENANT_NAME = os.environ["OS_TENANT_NAME"]
API_KEY = os.environ["OS_PASSWORD"]
AUTH_SYSTEM = os.environ["OS_AUTH_SYSTEM"]
AUTH_URL = os.environ["OS_AUTH_URL"]
REGION = os.environ["OS_REGION_NAME"]
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
def remove_user_networks(rax_nova_client, rax_networks):
    # rax default public & private networks
    blacklist = [
            "00000000-0000-0000-0000-000000000000", \
            "11111111-1111-1111-1111-111111111111"
            ]
    
    for network in rax_networks:
        if network.id not in blacklist:
            RackspaceNetworks.delete(rax_nova_client, network.id)
#-------------------------------------------------------------------------------
def main():
    # Setup parser options & parse them
    parser = setup_parser_options()
    (options, args) = parser.parse_args()

    rax_nova_client = nova_client.Client(USERNAME, API_KEY, \
        TENANT_NAME, AUTH_URL, service_type="compute", \
        auth_system = AUTH_SYSTEM, region_name = REGION)

    rax_networks = RackspaceNetworks.list(rax_nova_client)
    remove_user_networks(rax_nova_client, rax_networks)
    print RackspaceNetworks.list(rax_nova_client)

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#-------------------------------------------------------------------------------
#===============================================================================
