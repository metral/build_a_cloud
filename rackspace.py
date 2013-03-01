#===============================================================================
import os_networksv2_python_novaclient_ext as rax_network
from novaclient.v1_1 import client as python_novaclient
from time import sleep
from utils import Utils
#-------------------------------------------------------------------------------
default_nics = [
        "00000000-0000-0000-0000-000000000000",     # Public
        "11111111-1111-1111-1111-111111111111"      # Private
        ]
#-------------------------------------------------------------------------------
# Abstract the usage of Rackspace CloudServers functionality
#-------------------------------------------------------------------------------
class CloudServers():
    nova_client = python_novaclient.Client("","","","")
    
    def __init__(self, *args, **kwargs):
        self.nova_client = kwargs.pop('nova_client', None)
#-------------------------------------------------------------------------------
    @classmethod
    def create(cls, username, api_key, tenant_name, 
            auth_url, auth_system, region):
        
        # Create nova client to Rackspace CloudServers
        new_nova_client = cls(
                nova_client = python_novaclient.Client(username, api_key, \
                tenant_name, auth_url, service_type="compute", \
                auth_system = auth_system, region_name = region)
                )

        return new_nova_client
#-------------------------------------------------------------------------------
    @classmethod
    def create_opencenter_server(cls, nova_client, name, network_id):
        image = "5cebb13a-f783-4f8c-8058-c4182c724ccd"      # Ubuntu 12.04
        flavor = 2      # 512MB

        server = nova_client.servers.create(
            name = name,
            image = image,
            flavor = flavor,
            nics = [
                {"net-id": default_nics[0]},
                {"net-id": default_nics[1]},
                {"net-id": network_id},
                ],
            files = {
                "/root/.ssh/authorized_keys": 
                    Utils.read_data("/root/.ssh/id_rsa.pub"),
                "/etc/prep.sh": 
                    Utils.read_data("vm_scripts/prep.sh"),
                "/root/upgrade.sh":
                    Utils.read_data("vm_scripts/upgrade.sh"),
                "/root/install_server.sh":
                    Utils.read_data("vm_scripts/install_server.sh"),
                }
        )

        print "Scheduled server creation: %s | %s" % (server.id, server.name)
        return server
#-------------------------------------------------------------------------------
    @classmethod
    def list_networks(cls, nova_client):
        networks = None

        while networks is None:
            try:
                network_manager = rax_network.NetworkManager(nova_client)
                networks = network_manager.list()
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return networks
#-------------------------------------------------------------------------------
    @classmethod
    def get_network(cls, nova_client, network_id):
        network = None

        while network is None:
            try:
                network_manager = rax_network.NetworkManager(nova_client)
                network = network_manager.get(network_id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return network
#-------------------------------------------------------------------------------
    @classmethod
    def delete_network(cls, nova_client, network):
        while network in cls.list_networks(nova_client):
            try:
                network_manager = rax_network.NetworkManager(nova_client)
                network_manager.delete(network.id)
                print "Removed network: %s | %s" % (network.label, network.id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
#-------------------------------------------------------------------------------
    @classmethod
    def create_network(cls, nova_client, label, cidr):
        network = None

        while network is None:
            try:
                network_manager = rax_network.NetworkManager(nova_client)
                network = network_manager.create(label, cidr)
                print "Created network: %s | %s" % (network.label, network.id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return network
#-------------------------------------------------------------------------------
    @classmethod
    def remove_user_networks(cls, nova_client):
        networks = cls.list_networks(nova_client)
        
        for network in networks:
            if network.id not in default_nics:
                cls.delete_network(nova_client, network)
#-------------------------------------------------------------------------------
#===============================================================================
