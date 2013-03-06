#===============================================================================
import os_networksv2_python_novaclient_ext as rax_network
from novaclient.v1_1 import client as python_novaclient
from time import sleep
from utils import Utils
import sys
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
    def create_server(cls, nova_client, name, network_id, data):
        image = "5cebb13a-f783-4f8c-8058-c4182c724ccd"      # Ubuntu 12.04
        flavor = 6      # 8GB
        
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
                    "/root/.ssh/authorized_keys": \
                        Utils.read_data("/root/.ssh/id_rsa.pub"),
                    "/etc/prep.sh": Utils.read_data("vm_scripts/prep.sh"),
                    "/root/upgrade.sh": \
                        Utils.read_data("vm_scripts/upgrade.sh"),
                    "/root/install_oc.sh": data,
                    }
                )
        print "Scheduled server creation: %s | %s" % (server.id, server.name)
        return server
#-------------------------------------------------------------------------------
    @classmethod
    def check_quotas(cls, nova_client):
        # Check RAM & CloudNetwork Quotas

        ram_needed = 32768  # 32GB= 8GB x 4 = server, chef, controller, compute
        max_ram = Utils.get_limit(nova_client, "maxTotalRAMSize")

        # default rax max ram - 65GB
        enough_ram, ram_used = Utils.has_enough(
                nova_client,
                "totalRAMUsed",
                ram_needed,
                max_ram
                )

        networks_needed = 1
        max_networks = Utils.get_limit(nova_client, "maxTotalPrivateNetworks")

        # default rax max private networks - 3
        enough_networks, networks_used = Utils.has_enough(
                nova_client,
                "totalPrivateNetworksUsed",
                networks_needed,
                max_networks
                )

        while (not enough_ram) or (not enough_networks):
            if not enough_ram:
                print "\nQuota exceeded: not enough RAM"
                print "RAM Needed: %s\tRAM Used: %s" % (ram_needed, ram_used)
            if not enough_networks:
                print "\nQuota exceeded: too many networks"
                print "Networks Needed: %s\tNetworks Used: %s" % \
                        (networks_needed, networks_used)

            enough_ram, ram_used = Utils.has_enough(
                    nova_client,
                    "totalRAMUsed",
                    ram_needed,
                    max_ram
                    )
            enough_networks, networks_used = Utils.has_enough(
                    nova_client,
                    "totalPrivateNetworksUsed",
                    networks_needed,
                    max_networks
                    )

            print "\nRetrying in 10 secs..."
            sleep(10)
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_oc_service(cls, server, oc_port):
        try:
            ipv4 = Utils.get_ipv4(server.addresses["public"])
            
            while (not Utils.port_is_open(ipv4, oc_port)):
                print "\nWaiting for OpenCenter service to be up:", server.name
                sleep(10)
            print "OpenCenter Service Ready on:", server.name
        except Exception,e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
    @classmethod
    def delete_server(cls, server):
        try:
            server.delete()
        except Exception,e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
    @classmethod
    def update_server(cls, nova_client, server):
        try:
            updated_server = nova_client.servers.get(server.id)
            return updated_server
        except Exception,e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
    @classmethod
    def update_server_root_password(cls, updated_server, orig_server):
        try:
            updated_server.adminPass = orig_server.adminPass
        except Exception,e:
            print Utils.logging(e)
        return updated_server
#-------------------------------------------------------------------------------
    @classmethod
    def update_oc_admin_password(cls, updated_server, orig_server):
        try:
            updated_server.oc_server_password = orig_server.oc_server_password
        except Exception,e:
            pass
        return updated_server
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_server(cls, nova_client, server, oc_port = None):
        # Check server status until active
        updated_server = nova_client.servers.get(server.id)

        while (updated_server.status != "ACTIVE"):
            Utils.print_server_status(updated_server)
            updated_server = cls.update_server(nova_client, server)
            
            if updated_server.status == "ERROR":
                cls.delete_server(updated_server)
                return False
                
            sleep(10)
            
        # Set passwords
        updated_server = cls.update_server_root_password(updated_server, server)
        updated_server = cls.update_oc_admin_password(updated_server, server)
        
        # Print server info
        Utils.print_server_info(updated_server)

        # Run payloads via SSH
        ipv4 = Utils.get_ipv4(updated_server.addresses["public"])
        Utils.do_ssh_work(ipv4)

        # Wait for opencenter services to be ready, if required
        if oc_port: cls.wait_for_oc_service(updated_server, oc_port)
        
        return True
#-------------------------------------------------------------------------------
    @classmethod
    def launch_cluster(cls, nova_client, network, num_of_oc_agents):
        # Create OpenCenter Server & Prep install file
        name = Utils.generate_unique_name("bac-opencenter-server")
        
        fp = "vm_scripts/install_oc_server.sh"
        data = Utils.read_data(fp)
        oc_server_password = Utils.generate_password()
        data = data.replace("PASSWORD", oc_server_password)

        # Create OpenCenter Server
        created = False
        oc_server = None
        oc_server_ipv4 = None
        while not created:
            oc_server = cls.create_server(nova_client, name, network.id, data)
            oc_server.oc_server_password = oc_server_password

            # Wait for OpenCenter server services
            oc_server_port = 443   # OpenCenter HTTPS Server
            created = \
                    cls.wait_for_server(nova_client, oc_server, oc_server_port)
            
            if created:
                # Get OpenCenter IP
                oc_server = nova_client.servers.get(oc_server.id)
                oc_server_ipv4 = Utils.get_ipv4(oc_server.addresses["public"])

        # Create opencenter agents
        fp = "vm_scripts/install_oc_agent.sh"
        data = Utils.read_data(fp)
        data = data.replace("SERVER_IP", oc_server_ipv4)
        data = data.replace("PASSWORD", oc_server_password)

        created = False
        while not created:
            for i in range(0, num_of_oc_agents):
                created = False
                name = Utils.generate_unique_name("bac-opencenter-agent")
                oc_agent = \
                        cls.create_server(nova_client, name, network.id, data)
                created = \
                        cls.wait_for_server(nova_client, oc_agent)
#-------------------------------------------------------------------------------
    @classmethod
    def build_a_cloud(cls, nova_client):
        # Dev Cleanup
        cls.remove_user_networks(nova_client)

        # Check RAM & CloudNetwork Quotas
        cls.check_quotas(nova_client)

        # Create new network
        network = cls.create_network(nova_client, "bac", "192.168.4.0/24")

        # Launch opencenter cluster
        num_of_oc_agents = 5
        cls.launch_cluster(nova_client, network, num_of_oc_agents)
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
