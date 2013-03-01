#===============================================================================
#!/usr/bin/python
#-------------------------------------------------------------------------------
import os_networksv2_python_novaclient_ext as rax_network
import random
import subprocess
from time import time, sleep
#-------------------------------------------------------------------------------
class Utils:
#-------------------------------------------------------------------------------
    @classmethod
    def read_data(self, filepath):
        data = ""

        with open(filepath, "rb") as f:
            data = f.read()

        return data
#-------------------------------------------------------------------------------
    @classmethod
    def random_number(self):
        return str(int(time())) + "-" + str(random.randint(10000000,99999999))
#-------------------------------------------------------------------------------
    @classmethod
    def generate_password(self):
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
    def do_ssh(self, public_ipv4):
        try:
            command = \
                "ssh %s 'chmod +x /etc/prep.sh ; /etc/prep.sh'" % public_ipv4
            p = subprocess.Popen(command, stdout = subprocess.PIPE, shell=True)
            output, error = p.communicate()
        except Exception,e:
            print str(e)
#-------------------------------------------------------------------------------
# Abstract the usage of Rackspace Cloud Networks python-novaclient extension
class RackspaceNetworks:
#-------------------------------------------------------------------------------
    @classmethod
    def list(cls, nova_client):
        networks = None
        
        while networks is None:
            try:
                networks = rax_network.NetworkManager(nova_client).list()
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return networks
#-------------------------------------------------------------------------------
    @classmethod
    def get(cls, nova_client, network_id):
        network = None

        while network is None:
            try:
                network = \
                        rax_network.NetworkManager(nova_client).get(network_id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return network
#-------------------------------------------------------------------------------
    @classmethod
    def delete(cls, nova_client, network):
        while network in cls.list(nova_client):
            try:
                rax_network.NetworkManager(nova_client).delete(network.id)
                print "Removed network: %s | %s" % (network.label, network.id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
#-------------------------------------------------------------------------------
    @classmethod
    def create(cls, nova_client, label, cidr):
        network = None

        while network is None:
            try:
                network = \
                    rax_network.NetworkManager(nova_client).create(label, cidr)
                print "Created network: %s | %s" % (network.label, network.id)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return network
#-------------------------------------------------------------------------------
#===============================================================================
