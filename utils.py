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

# Abstract the usage of Rackspace Cloud Networks python-novaclient extension
class RackspaceNetworks:
#-------------------------------------------------------------------------------
    @classmethod
    def list(cls, nova_client):
        return rax_network.NetworkManager(nova_client).list()
#-------------------------------------------------------------------------------
    @classmethod
    def get(cls, nova_client, network_id):
        return rax_network.NetworkManager(nova_client).get(network_id)
#-------------------------------------------------------------------------------
    @classmethod
    def delete(cls, nova_client, network_id):
        return rax_network.NetworkManager(nova_client).delete(network_id)
#-------------------------------------------------------------------------------
    @classmethod
    def create(cls, nova_client, label, cidr):
        network = None

        while network is None:
            try:
                network = \
                    rax_network.NetworkManager(nova_client).create(label, cidr)
            except Exception,e:
                print str(e)
                print "Retrying in 5 secs..."
                sleep(5)
        return network
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#===============================================================================
