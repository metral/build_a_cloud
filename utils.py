#===============================================================================
#!/usr/bin/python
#-------------------------------------------------------------------------------
import os_networksv2_python_novaclient_ext as rax_network
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
        return rax_network.NetworkManager(nova_client).create(label, cidr)
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#===============================================================================
