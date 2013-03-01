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
    @classmethod
    def get_usage(cls, nova_client, limit_name):            
        total_used = 0
        limits = nova_client.limits.get()
        
        for limit in limits.absolute:
            if limit.name == limit_name:
                total_used = limit.value
        
        return total_used
#-------------------------------------------------------------------------------
    @classmethod
    def has_enough(cls, nova_client, limit_name, needed, max):
        used = cls.get_usage(nova_client, limit_name)
        
        tentative_total = used + needed
        
        if tentative_total <= max:
            return True, used
        return False, used
#-------------------------------------------------------------------------------
#===============================================================================
