#-------------------------------------------------------------------------------
from utils import Utils
import collections
import httplib
import json
#-------------------------------------------------------------------------------
class OC:
    OC_API="166.78.125.17:8080"
#-------------------------------------------------------------------------------
    @classmethod
    def convert_uni_to_str(cls, data):
        # convert unicode to string
        if isinstance(data, unicode):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict(map(cls.convert_uni_to_str, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(cls.convert_uni_to_str, data))
        else:
            return data
#-------------------------------------------------------------------------------
    @classmethod
    def nodes_conn(cls):
        url = cls.OC_API
        path = "/".join(["/nodes/"])

        conn = (url, path)
        return conn
#-------------------------------------------------------------------------------
    @classmethod
    def nodes_post(cls):
        url, path = cls.nodes_conn()
        post_params = {
                "volume": {
                    "size": 1,
                    "display_name": "foobar-volume-",
                    }
                }
        params = json.dumps(post_params)
        headers = {"Content-Type": "application/json"}

        conn = httplib.HTTPConnection(url)
        conn.request("POST", path, params, headers)
        res = conn.getresponse()

        try:
            json_data = json.loads(res.read())
        except:
            return res.read()

        return json_data
#-------------------------------------------------------------------------------
    @classmethod
    def get(cls, url, path):
        url, path = url, path
        headers = {"Content-Type": "application/json"}

        conn = httplib.HTTPConnection(url)
        conn.request("GET", path, "", headers)
        res = conn.getresponse()

        try:
            json_data = cls.convert_uni_to_str(json.loads(res.read()))
        except Exception,e:
            print str(e)
            return res.read()

        return json_data
#-------------------------------------------------------------------------------
    @classmethod
    def extract_unprovisioned(cls, nodes):
        unprovisioned = None
        unprovisioned_nodes = []
        for node in nodes:
            if node['name'] == "unprovisioned":
                unprovisioned = node
        if unprovisioned:
            for node in nodes:
                try:
                    if node['facts']['parent_id'] == unprovisioned['id']:
                        unprovisioned_nodes.append(node)
                except:
                    pass

        return unprovisioned_nodes
#-------------------------------------------------------------------------------
    @classmethod
    def process_nodes_data(cls, json_data):
        status = int(json_data['status'])
        nodes = json_data['nodes']

        try:
            if status == 200:
                unprovisioned_nodes = cls.extract_unprovisioned(nodes)
                chef = unprovisioned_nodes.pop()
        except Exception, e:
            print Utils.logging(e)
#-------------------------------------------------------------------------------
nodes_url, nodes_path = OC.nodes_conn()
nodes_json_data = OC.get(nodes_url, nodes_path)
OC.process_nodes_data(nodes_json_data)

#print OC.nodes_post()
