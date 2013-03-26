#===============================================================================
import os_networksv2_python_novaclient_ext as rax_network
from novaclient.v1_1 import client as python_novaclient
from time import sleep
from utils import Utils
import oc
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
        ram_needed = 40960  # 40GB= 8GB x 5 = server, chef, controller, 2xcomp
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
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def update_root_password(cls, oc_server, updated_oc_server):
        try:
            updated_oc_server.adminPass = oc_server.adminPass
        except Exception,e:
            print Utils.logging(e)
        return updated_oc_server
#-------------------------------------------------------------------------------
    @classmethod
    def update_oc_password(cls, oc_server, updated_oc_server):
        try:
            updated_oc_server.oc_password = oc_server.oc_password
        except Exception,e:
            pass
        return updated_oc_server
#-------------------------------------------------------------------------------
    @classmethod
    def check_status(cls, nova_client, server):
        updated_server = cls.update_server(nova_client, server)
        
        try:
            if not updated_server:
                return None
            elif updated_server.status == "ERROR":
                return None
            elif updated_server.status == "BUILD":
                Utils.print_server_status(updated_server)
                return False
            elif updated_server.status == "ACTIVE":
                Utils.print_server_status(updated_server)
                return True
        except Exception,e:
            print Utils.logging(e)
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def post_setup(cls, nova_client, oc_server, oc_port = None):
        # Update server to have latest info
        updated_oc_server = cls.update_server(nova_client, oc_server)

        # Set passwords
        updated_oc_server = cls.update_root_password(\
                oc_server, updated_oc_server)
        updated_oc_server = cls.update_oc_password(oc_server, updated_oc_server)
        
        # Print server info
        Utils.print_server_info(updated_oc_server)

        # Run payloads via SSH
        ipv4 = Utils.get_ipv4(updated_oc_server.addresses["public"])
        command = "ssh %s 'chmod +x /etc/prep.sh ; /etc/prep.sh'" % ipv4
        Utils.do_subprocess(command)

        # Wait for opencenter services to be ready, if required
        if oc_port: cls.wait_for_oc_service(updated_oc_server, oc_port)
        
        return updated_oc_server
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_oc_server(cls, nova_client, oc_server, 
            network, oc_port = None):

        updated_oc_server = oc_server
        
        # Check server status until active
        status = cls.check_status(nova_client, updated_oc_server)
        while not status:
            if status == False:
                sleep(10)
                updated_oc_server = \
                        cls.update_server(nova_client, updated_oc_server)
            elif status is None:
                print "\nServer Error (Server): Deleting %s" \
                        % updated_oc_server.name
                cls.delete_server(updated_oc_server)
                sleep(10)
                updated_oc_server = cls.launch_oc_server(nova_client, network)
            status = cls.check_status(nova_client, updated_oc_server)
                
        ipv4 = Utils.get_ipv4(updated_oc_server.addresses["public"])
        active_port = 22    # SSH
        
        # If active, do post setup
        if Utils.port_is_open(ipv4, active_port):
            updated_oc_server = cls.post_setup(nova_client, oc_server, oc_port)
        # If for some reason network is not working even when active, try again
        else: 
            cls.delete_server(updated_oc_server)
            sleep(10)
            updated_oc_server = cls.launch_oc_server(nova_client, network)
            oc_port = 443
            updated_oc_server = cls.wait_for_oc_server(\
                    nova_client, oc_server, network, oc_port)
        
        return updated_oc_server
#-------------------------------------------------------------------------------
    @classmethod
    def launch_oc_server(cls, nova_client, network):
        name = Utils.generate_unique_name("bac-opencenter-server")
        
        fp = "vm_scripts/install_oc_server.sh"
        data = Utils.read_data(fp)
        oc_password = Utils.generate_password()
        data = data.replace("PASSWORD", oc_password)

        # Create OpenCenter Server
        oc_server = None
        oc_server = cls.create_server(nova_client, name, network.id, data)
        oc_server.oc_password = oc_password
        
        return oc_server
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_oc_agents(cls, oc_agents, nova_client, oc_server, network):
        updated_oc_agents = []
        
        active_port = 22    # SSH
        while len(updated_oc_agents) != len(oc_agents):
            for index, oc_agent in enumerate(oc_agents):
                status = cls.check_status(nova_client, oc_agent)
                
                if status == True:
                    updated_oc_agent = cls.update_server(nova_client, oc_agent)
                    ipv4 = Utils.get_ipv4(updated_oc_agent.addresses["public"])
                    if updated_oc_agent not in updated_oc_agents:
                        if Utils.port_is_open(ipv4, active_port):
                            updated_oc_agent = \
                                    cls.post_setup(nova_client, oc_agent)
                            updated_oc_agents.append(updated_oc_agent)
                        else:
                            print "\nServer Error (Agent Net): Deleting %s" \
                                    % oc_agent.name
                            cls.delete_server(oc_agent)
                            sleep(10)
                            oc_agent = cls.launch_oc_agent(\
                                    oc_server, nova_client, network)
                            oc_agents[index] = oc_agent    
                elif status == False:
                    sleep(10)
                elif status is None:
                    print "\nServer Error (Agent): Deleting %s", oc_agent.name
                    cls.delete_server(oc_agent)
                    sleep(10)
                    oc_agent = cls.launch_oc_agent(\
                            oc_server, nova_client, network)
                    oc_agents[index] = oc_agent    
        
        return updated_oc_agents
#-------------------------------------------------------------------------------
    @classmethod
    def launch_oc_agent(cls, oc_server, nova_client, network):
        name = Utils.generate_unique_name("bac-opencenter-agent")

        ipv4 = Utils.get_ipv4(oc_server.addresses["public"])
        
        fp = "vm_scripts/install_oc_agent.sh"
        data = Utils.read_data(fp)
        data = data.replace("SERVER_IP", ipv4)
        data = data.replace("PASSWORD", oc_server.oc_password)
            
        oc_agent = cls.create_server(nova_client, name, network.id, data)
        
        return oc_agent
#-------------------------------------------------------------------------------
    @classmethod
    def launch_oc_agents(cls, oc_server, nova_client, 
            network, num_of_oc_agents):

        oc_agents = []
        for i in range(0, num_of_oc_agents):
            oc_agent = cls.launch_oc_agent(oc_server, nova_client, network)
            oc_agents.append(oc_agent)    
            sleep(2)
            
        updated_oc_agents = cls.wait_for_oc_agents(\
                oc_agents, nova_client, oc_server, network)
                    
        return updated_oc_agents
#-------------------------------------------------------------------------------
    @classmethod
    def launch_cluster(cls, nova_client, network, num_of_oc_agents):
        # Create OpenCenter Server 
        oc_server = cls.launch_oc_server(nova_client, network)

        # Wait for OpenCenter server HTTPS server to be up
        oc_port = 443
        updated_oc_server = \
                cls.wait_for_oc_server(nova_client, oc_server, network, oc_port)

        # Create opencenter agents
        oc_agents = cls.launch_oc_agents(\
                updated_oc_server, nova_client, network, num_of_oc_agents)
        
        return updated_oc_server, oc_agents
#-------------------------------------------------------------------------------
    @classmethod
    def build_a_cloud(cls, nova_client):
        # Dev Cleanup
        cls.remove_user_networks(nova_client)

        # Check RAM & CloudNetwork Quotas
        cls.check_quotas(nova_client)

        # Create new network
        cidr = "192.168.3.0/24"
        network = cls.create_network(nova_client, "bac", cidr)

        # Launch opencenter cluster
        num_of_oc_agents = 4
        oc_server, oc_agents = \
                cls.launch_cluster(nova_client, network, num_of_oc_agents)
                
                
        print "************************** Cluster Launched" 
        Utils.print_server_info(oc_server)
        for oc_agent in oc_agents:
            Utils.print_server_info(oc_agent)
            

        print "************************** Provisioning Cluster" 
        oc_user = "admin"
        oc_password = oc_server.oc_password
        oc_server_ipv4 = Utils.get_ipv4(oc_server.addresses["public"])
        oc_url ="https://%s:8443" % oc_server_ipv4
         
        oc.provision_cluster(nova_client, oc_server, oc_url, oc_user, \
            oc_password, num_of_oc_agents, cidr)

        #USER = "admin"
        #PASSWORD = "KOHirS1QrtSs"
        #SERVER_IPV4 = "166.78.118.53"
        #URL ="https://%s:8443" % SERVER_IPV4

        #cidr = "192.168.3.0/24"
        #class Foo():
        #    name = "bac-opencenter-server-1363043393-72479695"
        #oc_server = Foo()
        #
        #oc.provision_cluster(nova_client, oc_server, URL, USER, \
        #    PASSWORD, 3, cidr)
        
#-------------------------------------------------------------------------------
    @classmethod
    def list_networks(cls, nova_client):
        networks = None

        try:
            network_manager = rax_network.NetworkManager(nova_client)
            networks = network_manager.list()
        except Exception,e:
            pass
        
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
        while True:
            try:
                network_manager = rax_network.NetworkManager(nova_client)
                network_manager.delete(network.id)
                print "Removed network: %s | %s" % (network.label, network.id)
                break
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

        if networks:
            for network in networks:
                if network.id not in default_nics:
                    cls.delete_network(nova_client, network)
#-------------------------------------------------------------------------------
#===============================================================================
