#-------------------------------------------------------------------------------
from utils import Utils
#-------------------------------------------------------------------------------
OPENCENTER_URL ="166.78.125.17:8080"
#-------------------------------------------------------------------------------
################################################################################
class Adventures:
#-------------------------------------------------------------------------------
    @classmethod
    def provision_chef(cls,node):
        None
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
        nodes = json_data['nodes']
        
        unprovisioned = None
        unprovisioned_nodes = []
        
        try:
            if status == 200:
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
# Get nodes info
nodes_json = Utils.get_json(OPENCENTER_URL, "/nodes/")
unprovisioned_nodes = Nodes.get_unprovisioned(nodes_json)
if unprovisioned_nodes:
    for i in unprovisioned_nodes:
        print i['name']

#adventures_json = Adventures.get_json(OPENCENTER_URL, "/adventures/")
#adventures = Adventures.get_adventures(adventures_json)

#chef = provision_chef(unprovisioned_nodes.pop(0))
#controller = provision_controller(unprovisioned_nodes.pop(0))
#compute1 = provision_compute(unprovisioned_nodes.pop(0))
#-------------------------------------------------------------------------------
