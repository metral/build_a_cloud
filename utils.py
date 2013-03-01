#===============================================================================
import random
import subprocess
from time import time, sleep
#-------------------------------------------------------------------------------
class Utils:
#-------------------------------------------------------------------------------
    @classmethod
    def read_data(cls, filepath):
        data = ""

        with open(filepath, "rb") as f:
            data = f.read()

        return data
#-------------------------------------------------------------------------------
    @classmethod
    def timestamp_rand(cls):
        return str(int(time())) + "-" + str(random.randint(10000000,99999999))
#-------------------------------------------------------------------------------
    @classmethod
    def generate_password(cls):
        error = ""

        try:
            command = "pwgen -s 15"
            p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
            output, error = p.communicate()
            output = output.replace("\n", "")
            output = output.replace(" ", "")
        except Exception,e:
            print str(e)
            return none

        return output
#-------------------------------------------------------------------------------
    @classmethod
    def do_ssh_work(cls, public_ipv4):
        try:
            command = \
                "ssh %s 'chmod +x /etc/prep.sh ; /etc/prep.sh'" % public_ipv4
            p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
            output, error = p.communicate()
        except Exception,e:
            print str(e)
#-------------------------------------------------------------------------------
    @classmethod
    def print_server_status(cls, server):
        print "\nServer Status:", server.status
        print "Server Progress: %s%%" % server.progress
#-------------------------------------------------------------------------------
    @classmethod
    def print_server_info(cls, server):
        print "\nServer Status:", server.status
        print "Server Public IP:", cls.get_ipv4(server.addresses["public"])
        print "Server Root Password:", server.adminPass
#-------------------------------------------------------------------------------
    @classmethod
    def get_ipv4(cls, addresses):
        ipv4 = ""

        for ip in addresses:
            if ip["version"] == 4:
                ipv4 = ip["addr"]

        return ipv4
#-------------------------------------------------------------------------------
    @classmethod
    def generate_unique_name(cls, name):
        unique_name = "_".join([name, cls.timestamp_rand()])
        return unique_name
#-------------------------------------------------------------------------------
#def get_ram_usage(rax_nova_client):            
#    flavor_map = {
#            '2' : 512,
#            '3' : 1024,
#            '4' : 2048,
#            '5' : 4096,
#            '6' : 8192,
#            '7' : 15360,
#            '8' : 30720,
#            }
#    
#    ram_usage = 0
#    
#    for server in rax_nova_client.servers.list():
#        flavor_id = server.flavor['id']
#        ram_usage += flavor_map[flavor_id]
#        
#    return ram_usage
##-------------------------------------------------------------------------------
#def has_enough_ram(rax_nova_client, ram_gb_needed):
#    max_ram = 66560 # default rackspace max ram - 65GB
#    
#    tentative_total = get_ram_usage(rax_nova_client) + (ram_gb_needed * 1024)
#    
#    if tentative_total <= max_ram:
#        return True
#    
#    return False
##-------------------------------------------------------------------------------
#def get_user_networks_usage(rax_nova_client):            
#    networks = Networks.list(rax_nova_client)
#    return len(networks) - 2  # remove 2: default RAX public & private network
##-------------------------------------------------------------------------------
#def has_not_hit_networks_quota(rax_nova_client, networks_needed):
#    max_networks = 3 # default rackspace max cloud networks
#    
#    tentative_total = get_user_networks_usage(rax_nova_client) + networks_needed
#    
#    if tentative_total <= max_networks:
#        return True
#    
#    return False
#-------------------------------------------------------------------------------
#===============================================================================
