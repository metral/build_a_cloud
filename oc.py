#-------------------------------------------------------------------------------
from time import sleep
from utils import Utils
#-------------------------------------------------------------------------------
################################################################################
class Task:
#-------------------------------------------------------------------------------
    @classmethod
    def wait_for_task(cls, url, user, password, node, action):
        tasked = False
        state = None
        task_id = None
        while not tasked:
            tasks_json = Utils.oc_api(url + "/tasks/", user, password)
            tasks = Utils.extract_oc_object_type(tasks_json, "tasks")
            for task in tasks:
                if (task['node_id'] == node['id']) and (task['action'] == action):
                    tasked = True
                    task_id = task['id']
                    state = task['state']
            print "Waiting for %s to be tasked..." % action
            sleep(3)
        while(state != 'done'):
            print "Waiting for %s to adventurate..." % action
            path = "/tasks/%s" % task_id
            updated_json = Utils.oc_api(url + path, user, password)
            updated_task = Utils.extract_oc_object_type(updated_json, "task")
            if updated_task:
                state = updated_task['state']
            sleep(10)
################################################################################
class Adventures:
#-------------------------------------------------------------------------------
    @classmethod
    def get_adventures(cls, url, user, password):
        # Get adventures
        adventures_json = Utils.oc_api(url + "/adventures/", user, password)
        adventures = Utils.extract_oc_object_type(adventures_json, "adventures")
        return adventures
#-------------------------------------------------------------------------------
    @classmethod
    def find(cls, adventure_name, adventures):
        for adventure in adventures:
            if adventure['name'] == adventure_name:
                return adventure 
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def execute(cls, adventure, node, url, user, password):
        path = "/adventures/%s/execute" % adventure['id']
        params_json = {
                "node": node['id'],
                }
        result = Utils.oc_api(url + path, user, password, 
                kwargs={'json': params_json })

        if result:
            return result
        return None
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef(cls, node, url, user, password):
        # Get adventures
        adventures = cls.get_adventures(url, user, password)
        
        # Execute 'install_chef_server' adventure
        adventure = cls.find("Install Chef Server", adventures)
        result = cls.execute(adventure, node, url, user, password)
        
        try:
            if result['status'] == 202:
                # Monitor tasking of install_chef_server
                action = "install_chef_server"
                Task.wait_for_task(url, user, password, node, action)
                    
                # Monitor tasking of download_cookbooks
                action = "download_cookbooks"
                Task.wait_for_task(url, user, password, node, action)
        except Exception,e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
    @classmethod
    def provision_controller(cls,node):
        None
#-------------------------------------------------------------------------------
    @classmethod
    def provision_compute(cls,node):
        None

################################################################################

class Nodes:
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
            unprovisioned_nodes = Nodes.get_unprovisioned(nodes_json)
            if len(unprovisioned_nodes) < total_agents:
                print "Waiting for all unprovisioned nodes..."
                sleep(10)
        
        return unprovisioned_nodes
#-------------------------------------------------------------------------------

USER = "admin"
PASSWORD = "fW2T5XJezsE3"
SERVER_IPV4 = "166.78.124.234"
URL ="https://%s:8443" % SERVER_IPV4

unprovisioned_nodes = Nodes.wait_for_agents(10, URL, USER, PASSWORD)

Adventures.provision_chef(unprovisioned_nodes.pop(0), URL, USER, PASSWORD)

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
#-------------------------------------------------------------------------------
