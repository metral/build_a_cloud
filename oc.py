#-------------------------------------------------------------------------------
from time import sleep
from utils import Utils
import json
import logging
#-------------------------------------------------------------------------------
logger = logging.getLogger('build_a_cloud')
#-------------------------------------------------------------------------------
################################################################################
class Task:
#-------------------------------------------------------------------------------
    @classmethod
    # Wait for task to be tasked & adventurated on
    # When an adventure is tasked, 2 tasks are actually created: adventurate &
    # then the actual adventure that is spawned by adventurate. therefore, 
    # the task_id returned during adventure execution is that of adventurate, 
    # not of the actual task, so you need parent_id of the 
    # adventure task. thus to wait for the task you need to compare the
    # parent_id (adventurate task), the action invoked & the node_id in 
    # which the adventure was issued upon. 
    # However, in the case of create_nova_cluster where the task is a 
    # plan that is only an adveruate task, there is no parent and the node_id
    # is the OpenCenter server itself, so you can only compare the task_id 
    def wait_for_task(cls, parent_id, node, action, url, user, password,
            queued_task_id = None):
        tasked = False
        state = None
        task_id = None

        logger.info("Waiting for '%s' to task ... " % (action))
        while not tasked:
            tasks_json = Utils.oc_api(url + "/tasks/", user, password)
            tasks = Utils.extract_oc_object_type(tasks_json, "tasks")
            for task in tasks:
                if action == "adventurate":
                    if task['id'] == queued_task_id:
                        tasked = True
                        task_id = task['id']
                        state = task['state']
                else:
                    if (task['node_id'] == node['id']) and \
                        (task['action'] == action) and \
                        (task['parent_id'] >= parent_id):
                        tasked = True
                        task_id = task['id']
                        state = task['state']

            logger.debug("Still waiting for '%s' to task ... " % (action))
            sleep(2)

        logger.info("'%s' is running ..." % (action))
        while(state != 'done' and task_id):
            logger.debug("'%s' is still running ..." % (action))
            path = "/tasks/%s" % task_id
            updated_json = Utils.oc_api(url + path, user, password)
            updated_task = Utils.extract_oc_object_type(updated_json, "task")
            if updated_task:
                state = updated_task['state']
            sleep(5)
    
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_remaining_tasks(cls, url, user, password):
        
        restart_loop = True
        
        while restart_loop:
            tasks_json = Utils.oc_api(url + "/tasks/", user, password)
            tasks = Utils.extract_oc_object_type(tasks_json, "tasks")
            restart_loop = False
            for task in tasks:
                if task['state'] == "running":
                    restart_loop = True
                    break
#-------------------------------------------------------------------------------
################################################################################
            
class Fact:
#-------------------------------------------------------------------------------
    @classmethod
    def create(cls, url, user, password, params):
        result = None
        path = "/facts/"
        full_url = url + path
        
        if params:
            result = Utils.oc_api(full_url, user, password,
                    kwargs={'json': params})
            return result

        return None
#-------------------------------------------------------------------------------
################################################################################
            
class Adventure:
#-------------------------------------------------------------------------------
    @classmethod
    def get_adventures(cls, url, user, password):
        # Get adventures
        adventures_json = Utils.oc_api(url + "/adventures/", user, password)
        adventures = Utils.extract_oc_object_type(adventures_json, "adventures")
        return adventures
#-------------------------------------------------------------------------------
    @classmethod
    def find(cls, adventure_name, url, user, password):
        # Find adventures
        adventures = cls.get_adventures(url, user, password)

        for adventure in adventures:
            if adventure['name'] == adventure_name:
                return adventure
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef_server(cls, node, url, user, password):
        # Execute 'install_chef_server' adventure
        adventure = cls.find("Install Chef Server", url, user, password)
        params = {
                "node": node['id'],
                }

        path = "/adventures/%s/execute" % adventure['id']
        result = Utils.execute(path, url, user, password, params)

        # result['task']['id'] is adventurate parent id
        parent_id = int(result['task']['id'])

        try:
            if result['status'] == 202:
                # Monitor tasking of install_chef_server
                action = "install_chef_server"
                Task.wait_for_task(parent_id, node, action, url, user, password)

                # Monitor tasking of download_cookbooks
                action = "download_cookbooks"
                Task.wait_for_task(parent_id, node, action, url, user, password)
        except Exception,e:
            logger.error(str(e))
            return None

        return node
#-------------------------------------------------------------------------------
    @classmethod
    def create_nova_cluster(cls, node, chef_server, url, user,
        password, cidr):

        workspace_node = Node.find("workspace", url, user, password)

        # Create Nova Cluster
        params = {
                "node": workspace_node['id'],
                "plan": [
                    { "primitive": "node.add_backend",
                        "ns": {
                            "backend": "nova"}},
                        { "primitive": "nova.create_cluster",
                            "ns": {
                                "chef_server": chef_server['id'],
                                "cluster_name": "NovaCluster",
                                "nova_public_if": "eth0",
                                "keystone_admin_pw": password,
                                "nova_dmz_cidr": "172.16.0.0/24",
                                "nova_vm_fixed_range": "172.28.48.0/24",
                                "nova_vm_fixed_if": "eth2",
                                "nova_vm_bridge": "br100",
                                "osops_mgmt": cidr,
                                "osops_nova": cidr,
                                "osops_public": cidr,
                                }
                            }
                        ]
                }

        path = "/plan/"
        result = Utils.execute(path, url, user, password, params)

        task_id = int(result['task']['id'])
        
        try:
            if result['status'] == 202:
                # Monitor tasking of create_nova_cluster
                action = "adventurate"
                Task.wait_for_task(None, None, action, url, \
                        user, password, task_id)
        except Exception,e:
            logger.error(str(e))
#-------------------------------------------------------------------------------
    @classmethod
    def provision_nova_node(cls, node_name, node, url, user, password):
        nova_node = Node.find(node_name, url, user, password)
        
        # Execute fact
        params = {
                "node_id": ("%s" % node['id']),
                "key": "parent_id",
                "value": nova_node['id']
                }

        result = Fact.create(url, user, password, params)

        # result['task']['id'] is adventurate parent id
        parent_id = int(result['task']['id'])
        try:
            if result['status'] == 202:
                # Monitor tasking of install_chef client
                action = "install_chef"
                Task.wait_for_task(parent_id, node, action, url, user, password)

                # Monitor tasking of running chef-client
                action = "run_chef"
                Task.wait_for_task(parent_id, node, action, url, user, password)
        except Exception,e:
            logger.error(str(e))
            return None

        return node
#-------------------------------------------------------------------------------
    @classmethod
    def generic_adventure(cls, node, url, user, password, 
            adventure_name, action):

        # Execute the adventure
        adventure = cls.find(adventure_name, url, user, password)
        params = {
                "node": node['id'],
                }

        path = "/adventures/%s/execute" % adventure['id']
        result = Utils.execute(path, url, user, password, params)

        # result['task']['id'] is adventurate parent id
        parent_id = int(result['task']['id'])

        try:
            if result['status'] == 202:
                # Monitor tasking of action
                action = action
                Task.wait_for_task(parent_id, node, action, url, user, password)

        except Exception,e:
            logger.error(str(e))
            return None

        return node
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef_clients(cls, nodes, url, user, password,
            num_of_clients):
        provisioned_chef_clients = []

        for i in range(0, num_of_clients):
            node = nodes.pop(0)
            provisioned_node = cls.generic_adventure(\
                    node, url, user, password, "Install Chef Client",
                    "install_chef")
            provisioned_chef_clients.append(provisioned_node)

        return provisioned_chef_clients

################################################################################

class Node:
#-------------------------------------------------------------------------------
    @classmethod
    def get_unprovisioned(cls, nodes, url, user, password):
        unprovisioned_nodes = []
        try:
            unprovisioned_node = cls.find("unprovisioned", url, user, password)
            if unprovisioned_node:
                for node in nodes:
                    try:
                        parent_id = node['facts']['parent_id']
                        if parent_id == unprovisioned_node['id']:
                            unprovisioned_nodes.append(node)
                    except:
                        pass

            return unprovisioned_nodes
        except Exception,e:
            logger.error(str(e))
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def get_nodes(cls, url, user, password):
        # Get nodes
        nodes_json = Utils.oc_api(url + "/nodes/", user, password)
        nodes = Utils.extract_oc_object_type(nodes_json, "nodes")
        return nodes
#-------------------------------------------------------------------------------
    @classmethod
    def find(cls, node_name, url, user, password):
        # Find nodes
        nodes = cls.get_nodes(url, user, password)

        for node in nodes:
            if node['name'] == node_name:
                return node
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_agents(cls, total_agents, url, user, password):
        unprovisioned_nodes = []

        logger.info("Waiting for all unprovisioned/available nodes...")
        while len(unprovisioned_nodes) < total_agents:
            nodes = cls.get_nodes(url, user, password)
            unprovisioned_nodes = cls.get_unprovisioned(nodes, \
                    url, user, password)
            if len(unprovisioned_nodes) < total_agents:
                msg = "Still waiting for all unprovisioned/available nodes..."
                logger.debug(msg)
                sleep(10)

        return unprovisioned_nodes
#-------------------------------------------------------------------------------
    @classmethod
    def make_chef_changes(cls, server):
        #try:
        #    ipv4 = Utils.get_ipv4(server.addresses["public"])
        #    command = "scp vm_scripts/update_chef.py %s:/root/ ;" \
        #            "ssh %s python update_chef.py" % (ipv4, ipv4)
        #    print Utils.do_subprocess(command)
        #except Exception,e:
        #    print logger.error(str(e))
        
        try:
            ipv4 = Utils.get_ipv4(server.addresses["public"])
            command = "scp -o StrictHostKeyChecking=no " + \
                    "vm_scripts/update_chef.sh %s:/root/ ;" + \
                    "ssh -o StrictHostKeyChecking=no %s " + \
                    "/root/update_chef.sh > /dev/null" % (ipv4, ipv4)
            logger.debug(Utils.do_subprocess(command))
        except Exception,e:
            logger.error(str(e))
#-------------------------------------------------------------------------------
    @classmethod
    def make_nova_changes(cls, server):
        try:
            ipv4 = Utils.get_ipv4(server.addresses["public"])
            command = "scp -o StrictHostKeyChecking=no " + \
                    "vm_scripts/nova.sh %s:/root/ ;" + \
                    "ssh -o StrictHostKeyChecking=no " + \
                    "%s /root/nova.sh > /dev/null" % (ipv4, ipv4)
            logger.debug(Utils.do_subprocess(command))
        except Exception,e:
            logger.error(str(e))
#-------------------------------------------------------------------------------
def provision_cluster(nova_client, oc_server, url, user, 
        password, num_of_oc_agents, cidr):

    #Get OpenCenter server node
    service_nodes_server = Node.find(oc_server.name, url, user, password)
    
    # Enable qemu in chef environment template file
    logger.info("Updating Chef Environment Template to use Qemu")
    service_nodes_server_node = Utils.find_server(\
            nova_client, service_nodes_server['name'])
    Node.make_chef_changes(service_nodes_server_node)
    
    # Wait for all unprovisioned OC agent nodes to be up & talking to OC server
    unprovisioned_nodes = Node.wait_for_agents(\
            num_of_oc_agents, url, user, password)

    # Provision OC agent as Chef Server
    node = unprovisioned_nodes.pop(0)
    chef_server = Adventure.provision_chef_server(node, url, user, password)
    chef_server_node = Utils.find_server(nova_client, chef_server['name'])
    logger.info("Chef-Server:")
    logger.info(chef_server['name'])
    
    ##TODO: DELETE THIS!!! 
    #chef_server = {
    #        'id': 5,
    #        'name': "bac-opencenter-agent-1363036620-85805073",
    #        }
    
    ##TODO: DELETE THIS!!! 
    #controller = {
    #        'id': 6,
    #        }
    #

    # Create Nova Cluster
    logger.info("Create Nova Cluster:")
    Adventure.create_nova_cluster(service_nodes_server, chef_server, url, \
            user, password, cidr)
    
    # Provision Nova Controller
    logger.info("Nova Controller:")
    node = unprovisioned_nodes.pop(0)
    controller = Adventure.provision_nova_node(\
            "Infrastructure", node, url, user, password)
    logger.info(controller['name'])

    # Run Upload Initial Glance Images on Controller
    logger.info("Uploading Initial Glance Images on Controller")
    Adventure.generic_adventure(controller, url, user, password, \
            "Upload Initial Glance Images", "openstack_upload_images")

    logger.info("Making Nova Changes on Controller:")
    controller_node = Utils.find_server(nova_client, controller['name'])
    Node.make_nova_changes(controller_node)
    
    # Provision Nova Compute
    logger.info("Nova Compute:")
    num_of_computes = len(unprovisioned_nodes)
    computes = []
    for i in range(0, num_of_computes):
        node = unprovisioned_nodes.pop(0)
        compute = Adventure.provision_nova_node(\
                "AZ nova", node, url, user, password)
        computes.append(compute)
        logger.info(compute['name'])
    
    logger.info("Waiting for remaining running tasks ...")
    Task.wait_for_remaining_tasks(url, user, password)
    
#-------------------------------------------------------------------------------
#USER = "admin"
#PASSWORD = "DKlq20bAVCyF"
#SERVER_IPV4 = "166.78.109.227"
#URL ="https://%s:8443" % SERVER_IPV4
#
#cidr = "192.168.3.0/24"
#class Foo():
#    name = "bac-opencenter-server-1363035526-75498007"
#oc_server = Foo()
#
#provision_cluster(oc_server, None, URL, USER, PASSWORD, 5, cidr)
#-------------------------------------------------------------------------------
