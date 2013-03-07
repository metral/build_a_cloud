#-------------------------------------------------------------------------------
from time import sleep
from utils import Utils
#-------------------------------------------------------------------------------
################################################################################
class Task:
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_task(cls, parent_id, node, action, url, user, password):
        tasked = False
        state = None
        node_name = node['name']
        task_id = None
        
        while not tasked:
            tasks_json = Utils.oc_api(url + "/tasks/", user, password)
            tasks = Utils.extract_oc_object_type(tasks_json, "tasks")
            for task in tasks:
                if (task['node_id'] == node['id']) and \
                    (task['action'] == action) and \
                    (task['parent_id'] == parent_id):
                    tasked = True
                    task_id = task['id']
                    state = task['state']
            print "Waiting for %s to be tasked on %s..." % (action, node_name)
            sleep(2)
        while(state != 'done' and task_id):
            print "Waiting for %s to adventurate on %s..." % (action, node_name)
            path = "/tasks/%s" % task_id
            updated_json = Utils.oc_api(url + path, user, password)
            updated_task = Utils.extract_oc_object_type(updated_json, "task")
            if updated_task:
                state = updated_task['state']
            sleep(5)
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
        # Get adventures
        adventures = cls.get_adventures(url, user, password)
        
        for adventure in adventures:
            if adventure['name'] == adventure_name:
                return adventure 
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def execute(cls, adventure, url, user, password, params = None):
        path = "/adventures/%s/execute" % adventure['id']
        full_url = url + path
        
        result = None
        if params:
            result = Utils.oc_api(full_url, user, password,
                    kwargs={'json': params})
        else:
            result = Utils.oc_api(full_url, user, password)

        if result:
            return result
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef_server(cls, node, url, user, password):
        
        # Execute 'install_chef_server' adventure
        adventure = cls.find("Install Chef Server", url, user, password)
        params = {
                "node": node['id'],
                }
        result = cls.execute(adventure, url, user, password, params)
        
        # result['id'] is adventurate parent id
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
            print Utils.logging(e)
            return None
            
        return node
#-------------------------------------------------------------------------------
    @classmethod
    def create_nova_cluster(cls, url, user, password):
        # Create Nova Cluster
        adventure = Adventure.find("Create Nova Cluster", url, user, password)
        result = Adventure.execute(adventure, url, user, password)
        
        # result['id'] is adventurate parent id
        parent_id = int(result['task']['id'])
        
        try:
            if result['status'] == 202:
                # Monitor tasking of create_nova_cluster
                action = "" #TODO
                Task.wait_for_task(parent_id, node, action, url, user, password)
        except Exception,e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef_clients(cls, nodes, num_of_clients, url, user, password):
        provisioned_chef_clients = []
        adventure = Adventure.find("Install Chef Client", url, user, password)
        
        for i in range(0, num_of_clients):
            node = nodes.pop(0)
            params = {
                    "node": node['id'],
                    }
            result = Adventure.execute(adventure, url, user, password, params)
        
            # result['id'] is adventurate parent id
            parent_id = int(result['task']['id'])

            try:
                if result['status'] == 202:
                    # Monitor tasking of install_chef
                    action = "install_chef"
                    Task.wait_for_task(parent_id, node, action, 
                            url, user, password)
                    provisioned_chef_clients.append(node)
            except Exception,e:
                print Utils.logging(e)
        
        return provisioned_chef_clients
#-------------------------------------------------------------------------------
    @classmethod
    def provision_controller(cls,node):
        None
#-------------------------------------------------------------------------------
    @classmethod
    def provision_compute(cls,node):
        None

################################################################################

class Node:
#-------------------------------------------------------------------------------
    @classmethod
    def get_unprovisioned(cls, json_data):
        if json_data is None:
            return None
        
        status = int(json_data['status'])
        
        try:
            if status == 200:
                nodes = json_data['nodes']
                unprovisioned = None
                unprovisioned_nodes = []
                for node in nodes:
                    if node['name'] == "unprovisioned":
                        unprovisioned = node
                if unprovisioned:
                    for node in nodes:
                        try:
                            parent_id = node['facts']['parent_id']
                            if parent_id == unprovisioned['id']:
                                unprovisioned_nodes.append(node)
                        except:
                            pass

                return unprovisioned_nodes
        except Exception,e:
            print Utils.logging(e)
            return None
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_agents(cls, total_agents, url, user, password):
        unprovisioned_nodes = []
        
        while len(unprovisioned_nodes) < total_agents:
            nodes_json = Utils.oc_api(url + "/nodes/", user, password)
            unprovisioned_nodes = cls.get_unprovisioned(nodes_json)
            if len(unprovisioned_nodes) < total_agents:
                print "Waiting for all unprovisioned nodes..."
                sleep(10)
        
        return unprovisioned_nodes
#-------------------------------------------------------------------------------

#USER = "admin"
#PASSWORD = ""
#SERVER_IPV4 = ""
#URL ="https://%s:8443" % SERVER_IPV4

def provision_cluster(url, user, password, num_of_oc_agents):
    # Wait for all unprovisioned OC agent nodes to be up & talking to OC server
    unprovisioned_nodes = Node.wait_for_agents(\
            num_of_oc_agents, url, user, password)

    # Provision OC agent as Chef Server
    node = unprovisioned_nodes.pop(0)
    chef_server = Adventure.provision_chef_server(node, url, user, password)
    print "*********** Chef-Server:"
    print chef_server['name']

    # Create Nova Cluster
    #Adventure.create_nova_cluster(URL, USER, PASSWORD)


# testing
#print "*********** Unprovisioned Nodes:"
#for i in unprovisioned_nodes:
#    print i['name']
#
#print "*********** Adventures:"
#adventures_json = Utils.oc_api(URL + "/adventures/", USER, PASSWORD)
#adventures = Utils.extract_oc_object_type(adventures_json, "adventures")
#for i in adventures:
#    print i['name']
#
#print "*********** Adventure:"
#adventure_json = Utils.oc_api(URL + "/adventures/2", USER, PASSWORD)
#adventure = Utils.extract_oc_object_type(adventure_json, "adventure")
#print adventure
#
#print "*********** Tasks:"
#tasks_json = Utils.oc_api(URL + "/tasks/", USER, PASSWORD)
#tasks = Utils.extract_oc_object_type(tasks_json, "tasks")
#for i in tasks:
#    print i['name']
#        
#print "*********** Task:"
#task_json = Utils.oc_api(URL + "/tasks/2", USER, PASSWORD)
#task = Utils.extract_oc_object_type(task_json, "task")
#print task

# Provision remaining unprovisioned OC agent nodes as Chef Clients
#num_of_clients = len(unprovisioned_nodes)
#chef_clients = Adventure.provision_chef_clients(unprovisioned_nodes,
#        num_of_clients, url, user, password)
#print "*********** Chef-Clients:"
#for i in chef_clients:
#    print i['name']
#-------------------------------------------------------------------------------
